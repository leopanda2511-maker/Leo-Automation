from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    oauth_redirect_uri: str = "http://localhost:8000/api/youtube/callback"
    
    # JWT
    jwt_secret_key: str = "change-this-secret-key-in-production"
    jwt_algorithm: str = "HS256"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Storage paths
    storage_dir: str = "storage"
    users_file: str = "storage/users.json"
    tokens_file: str = "storage/youtube_tokens.json"
    jobs_file: str = "storage/scheduled_jobs.json"
    recent_videos_file: str = "storage/recent_videos.json"
    failed_videos_file: str = "storage/failed_videos.json"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
