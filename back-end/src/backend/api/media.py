from typing import Any, List, Dict, Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlmodel import Session, select
import httpx
import re

from backend.api import deps
from backend.services.tmdb import tmdb_client
from backend.services.emby import emby_client
from backend.models import User, SubscriptionRequest
from backend.db import get_session
from backend.settings import get_settings

settings = get_settings()
router = APIRouter()

def extract_media_info(emby_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    media_streams = emby_item.get("MediaStreams", [])
    if not media_streams:
        return None

    video_stream = next((stream for stream in media_streams if stream.get("Type") == "Video"), None)
    if not video_stream:
        return None

    audio_streams = [
        {
            "title": stream.get("DisplayTitle"),
            "codec": stream.get("Codec"),
            "channels": stream.get("Channels"),
            "bitrate": stream.get("BitRate"),
            "sample_rate": stream.get("SampleRate"),
            "language": stream.get("Language"),
        }
        for stream in media_streams
        if stream.get("Type") == "Audio"
    ]

    subtitle_streams = [
        {
            "title": stream.get("DisplayTitle"),
            "language": stream.get("Language"),
            "codec": stream.get("Codec"),
        }
        for stream in media_streams
        if stream.get("Type") == "Subtitle"
    ]

    video_info = {
        "title": video_stream.get("DisplayTitle") or emby_item.get("Name"),
        "codec": video_stream.get("Codec"),
        "profile": video_stream.get("Profile"),
        "level": video_stream.get("Level"),
        "width": video_stream.get("Width"),
        "height": video_stream.get("Height"),
        "aspect_ratio": video_stream.get("AspectRatio"),
        "is_interlaced": video_stream.get("IsInterlaced"),
        "frame_rate": video_stream.get("AverageFrameRate"),
        "bitrate": video_stream.get("BitRate") or emby_item.get("Bitrate"),
        "video_range": video_stream.get("VideoRangeType") or video_stream.get("VideoRange"),
        "bit_depth": video_stream.get("BitDepth"),
        "pixel_format": video_stream.get("PixelFormat"),
        "ref_frames": video_stream.get("RefFrames"),
        "hdr": video_stream.get("IsHdr"),
        "color_space": video_stream.get("ColorSpace"),
    }

    return {
        "video": video_info,
        "audio": audio_streams,
        "subtitles": subtitle_streams,
        "container": emby_item.get("Container"),
        "path": emby_item.get("Path"),
        "size": emby_item.get("Size"),
    }

async def enrich_media_status(media_list: List[Dict[str, Any]], session: Session):
    """
    Check Emby and Local DB for status.
    """
    for media in media_list:
        tmdb_id = str(media.get("id"))
        
        # 1. Check Emby
        emby_items = await emby_client.search_by_provider_id("Tmdb", tmdb_id)
        if emby_items:
            media["status"] = "AVAILABLE"
            media["emby_id"] = emby_items[0].get("Id")
            continue

        # 2. Check SubscriptionRequest
        statement = select(SubscriptionRequest).where(
            SubscriptionRequest.tmdb_id == tmdb_id
        )
        request = session.exec(statement).first()
        
        if request:
            media["status"] = request.status.value.upper()
            media["request_user_id"] = request.user_id
        else:
            media["status"] = "UNKNOWN" # Not in Emby, not requested

@router.get("/trending")
async def get_trending(
    page: int = 1,
    media_type: str = Query("all", pattern="^(all|movie|tv)$"),
    time_window: str = Query("day", pattern="^(day|week)$"),
    without_genres: Optional[str] = Query(None),
    current_user: User = Depends(deps.get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    try:
        if media_type == "tv" and without_genres:
            # Use discover endpoint for TV with filtering
            data = await tmdb_client.discover_tv(page=page, without_genres=without_genres)
        else:
            data = await tmdb_client.get_trending(media_type=media_type, time_window=time_window, page=page)
    except Exception as e:
        print(f"TMDB Get Trending Error: {e}")
        # Return empty results instead of 500 to avoid breaking UI completely
        return {"results": []}

    results = data.get("results", [])

    # Trending endpoint doesn't always include media_type when we request a single type,
    # so ensure the downstream UI can distinguish movies vs TV shows.
    if media_type in ("movie", "tv"):
        for item in results:
            item["media_type"] = media_type
    
    await enrich_media_status(results, session)
    
    return {"results": results}

@router.get("/latest")
async def get_latest(
    limit: int = 20, # Increased default limit to 20 as requested
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Get recently added items from Emby, then fetch their details from TMDB for better metadata.
    """
    try:
        emby_items = await emby_client.get_latest_items(limit=limit)
    except Exception as e:
        print(f"Emby Get Latest Error: {e}")
        return {"results": []}
    
    results = []
    for item in emby_items:
        # Extract TMDB ID from ProviderIds
        provider_ids = item.get("ProviderIds", {})
        print(f"DEBUG: Item {item.get('Name')} ProviderIds: {provider_ids}") # DEBUG LOG
        tmdb_id = provider_ids.get("Tmdb") or provider_ids.get("tmdb") or provider_ids.get("TMDB")
        
        # Try to find via IMDb if TMDB ID is missing
        if not tmdb_id:
            imdb_id = provider_ids.get("Imdb") or provider_ids.get("imdb") or provider_ids.get("IMDB")
            if imdb_id:
                try:
                    print(f"DEBUG: Looking up TMDB ID for {item.get('Name')} via IMDb: {imdb_id}")
                    find_res = await tmdb_client.find_by_external_id(imdb_id, "imdb_id")
                    # Check movie_results or tv_results
                    found_items = find_res.get("movie_results", []) + find_res.get("tv_results", [])
                    if found_items:
                        tmdb_id = str(found_items[0].get("id"))
                        print(f"DEBUG: Found TMDB ID via IMDb: {tmdb_id}")
                except Exception as e:
                    print(f"DEBUG: Failed lookup via IMDb: {e}")
        
        # Fallback: Search by name and year if still no ID
        if not tmdb_id:
            try:
                name = item.get("Name")
                year = None
                if item.get("ProductionYear"):
                    year = item.get("ProductionYear")
                elif item.get("PremiereDate"):
                    year = item.get("PremiereDate")[:4]
                
                print(f"DEBUG: Searching TMDB by name for {name} ({year})")
                search_res = await tmdb_client.search(query=name, page=1)
                search_results = search_res.get("results", [])
                
                # Filter by year if available to be more precise
                candidate = None
                if search_results:
                    if year:
                        for res in search_results:
                            res_year = res.get("release_date", "")[:4] or res.get("first_air_date", "")[:4]
                            if res_year == str(year):
                                candidate = res
                                break
                    
                    # If no exact year match or no year provided, take the first result
                    if not candidate and search_results:
                        candidate = search_results[0]
                
                if candidate:
                    tmdb_id = str(candidate.get("id"))
                    print(f"DEBUG: Found TMDB ID via Search: {tmdb_id} for {name}")
            except Exception as e:
                 print(f"DEBUG: Failed lookup via Search: {e}")

        if tmdb_id:
            media_type = "movie" if item.get("Type") == "Movie" else "tv"
            try:
                # Fetch details from TMDB
                tmdb_data = await tmdb_client.get_details(media_type, tmdb_id)
                
                # Use TMDB data but mark as AVAILABLE (since it's from Emby)
                tmdb_data["status"] = "AVAILABLE"
                tmdb_data["media_type"] = media_type
                # Ensure ID matches TMDB ID format (int in TMDB response, but we use str often)
                tmdb_data["id"] = tmdb_data.get("id") 
                
                # Add Emby ID just in case we need to link back (though we prefer TMDB metadata now)
                tmdb_data["emby_id"] = item.get("Id")
                
                results.append(tmdb_data)
            except Exception as e:
                print(f"Failed to fetch TMDB details for {item.get('Name')}: {e}")
                # Skip this item if TMDB fetch fails, do not fallback to Emby ID to avoid frontend errors
                continue
        else:
            # No TMDB ID found, skip this item
            print(f"DEBUG: Skipping {item.get('Name')} (ID: {item.get('Id')}) - No TMDB ID found in ProviderIds: {provider_ids} or via search")
            continue
        
    return {"results": results}

@router.get("/emby-image/{item_id}")
async def get_emby_image(item_id: str):
    """
    Proxy Emby images to avoid CORS and mixed content issues.
    """
    url = f"{settings.EMBY_SERVER_URL}/Items/{item_id}/Images/Primary"
    async with httpx.AsyncClient() as client:
        # Forward request to Emby
        resp = await client.get(url, params={"maxWidth": 400})
        return Response(content=resp.content, media_type=resp.headers.get("content-type", "image/jpeg"))

@router.get("/tmdb-image/{size}/{image_path:path}")
async def get_tmdb_image(size: str, image_path: str):
    """
    Proxy TMDB images to avoid blocking issues in some regions.
    """
    url = f"https://image.tmdb.org/t/p/{size}/{image_path}"
    async with httpx.AsyncClient() as client:
        # Forward request to TMDB
        # We might want to add some caching headers here if not present
        try:
            resp = await client.get(url)
            # Pass along content type
            return Response(content=resp.content, media_type=resp.headers.get("content-type", "image/jpeg"))
        except Exception as e:
            print(f"Failed to proxy TMDB image: {e}")
            return Response(status_code=404)

@router.get("/search")
async def search_media(
    query: str,
    page: int = 1,
    current_user: User = Depends(deps.get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    data = await tmdb_client.search(query, page)
    results = data.get("results", [])
    
    # Filter out people
    results = [r for r in results if r.get("media_type") in ["movie", "tv"]]
    
    await enrich_media_status(results, session)
    
    return {"results": results, "total_pages": data.get("total_pages")}

@router.get("/anime")
async def get_anime(
    page: int = 1,
    current_user: User = Depends(deps.get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    data = await tmdb_client.get_anime(page)
    results = data.get("results", [])
    
    await enrich_media_status(results, session)
    
    return {"results": results}

@router.get("/person/{person_id}")
async def get_person_details(
    person_id: str,
    current_user: User = Depends(deps.get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """
    Get person details from TMDB including combined credits.
    """
    data = await tmdb_client.get_person_details(person_id)
    
    # Enrich credits with status
    if "combined_credits" in data:
        cast = data["combined_credits"].get("cast", [])
        crew = data["combined_credits"].get("crew", [])
        
        # Filter duplicates or just process all
        # We need to make sure media_type is set correctly for enrichment
        # TMDB usually provides media_type in combined_credits
        
        # Combine relevant items for enrichment
        items_to_enrich = []
        seen_ids = set()
        
        for item in cast + crew:
            # Only interested in movie/tv
            if item.get("media_type") in ["movie", "tv"]:
                if item["id"] not in seen_ids:
                    items_to_enrich.append(item)
                    seen_ids.add(item["id"])
        
        await enrich_media_status(items_to_enrich, session)
        
    return data


@router.get("/tv/{tmdb_id}/season/{season_number}")
async def get_season_details(
    tmdb_id: str,
    season_number: int,
    current_user: User = Depends(deps.get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """
    Get details for a specific season of a TV show.
    """
    data = await tmdb_client.get_season_details(tmdb_id, season_number)
    
    # Enrich with Emby status
    try:
        emby_lookup = await emby_client.search_by_provider_id("Tmdb", tmdb_id)
        if emby_lookup:
            series_id = emby_lookup[0].get("Id")
            emby_episodes = await emby_client.get_episodes(series_id, season_number)
            
            # Create a set of existing episode numbers
            existing_episodes = set()
            for ep in emby_episodes:
                # Emby IndexNumber is the episode number
                idx = ep.get("IndexNumber")
                if idx is not None:
                    existing_episodes.add(idx)
            
            # Mark episodes
            if "episodes" in data:
                for ep in data["episodes"]:
                    if ep.get("episode_number") in existing_episodes:
                        ep["is_in_library"] = True
                    else:
                        ep["is_in_library"] = False
    except Exception as e:
        print(f"Failed to enrich season details with Emby data: {e}")
        
    return data


@router.get("/{media_type}/{tmdb_id}")
async def get_details(
    media_type: str,
    tmdb_id: str,
    current_user: User = Depends(deps.get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """
    Get media details from TMDB and enrich with credits.
    """
    # Allow 'tv' alias for 'series'
    if media_type == "series":
        media_type = "tv"
        
    data = await tmdb_client.get_details(media_type, tmdb_id)
    
    # Enrich with credits (cast/crew) - tmdb_client.get_details already does 'append_to_response' but we might need more
    # Actually my current get_details implementation only does external_ids. Let's update it to include credits.
    
    # Mock status enrichment (single item list)
    wrapper = [data]
    # Ensure ID is string for comparison
    data["id"] = str(data["id"])
    data["media_type"] = media_type
    
    await enrich_media_status(wrapper, session)

    if data.get("status") == "AVAILABLE" and not data.get("emby_id"):
        try:
            emby_lookup = await emby_client.search_by_provider_id("Tmdb", tmdb_id)
            if emby_lookup:
                data["emby_id"] = emby_lookup[0].get("Id")
        except Exception as exc:
            print(f"Failed to lookup Emby item for {tmdb_id}: {exc}")

    if data.get("emby_id"):
        try:
            emby_details = await emby_client.get_item_details(data["emby_id"])
            media_info = extract_media_info(emby_details)
            if media_info:
                data["media_info"] = media_info
        except Exception as exc:
            # Log and continue without failing the entire response
            print(f"Failed to fetch Emby media info for {tmdb_id}: {exc}")
    
    if media_type == "tv" and data.get("emby_id"):
        try:
            # If TV show is available, fetch all episodes to determine status of each season
            emby_episodes = await emby_client.get_episodes(data["emby_id"])
            
            # Group episodes by ParentIndexNumber (Season Number)
            episodes_by_season = {}
            for ep in emby_episodes:
                season_num = ep.get("ParentIndexNumber")
                if season_num is not None:
                    episodes_by_season[season_num] = episodes_by_season.get(season_num, 0) + 1
            
            # Add existing_episode_count to seasons data
            if "seasons" in data:
                for season in data["seasons"]:
                    s_num = season.get("season_number")
                    season["existing_episode_count"] = episodes_by_season.get(s_num, 0)
                    
        except Exception as e:
            print(f"Failed to fetch Emby episodes for TV show {tmdb_id}: {e}")

    # Check if subscribed (for heart icon)
    if media_type == "tv":
        # Fetch subscription requests for this show to determine season status
        requests = session.exec(
            select(SubscriptionRequest).where(SubscriptionRequest.tmdb_id == tmdb_id)
        ).all()
        
        season_requests = {r.specific_season: r.status for r in requests if r.specific_season is not None}
        # Check for whole-show request
        whole_show_request = next((r for r in requests if r.specific_season is None), None)
        
        if "seasons" in data:
            for season in data["seasons"]:
                s_num = season.get("season_number")
                # Check specific season status
                status = season_requests.get(s_num)
                # If not specifically requested, check if whole show is requested
                if not status and whole_show_request:
                     status = whole_show_request.status
                
                if status:
                    season["subscription_status"] = status.value.upper()

    return data
