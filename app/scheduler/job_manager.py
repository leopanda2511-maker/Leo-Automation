from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
from app.youtube.client import YouTubeClient
from app.storage.storage_manager import storage_manager
from typing import Callable
import uuid


class JobManager:
    """Manages scheduled video publishing jobs"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
    
    def schedule_publish(
        self,
        user_id: str,
        channel_id: str,
        video_id: str,
        publish_datetime: datetime,
        job_id: str
    ):
        """Schedule a video to be published at a specific datetime"""
        
        def publish_video():
            try:
                client = YouTubeClient(user_id, channel_id)
                client.update_video_privacy(video_id, "public")
                
                # Update job status
                storage_manager.update_job_status(job_id, "published", video_id=video_id)
            except Exception as e:
                storage_manager.update_job_status(
                    job_id,
                    "failed",
                    error_message=str(e),
                    video_id=video_id
                )
        
        # Schedule the job
        self.scheduler.add_job(
            publish_video,
            trigger=DateTrigger(run_date=publish_datetime),
            id=job_id,
            replace_existing=True
        )
    
    def get_job_status(self, job_id: str) -> dict:
        """Get status of a scheduled job"""
        job = storage_manager.get_job(job_id)
        if not job:
            return None
        
        # Check if job is in scheduler
        scheduled_job = self.scheduler.get_job(job_id)
        if scheduled_job:
            job["scheduled"] = True
            job["next_run_time"] = scheduled_job.next_run_time.isoformat() if scheduled_job.next_run_time else None
        else:
            job["scheduled"] = False
        
        return job


job_manager = JobManager()
