from typing import Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from backend.api import deps
from backend.db import get_session
from backend.models import User, SubscriptionRequest, SubscriptionStatus, UserRole
from backend.services.tmdb import tmdb_client
from backend.services.approval import approval_service

router = APIRouter()

@router.post("/", response_model=SubscriptionRequest)
async def create_request(
    request_in: SubscriptionRequest,
    current_user: User = Depends(deps.get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """
    Create a new subscription request.
    """
    # Check if already exists
    query = select(SubscriptionRequest).where(SubscriptionRequest.tmdb_id == request_in.tmdb_id)
    if request_in.specific_season is not None:
        query = query.where(SubscriptionRequest.specific_season == request_in.specific_season)
    else:
        # If requesting entire show, check if there is a request for entire show (specific_season is None)
        query = query.where(SubscriptionRequest.specific_season == None)
        
    existing = session.exec(query).first()
    
    if existing:
        if (
            existing.status == SubscriptionStatus.REJECTED
            and existing.user_id == current_user.id
        ):
            existing.status = SubscriptionStatus.PENDING
            existing.request_date = datetime.utcnow()
            existing.comment = request_in.comment
            existing.media_type = request_in.media_type
            existing.title = request_in.title
            existing.poster_path = request_in.poster_path
            existing.overview = request_in.overview
            existing.release_date = request_in.release_date
            existing.specific_season = request_in.specific_season
            session.add(existing)
            session.commit()
            session.refresh(existing)
            return existing
        raise HTTPException(status_code=400, detail="Request for this media already exists")

    # Enrich with details from TMDB if missing (optional, but good for consistency)
    # Here we assume frontend sends correct basic info.
    
    request_in.user_id = current_user.id
    request_in.status = SubscriptionStatus.PENDING
    
    # Fetch external IDs (IMDB/TVDB) for automation
    try:
        # Handle 'tv' vs 'series' vs 'movie'
        lookup_type = request_in.media_type
        if lookup_type == "series":
            lookup_type = "tv"
            
        details = await tmdb_client.get_details(lookup_type, request_in.tmdb_id)
        external_ids = details.get("external_ids", {})
        request_in.imdb_id = external_ids.get("imdb_id")
        request_in.tvdb_id = str(external_ids.get("tvdb_id")) if external_ids.get("tvdb_id") else None
    except Exception:
        pass # Ignore if TMDB fails, we can retry later or proceed without

    session.add(request_in)
    session.commit()
    session.refresh(request_in)
    return request_in

class RequestWithUser(SubscriptionRequest):
    user_name: Optional[str] = None

@router.get("/", response_model=List[RequestWithUser])
def read_requests(
    skip: int = 0,
    limit: int = 100,
    status: Optional[SubscriptionStatus] = None,
    own: bool = False,
    current_user: User = Depends(deps.get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """
    Retrieve requests.
    """
    query = select(SubscriptionRequest, User.name).join(User, SubscriptionRequest.user_id == User.id)
    
    if current_user.role != UserRole.ADMIN or own:
        query = query.where(SubscriptionRequest.user_id == current_user.id)
        
    if status:
        query = query.where(SubscriptionRequest.status == status)
        
    query = query.offset(skip).limit(limit).order_by(SubscriptionRequest.request_date.desc())
    
    results = session.exec(query).all()
    
    final_results = []
    for req, user_name in results:
        req_dict = req.model_dump()
        req_dict["user_name"] = user_name
        final_results.append(req_dict)
        
    return final_results

@router.put("/{request_id}/approve", response_model=SubscriptionRequest)
def approve_request(
    request_id: int,
    current_user: User = Depends(deps.get_current_active_admin),
    session: Session = Depends(get_session)
) -> Any:
    request = session.get(SubscriptionRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
        
    request.status = SubscriptionStatus.APPROVED
    session.add(request)
    session.commit()
    session.refresh(request)
    
    approval_service.notify_downloader(request)
    
    return request

@router.put("/{request_id}/reject", response_model=SubscriptionRequest)
def reject_request(
    request_id: int,
    current_user: User = Depends(deps.get_current_active_admin),
    session: Session = Depends(get_session)
) -> Any:
    request = session.get(SubscriptionRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
        
    request.status = SubscriptionStatus.REJECTED
    session.add(request)
    session.commit()
    session.refresh(request)
    return request

@router.delete("/{tmdb_id}")
def cancel_request(
    tmdb_id: str,
    season_number: Optional[int] = Query(None),
    current_user: User = Depends(deps.get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """
    Allow users (or admins) to cancel their own pending requests.
    """
    statement = select(SubscriptionRequest).where(SubscriptionRequest.tmdb_id == tmdb_id)
    if current_user.role != UserRole.ADMIN:
        statement = statement.where(SubscriptionRequest.user_id == current_user.id)

    if season_number is not None:
        statement = statement.where(SubscriptionRequest.specific_season == season_number)
    else:
        statement = statement.where(SubscriptionRequest.specific_season == None)

    request = session.exec(statement).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    if request.status != SubscriptionStatus.PENDING:
        raise HTTPException(status_code=400, detail="Only pending requests can be cancelled")

    response_payload = request.model_dump()
    session.delete(request)
    session.commit()
    return response_payload

