from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    PENDING = "pending"
    UPLOADED = "uploaded"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class ScheduledJob(BaseModel):
    job_id: str
    user_id: str
    channel_id: str
    video_id: Optional[str] = None
    video_title: str
    status: JobStatus
    publish_datetime: datetime
    created_at: datetime
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
