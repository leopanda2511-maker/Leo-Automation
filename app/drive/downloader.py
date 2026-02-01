import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from app.youtube.oauth import get_credentials_from_token, refresh_credentials
from app.storage.storage_manager import storage_manager
from typing import Optional
from pathlib import Path
import tempfile


class DriveDownloader:
    """Google Drive file downloader"""
    
    def __init__(self, user_id: str, channel_id: str):
        self.user_id = user_id
        self.channel_id = channel_id
        self._service = None
        self.temp_dir = Path(tempfile.gettempdir()) / "youtube_scheduler"
        self.temp_dir.mkdir(exist_ok=True)
    
    def _get_service(self):
        """Get Drive service with valid credentials"""
        if self._service is None:
            token_data = storage_manager.get_token(self.user_id, self.channel_id)
            if not token_data:
                raise ValueError("No token found for this channel")
            
            credentials = get_credentials_from_token(token_data)
            credentials = refresh_credentials(credentials)
            self._service = build('drive', 'v3', credentials=credentials)
        
        return self._service
    
    def _extract_file_id(self, url: str) -> Optional[str]:
        """Extract file ID from Google Drive URL"""
        if '/file/d/' in url:
            file_id = url.split('/file/d/')[1].split('/')[0]
            return file_id
        elif 'id=' in url:
            file_id = url.split('id=')[1].split('&')[0]
            return file_id
        return None
    
    def download_file(self, drive_url: str, filename: Optional[str] = None) -> str:
        """Download file from Google Drive"""
        file_id = self._extract_file_id(drive_url)
        if not file_id:
            raise ValueError("Invalid Google Drive URL")
        
        service = self._get_service()
        
        try:
            # Get file metadata
            file_metadata = service.files().get(fileId=file_id).execute()
            
            # Determine filename
            if not filename:
                filename = file_metadata.get('name', f'download_{file_id}')
            
            # Download file using Google API client
            from io import BytesIO
            from googleapiclient.http import MediaIoBaseDownload
            
            request = service.files().get_media(fileId=file_id)
            file_handle = BytesIO()
            downloader = MediaIoBaseDownload(file_handle, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                if status:
                    print(f"Download progress: {int(status.progress() * 100)}%")
            
            file_path = self.temp_dir / filename
            with open(file_path, 'wb') as f:
                f.write(file_handle.getvalue())
            
            return str(file_path)
        except HttpError as e:
            raise Exception(f"Drive download error: {e}")
    
    def cleanup_file(self, file_path: str):
        """Delete temporary file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error cleaning up file {file_path}: {e}")
