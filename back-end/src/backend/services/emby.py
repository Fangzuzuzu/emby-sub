import httpx
from typing import Optional, Dict, Any, List
from backend.settings import get_settings
from backend.models import UserRole

settings = get_settings()

class EmbyClient:
    def __init__(self):
        self.base_url = settings.EMBY_SERVER_URL
        self.api_key = settings.EMBY_API_KEY
        self.headers = {
            "X-Emby-Token": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        # Local connections to Emby should not use proxy
        # httpx respects NO_PROXY environment variable, but we can also force trust_env=False
        # if we want to ignore ALL proxy settings for Emby client. 
        # Given Emby is usually local/internal, this is safer than relying on correct NO_PROXY config.
        
    def _get_client(self) -> httpx.AsyncClient:
        """
        Return an AsyncClient that ignores proxy settings (trust_env=False).
        """
        return httpx.AsyncClient(trust_env=False)

    async def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user with Emby Server.
        """
        url = f"{self.base_url}/Users/AuthenticateByName"
        # Emby requires client info headers for authentication usually, but minimal works too
        auth_headers = {
             "Content-Type": "application/json",
             "X-Emby-Client": "EmbySubscriptionManager",
             "X-Emby-Device-Name": "Web",
             "X-Emby-Device-Id": "emby-sub-manager-001",
             "X-Emby-Client-Version": "1.0.0",
        }
        
        async with self._get_client() as client:
            response = await client.post(
                url, 
                json={"Username": username, "Pw": password},
                headers=auth_headers
            )
            response.raise_for_status()
            return response.json()

    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """
        Get user details including policy (admin status).
        """
        url = f"{self.base_url}/Users/{user_id}"
        async with self._get_client() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def get_latest_items(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recently added items.
        """
        url = f"{self.base_url}/Items"
        params = {
            "SortBy": "DateCreated",
            "SortOrder": "Descending",
            "IncludeItemTypes": "Movie,Series",
            "Recursive": "true",
            "Limit": limit,
            "Fields": "ProviderIds,Overview,DateCreated,CommunityRating",
        }
        async with self._get_client() as client:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json().get("Items", [])

    async def search_by_provider_id(self, provider: str, provider_id: str) -> List[Dict[str, Any]]:
        """
        Check if an item exists in Emby by Provider ID (Tmdb, Imdb).
        provider: 'Tmdb' or 'Imdb'
        """
        url = f"{self.base_url}/Items"
        params = {
            "Recursive": "true",
            "AnyProviderIdEquals": f"{provider}.{provider_id}",
            "Fields": "ProviderIds",
        }
        async with self._get_client() as client:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json().get("Items", [])

    async def get_item_details(self, item_id: str) -> Dict[str, Any]:
        """
        Fetch detailed metadata for a specific Emby item, including media streams.
        """
        if settings.EMBY_USER_ID:
            url = f"{self.base_url}/Users/{settings.EMBY_USER_ID}/Items/{item_id}"
        else:
            url = f"{self.base_url}/Items/{item_id}"
        params = {
            "Fields": "MediaStreams,Path,Size,Bitrate,Width,Height,Container,Overview",
        }
        async with self._get_client() as client:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()

    async def get_episodes(self, series_id: str, season_number: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get episodes for a specific series. If season_number is provided, filter by it.
        """
        if settings.EMBY_USER_ID:
            url = f"{self.base_url}/Users/{settings.EMBY_USER_ID}/Items"
        else:
            url = f"{self.base_url}/Items"
            
        params = {
            "ParentId": series_id,
            "IncludeItemTypes": "Episode",
            "Recursive": "true",
            "Fields": "ProviderIds,IndexNumber,ParentIndexNumber",
        }
        if season_number is not None:
            params["ParentIndexNumber"] = season_number
            
        async with self._get_client() as client:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json().get("Items", [])

emby_client = EmbyClient()
