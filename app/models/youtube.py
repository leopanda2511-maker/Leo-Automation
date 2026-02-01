from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class YouTubeToken(BaseModel):
    user_id: str
    channel_id: str
    channel_name: str
    access_token: str
    refresh_token: str
    token_expiry: datetime
    created_at: datetime


class YouTubeChannel(BaseModel):
    id: str
    title: str
    subscriber_count: Optional[int] = None
    description: Optional[str] = None
    thumbnail: Optional[str] = None
