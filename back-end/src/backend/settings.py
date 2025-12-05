from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "Emby Subscription Manager"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "YOUR_SECRET_KEY_CHANGE_ME"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Emby Configuration
    EMBY_SERVER_URL: str = "http://localhost:8096"
    EMBY_API_KEY: str = ""
    EMBY_USER_ID: str | None = None

    # TMDB Configuration
    TMDB_API_KEY: str = ""
    TMDB_BASE_URL: str = "https://api.themoviedb.org/3"
    TMDB_IMAGE_BASE_URL: str = "https://image.tmdb.org/t/p/original"

    # Database
    DATABASE_URL: str = "sqlite:///./app.db"

    # Proxy
    HTTP_PROXY: str | None = None
    HTTPS_PROXY: str | None = None

    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_settings():
    return Settings()

