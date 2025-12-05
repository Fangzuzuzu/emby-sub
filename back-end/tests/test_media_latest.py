import asyncio
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from backend.api import media
from backend.models import User


def test_get_latest_returns_tmdb_ids(monkeypatch):
    sample_emby_item = {
        "Name": "Sample Movie",
        "Id": "emby-123",
        "Type": "Movie",
        "ProviderIds": {"Tmdb": "321"},
    }

    async def fake_get_latest_items(limit: int):
        assert limit == 1
        return [sample_emby_item]

    async def fake_get_details(media_type: str, tmdb_id: str):
        assert media_type == "movie"
        assert tmdb_id == "321"
        return {
            "id": int(tmdb_id),
            "title": "Sample Movie",
            "poster_path": "/poster.jpg",
        }

    monkeypatch.setattr(media.emby_client, "get_latest_items", fake_get_latest_items)
    monkeypatch.setattr(media.tmdb_client, "get_details", fake_get_details)

    user = User(id="test-user", name="Tester")

    response = asyncio.run(media.get_latest(limit=1, current_user=user))
    assert len(response["results"]) == 1
    assert response["results"][0]["id"] == 321
    assert response["results"][0]["status"] == "AVAILABLE"

