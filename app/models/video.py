from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime


class VideoSchedule(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=5000)
    video_drive_url: str = Field(..., min_length=1)
    thumbnail_drive_url: Optional[str] = None
    publish_datetime: str = Field(..., description="ISO format datetime: YYYY-MM-DDTHH:MM:SS")
    tags: List[str] = Field(default_factory=list, max_length=500)
    category_id: str = Field(default="22", description="YouTube category ID")
    made_for_kids: bool = Field(default=False)
    
    @field_validator('publish_datetime')
    @classmethod
    def validate_datetime(cls, v: str) -> str:
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError("Invalid datetime format. Use ISO format: YYYY-MM-DDTHH:MM:SS")
        return v


class VideoScheduleRequest(BaseModel):
    videos: List[VideoSchedule] = Field(..., min_length=1)


class VideoScheduleResponse(BaseModel):
    success: List[Dict[str, Any]]
    failed: List[Dict[str, Any]]
    total: int
    success_count: int
    failed_count: int
