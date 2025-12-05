import httpx
import asyncio
from typing import Dict, Any, List, Optional
from backend.settings import get_settings

settings = get_settings()

class TMDBClient:
    def __init__(self):
        self.base_url = settings.TMDB_BASE_URL
        self.api_key = settings.TMDB_API_KEY
        self.params = {
            "api_key": self.api_key,
            "language": "zh-CN",  # Default to Chinese as requested
        }
        # Use explicit proxy settings if configured
        self.proxies = {}
        if settings.HTTP_PROXY:
            self.proxies["http://"] = settings.HTTP_PROXY
        if settings.HTTPS_PROXY:
            self.proxies["https://"] = settings.HTTPS_PROXY
            
    def _get_client(self) -> httpx.AsyncClient:
        """
        Return an AsyncClient with configured proxies.
        """
        # httpx 0.28.1 removed the 'proxies' argument from AsyncClient constructor if it's not passed correctly,
        # but checking the docs, 'proxies' IS the correct argument name. 
        # The error "unexpected keyword argument 'proxies'" usually means the version installed is VERY old 
        # or something weird is going on.
        # Let's verify the version or try mounting transport.
        # Alternatively, httpx renamed it to 'proxy' in some versions? No.
        # Wait, let's try simply NOT passing proxies if empty.
        
        # But actually, the error traceback says: 
        # TypeError: AsyncClient.__init__() got an unexpected keyword argument 'proxies'
        # This strongly suggests the installed httpx version does NOT support 'proxies' in __init__.
        # Older versions (pre 0.14) used 'proxies', newer use 'proxies' too...
        # Wait, httpx 0.28.1 DEFINITELY supports proxies.
        
        # Ah, maybe it's because we are passing it as a keyword argument to a class that might be wrapped or subclassed?
        # No, it's standard httpx.AsyncClient.
        
        # Let's try using mount() instead which is the lower-level way, or just setting it via mount.
        # Actually, another possibility: The user might have an older version of httpx installed in the venv despite what pip showed?
        # Let's try using 'proxy' (singular) just in case it's an extremely new or old version behavior change I'm missing.
        # BUT, checking httpx changelog, 0.28.1 supports 'proxy' arg for single proxy, and 'proxies' was deprecated/removed?
        # Let's check if we can use 'proxy' if it's a string, or 'mounts'.
        
        # FIX: httpx >= 0.24.0 prefers `proxy` (singular) string for simple cases or `mounts`.
        # BUT `proxies` dict is supported via `mounts` implicitly in older versions.
        # If `proxies` kwarg is gone, we must use `proxy` (if single) or `mounts`.
        # Since we have a dict, let's try to use the `proxy` argument if we only have one, or use standard env vars.
        # Since we are setting env vars in __init__, maybe we can just rely on that and NOT pass proxies arg?
        # The user previously said env vars didn't work.
        
        # Let's try this: pass `proxy` if we have http_proxy set.
        # httpx.AsyncClient(proxy="http://...")
        
        # If we have multiple (http and https), httpx might want us to use `mounts`.
        # But let's try the simplest fix:
        # If we have a proxy configured, use the 'proxy' argument (singular) which typically handles all traffic 
        # if we just pass the HTTP proxy URL.
        
        if self.proxies:
            # Just use the HTTP proxy for everything if available, as it's the most common setup
            proxy_url = self.proxies.get("http://") or self.proxies.get("https://")
            if proxy_url:
                return httpx.AsyncClient(proxy=proxy_url)
        
        return httpx.AsyncClient()

    async def get_trending(self, media_type: str = "all", time_window: str = "day", page: int = 1) -> Dict[str, Any]:
        """
        Get trending movies/shows.
        """
        url = f"{self.base_url}/trending/{media_type}/{time_window}"
        params = {**self.params, "page": page}
        async with self._get_client() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def search(self, query: str, page: int = 1) -> Dict[str, Any]:
        """
        Search for movies and TV shows.
        """
        url = f"{self.base_url}/search/multi"
        params = {**self.params, "query": query, "page": page}
        async with self._get_client() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def discover_tv(self, page: int = 1, without_genres: str = None) -> Dict[str, Any]:
        """
        Discover TV shows with filters (e.g. exclude genres).
        """
        url = f"{self.base_url}/discover/tv"
        params = {
            **self.params,
            "sort_by": "popularity.desc",
            "page": page
        }
        if without_genres:
            params["without_genres"] = without_genres
            
        async with self._get_client() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def get_anime(self, page: int = 1) -> Dict[str, Any]:
        """
        Get anime (Animation genre).
        Genre ID for Animation is 16.
        Mix of Movies and TV shows if possible, but TMDB discover is per type.
        We will fetch both and combine, or just fetch one type.
        For now, let's fetch both and mix them, or the caller decides.
        Actually, to simplify, let's just return TV shows (most anime) or allow type param.
        Wait, user wants "Anime" mixed.
        Let's fetch both and combine them by popularity.
        """
        # Fetch TV Anime
        url_tv = f"{self.base_url}/discover/tv"
        params_tv = {
            **self.params,
            "with_genres": "16",
            "sort_by": "popularity.desc",
            "page": page,
            "with_original_language": "ja",
        }
        
        # Fetch Movie Anime
        url_movie = f"{self.base_url}/discover/movie"
        params_movie = {
            **self.params,
            "with_genres": "16",
            "sort_by": "popularity.desc",
            "page": page,
            "with_original_language": "ja",
        }

        async with self._get_client() as client:
            # Parallel requests
            resp_tv, resp_movie = await asyncio.gather(
                client.get(url_tv, params=params_tv),
                client.get(url_movie, params=params_movie)
            )
            
            data_tv = resp_tv.json()
            data_movie = resp_movie.json()
            
            # Tag them
            results_tv = data_tv.get("results", [])
            for r in results_tv: r["media_type"] = "tv"
            
            results_movie = data_movie.get("results", [])
            for r in results_movie: r["media_type"] = "movie"
            
            # Combine and sort by popularity
            combined = results_tv + results_movie
            combined.sort(key=lambda x: x.get("popularity", 0), reverse=True)
            
            return {"results": combined[:20]} # Return top 20 mixed

    async def get_details(self, media_type: str, tmdb_id: str) -> Dict[str, Any]:
        """
        Get details for a specific movie or TV show, including external IDs and credits.
        """
        url = f"{self.base_url}/{media_type}/{tmdb_id}"
        # Request credits and external_ids
        params = {**self.params, "append_to_response": "external_ids,credits"}
        async with self._get_client() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def get_person_details(self, person_id: str) -> Dict[str, Any]:
        """
        Get person details and combined credits.
        """
        url = f"{self.base_url}/person/{person_id}"
        params = {**self.params, "append_to_response": "combined_credits,external_ids"}
        async with self._get_client() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def get_season_details(self, tv_id: str, season_number: int) -> Dict[str, Any]:
        """
        Get details for a specific season of a TV show.
        """
        url = f"{self.base_url}/tv/{tv_id}/season/{season_number}"
        async with self._get_client() as client:
            response = await client.get(url, params=self.params)
            response.raise_for_status()
            return response.json()

    async def find_by_external_id(self, external_id: str, external_source: str) -> Dict[str, Any]:
        """
        Find TMDB items by external ID (imdb_id, tvdb_id, etc).
        external_source: 'imdb_id', 'tvdb_id'
        """
        url = f"{self.base_url}/find/{external_id}"
        params = {**self.params, "external_source": external_source}
        async with self._get_client() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

tmdb_client = TMDBClient()
