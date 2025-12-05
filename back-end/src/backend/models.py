from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

class SubscriptionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"

class MediaType(str, Enum):
    MOVIE = "movie"
    SERIES = "series"
    TV = "tv" # Added alias for compatibility

class User(SQLModel, table=True):
    id: str = Field(primary_key=True) # Emby User ID
    name: str
    role: UserRole = Field(default=UserRole.USER)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: datetime = Field(default_factory=datetime.utcnow)

class SubscriptionRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    tmdb_id: str
    media_type: str = Field(description="movie, series, or tv")
    title: str
    poster_path: Optional[str] = None
    overview: Optional[str] = None
    release_date: Optional[str] = None
    status: SubscriptionStatus = Field(default=SubscriptionStatus.PENDING)
    request_date: datetime = Field(default_factory=datetime.utcnow)
    comment: Optional[str] = None
    specific_season: Optional[int] = Field(default=None, description="Specific season number to subscribe to")
    
    # For automated checking
    imdb_id: Optional[str] = None
    tvdb_id: Optional[str] = None

class Notification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    title: str
    message: str
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    related_subscription_id: Optional[int] = Field(default=None, foreign_key="subscriptionrequest.id")

