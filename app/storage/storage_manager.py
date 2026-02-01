import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from app.config.settings import settings


class StorageManager:
    """Manages JSON-based storage operations"""
    
    def __init__(self):
        self.storage_dir = Path(settings.storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        self.users_file = Path(settings.users_file)
        self.tokens_file = Path(settings.tokens_file)
        self.jobs_file = Path(settings.jobs_file)
        self.recent_videos_file = Path(settings.recent_videos_file)
        self.failed_videos_file = Path(settings.failed_videos_file)
        
        self._ensure_files_exist()
    
    def _ensure_files_exist(self):
        """Create JSON files if they don't exist"""
        for file_path in [self.users_file, self.tokens_file, self.jobs_file, 
                          self.recent_videos_file, self.failed_videos_file]:
            if not file_path.exists():
                file_path.parent.mkdir(parents=True, exist_ok=True)
                self._write_json(file_path, {})
    
    def _read_json(self, file_path: Path) -> Dict[str, Any]:
        """Read JSON file"""
        if not file_path.exists():
            return {}
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _write_json(self, file_path: Path, data: Dict[str, Any]):
        """Write JSON file"""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    # User operations
    def get_users(self) -> Dict[str, Any]:
        """Get all users"""
        return self._read_json(self.users_file)
    
    def save_user(self, user_id: str, user_data: Dict[str, Any]):
        """Save or update user"""
        users = self.get_users()
        users[user_id] = user_data
        self._write_json(self.users_file, users)
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        users = self.get_users()
        return users.get(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        users = self.get_users()
        for user_id, user_data in users.items():
            if user_data.get('email') == email:
                return {**user_data, 'id': user_id}
        return None
    
    # Token operations
    def get_tokens(self) -> Dict[str, Any]:
        """Get all YouTube tokens"""
        return self._read_json(self.tokens_file)
    
    def save_token(self, user_id: str, channel_id: str, token_data: Dict[str, Any]):
        """Save or update YouTube token"""
        tokens = self.get_tokens()
        if user_id not in tokens:
            tokens[user_id] = {}
        tokens[user_id][channel_id] = token_data
        self._write_json(self.tokens_file, tokens)
    
    def get_user_tokens(self, user_id: str) -> Dict[str, Any]:
        """Get all tokens for a user"""
        tokens = self.get_tokens()
        return tokens.get(user_id, {})
    
    def get_token(self, user_id: str, channel_id: str) -> Optional[Dict[str, Any]]:
        """Get specific token"""
        tokens = self.get_user_tokens(user_id)
        return tokens.get(channel_id)
    
    # Job operations
    def get_jobs(self) -> Dict[str, Any]:
        """Get all scheduled jobs"""
        return self._read_json(self.jobs_file)
    
    def save_job(self, job_id: str, job_data: Dict[str, Any]):
        """Save or update job"""
        jobs = self.get_jobs()
        jobs[job_id] = job_data
        self._write_json(self.jobs_file, jobs)
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID"""
        jobs = self.get_jobs()
        return jobs.get(job_id)
    
    def get_user_jobs(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all jobs for a user"""
        jobs = self.get_jobs()
        return [job for job in jobs.values() if job.get('user_id') == user_id]
    
    def update_job_status(self, job_id: str, status: str, error_message: Optional[str] = None, video_id: Optional[str] = None):
        """Update job status"""
        jobs = self.get_jobs()
        if job_id in jobs:
            jobs[job_id]['status'] = status
            if error_message:
                jobs[job_id]['error_message'] = error_message
            if video_id:
                jobs[job_id]['video_id'] = video_id
            self._write_json(self.jobs_file, jobs)
    
    # Recent videos operations
    def get_recent_videos(self) -> Dict[str, Any]:
        """Get all recent videos (organized by user_id -> channel_id -> list)"""
        return self._read_json(self.recent_videos_file)
    
    def save_recent_videos(self, user_id: str, channel_id: str, videos: List[Dict[str, Any]], max_entries: int = 20):
        """Save recent videos for a channel, keeping only the most recent max_entries"""
        all_recent = self.get_recent_videos()
        
        if user_id not in all_recent:
            all_recent[user_id] = {}
        
        # Sort by date (most recent first) and keep only max_entries
        videos_sorted = sorted(videos, key=lambda x: x.get('date', ''), reverse=True)[:max_entries]
        all_recent[user_id][channel_id] = videos_sorted
        
        self._write_json(self.recent_videos_file, all_recent)
    
    def get_channel_recent_videos(self, user_id: str, channel_id: str) -> List[Dict[str, Any]]:
        """Get recent videos for a specific channel"""
        all_recent = self.get_recent_videos()
        return all_recent.get(user_id, {}).get(channel_id, [])
    
    # Failed videos operations
    def get_failed_videos(self) -> Dict[str, Any]:
        """Get all failed videos (organized by user_id -> channel_id -> list)"""
        return self._read_json(self.failed_videos_file)
    
    def save_failed_video(self, user_id: str, channel_id: str, failed_video: Dict[str, Any], max_entries: int = 20):
        """Save a failed video, keeping only the most recent max_entries"""
        all_failed = self.get_failed_videos()
        
        if user_id not in all_failed:
            all_failed[user_id] = {}
        
        if channel_id not in all_failed[user_id]:
            all_failed[user_id][channel_id] = []
        
        # Add new failure
        all_failed[user_id][channel_id].append(failed_video)
        
        # Sort by failure_time (most recent first) and keep only max_entries
        all_failed[user_id][channel_id] = sorted(
            all_failed[user_id][channel_id],
            key=lambda x: x.get('failure_time', ''),
            reverse=True
        )[:max_entries]
        
        self._write_json(self.failed_videos_file, all_failed)
    
    def get_channel_failed_videos(self, user_id: str, channel_id: str) -> List[Dict[str, Any]]:
        """Get failed videos for a specific channel"""
        all_failed = self.get_failed_videos()
        return all_failed.get(user_id, {}).get(channel_id, [])


storage_manager = StorageManager()
