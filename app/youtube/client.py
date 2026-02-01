from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from app.youtube.oauth import get_credentials_from_token, refresh_credentials
from app.storage.storage_manager import storage_manager
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone


class YouTubeClient:
    """YouTube API client wrapper"""
    
    def __init__(self, user_id: str, channel_id: str):
        self.user_id = user_id
        self.channel_id = channel_id
        self._service = None
    
    def _get_service(self):
        """Get YouTube service with valid credentials"""
        if self._service is None:
            token_data = storage_manager.get_token(self.user_id, self.channel_id)
            if not token_data:
                raise ValueError("No token found for this channel")
            
            credentials = get_credentials_from_token(token_data)
            credentials = refresh_credentials(credentials)
            
            # Update token if refreshed
            if credentials.token != token_data.get("access_token"):
                storage_manager.save_token(
                    self.user_id,
                    self.channel_id,
                    {
                        "access_token": credentials.token,
                        "refresh_token": credentials.refresh_token,
                        "token_uri": credentials.token_uri,
                        "client_id": credentials.client_id,
                        "client_secret": credentials.client_secret,
                        "scopes": credentials.scopes,
                        "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
                        "channel_id": self.channel_id,
                        "channel_name": token_data.get("channel_name", ""),
                        "created_at": token_data.get("created_at", datetime.utcnow().isoformat())
                    }
                )
            
            self._service = build('youtube', 'v3', credentials=credentials)
        
        return self._service
    
    def get_channel_info(self) -> Dict[str, Any]:
        """Get channel information"""
        service = self._get_service()
        try:
            response = service.channels().list(
                part='snippet,statistics',
                mine=True
            ).execute()
            
            if not response.get('items'):
                raise ValueError("No channel found")
            
            channel = response['items'][0]
            return {
                "id": channel['id'],
                "title": channel['snippet']['title'],
                "subscriber_count": int(channel['statistics'].get('subscriberCount', 0)),
                "description": channel['snippet'].get('description', ''),
                "thumbnail": channel['snippet'].get('thumbnails', {}).get('default', {}).get('url', '')
            }
        except HttpError as e:
            raise Exception(f"YouTube API error: {e}")
    
    def get_recent_videos(self, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent videos (uploaded or scheduled) from YouTube channel.
        Returns the most recent videos sorted by published/scheduled date.
        """
        service = self._get_service()
        try:
            all_videos = []
            next_page_token = None
            
            while len(all_videos) < max_results:
                # Step 1: Use search.list to get video IDs for authenticated user
                search_response = service.search().list(
                    part='id,snippet',
                    forMine=True,
                    type='video',
                    maxResults=min(50, max_results - len(all_videos)),
                    order='date',  # Most recent first
                    pageToken=next_page_token
                ).execute()
                
                video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
                
                if not video_ids:
                    break
                
                # Step 2: Get full video details including status
                videos_response = service.videos().list(
                    part='snippet,status',
                    id=','.join(video_ids),
                    maxResults=50
                ).execute()
                
                items = videos_response.get('items', [])
                if not items:
                    break
                
                for video in items:
                    snippet = video.get('snippet', {})
                    status = video.get('status', {})
                    
                    # Determine date (publishedAt or publishAt)
                    published_at = snippet.get('publishedAt', '')
                    publish_at = status.get('publishAt', '')
                    video_date = publish_at if publish_at else published_at
                    
                    # Determine status
                    privacy_status = status.get('privacyStatus', '')
                    upload_status = status.get('uploadStatus', '')
                    
                    if upload_status == 'uploaded':
                        if privacy_status == 'public':
                            video_status = 'published'
                        elif privacy_status in ['private', 'unlisted'] and publish_at:
                            video_status = 'scheduled'
                        else:
                            video_status = 'private'
                    else:
                        video_status = upload_status
                    
                    all_videos.append({
                        'video_id': video['id'],
                        'title': snippet.get('title', ''),
                        'description': snippet.get('description', ''),
                        'status': video_status,
                        'privacy_status': privacy_status,
                        'date': video_date,
                        'published_at': published_at,
                        'scheduled_at': publish_at if publish_at else None,
                        'thumbnail': snippet.get('thumbnails', {}).get('default', {}).get('url', ''),
                        'source': 'youtube'
                    })
                
                next_page_token = search_response.get('nextPageToken')
                if not next_page_token:
                    break
            
            # Sort by date (most recent first) and limit
            all_videos.sort(key=lambda x: x.get('date', ''), reverse=True)
            return all_videos[:max_results]
        except HttpError as e:
            raise Exception(f"YouTube API error: {e}")
    
    def get_scheduled_videos(self) -> List[Dict[str, Any]]:
        """
        Get all scheduled videos from YouTube channel.
        
        According to YouTube Data API v3:
        - Use search.list with forMine=True to get video IDs (requires OAuth 2.0)
        - Then use videos.list with those IDs to get status and snippet
        - Filter by status.privacyStatus == "private" and status.publishAt exists
        - publishAt only exists for scheduled videos
        """
        service = self._get_service()
        try:
            scheduled_videos = []
            next_page_token = None
            
            while True:
                # Step 1: Use search.list to get video IDs for authenticated user
                search_response = service.search().list(
                    part='id',
                    forMine=True,
                    type='video',
                    maxResults=50,
                    pageToken=next_page_token
                ).execute()
                
                video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
                
                if not video_ids:
                    break
                
                # Step 2: Get full video details including status
                videos_response = service.videos().list(
                    part='snippet,status',
                    id=','.join(video_ids),
                    maxResults=50
                ).execute()
                
                items = videos_response.get('items', [])
                if not items:
                    break
                
                for video in items:
                    status = video.get('status', {})
                    privacy_status = status.get('privacyStatus', '')
                    publish_at = status.get('publishAt')
                    
                    # Scheduled videos are identified by:
                    # 1. privacyStatus == "private" (or "unlisted")
                    # 2. publishAt field exists (only present for scheduled videos)
                    if privacy_status in ['private', 'unlisted'] and publish_at:
                        # This is a scheduled video
                        scheduled_videos.append({
                            'video_id': video['id'],
                            'title': video['snippet']['title'],
                            'description': video['snippet'].get('description', ''),
                            'privacy_status': privacy_status,
                            'publish_at': publish_at,
                            'thumbnail': video['snippet'].get('thumbnails', {}).get('default', {}).get('url', '')
                        })
                
                next_page_token = search_response.get('nextPageToken')
                if not next_page_token:
                    break
            
            return scheduled_videos
        except HttpError as e:
            raise Exception(f"YouTube API error: {e}")
    
    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: List[str],
        category_id: str,
        made_for_kids: bool,
        privacy_status: str = "private",
        publish_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Upload video to YouTube with optional scheduling.
        
        If publish_at is provided, the video will be scheduled to publish at that time.
        The publishAt must be set in the status object during upload (not after).
        """
        import os
        from googleapiclient.http import MediaFileUpload
        
        service = self._get_service()
        
        # Check if file exists
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Build status object
        status_obj = {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': made_for_kids
        }
        
        # Add publishAt if scheduling is requested
        # Match working code pattern: publish_at_utc.isoformat()
        if publish_at:
            # Convert to UTC if timezone-aware, otherwise assume UTC
            if publish_at.tzinfo is None:
                # If naive datetime, assume it's already in UTC
                publish_at_utc = publish_at.replace(tzinfo=timezone.utc)
            else:
                # Convert to UTC
                publish_at_utc = publish_at.astimezone(timezone.utc)
            
            # Check if publish time is in the future
            now_utc = datetime.now(timezone.utc)
            if publish_at_utc <= now_utc:
                raise ValueError(
                    f"Publish datetime must be in the future. "
                    f"Provided: {publish_at_utc}, Current: {now_utc}"
                )
            
            # Match working code pattern exactly: publish_at_utc.isoformat()
            # But YouTube API requires Z suffix, not +00:00
            # Remove timezone info for clean ISO format, then add Z
            publish_at_naive_utc = publish_at_utc.replace(tzinfo=None)
            iso_str = publish_at_naive_utc.isoformat() + 'Z'
            
            status_obj['publishAt'] = iso_str
            print(f"[SCHEDULING] Setting publishAt: {status_obj['publishAt']}")
            print(f"[SCHEDULING] Original: {publish_at} -> UTC: {publish_at_utc} -> Naive UTC: {publish_at_naive_utc}")
            print(f"[SCHEDULING] Current UTC: {now_utc}, Time until publish: {publish_at_utc - now_utc}")
            print(f"[SCHEDULING] Full status object: {status_obj}")
        
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': category_id
            },
            'status': status_obj
        }
        
        try:
            # Create MediaFileUpload object
            media = MediaFileUpload(
                video_path,
                chunksize=-1,
                resumable=True,
                mimetype='video/*'
            )
            
            insert_request = service.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            response = None
            while response is None:
                status, response = insert_request.next_chunk()
                if status:
                    print(f"Upload progress: {int(status.progress() * 100)}%")
            
            # Log response to verify scheduling was set correctly
            response_status = response.get('status', {})
            response_publish_at = response_status.get('publishAt')
            response_privacy = response_status.get('privacyStatus')
            response_upload_status = response_status.get('uploadStatus', 'unknown')
            
            print(f"[UPLOAD RESULT] Video ID: {response['id']}")
            print(f"[UPLOAD RESULT] Upload Status: {response_upload_status}")
            print(f"[UPLOAD RESULT] Privacy Status: {response_privacy}")
            print(f"[UPLOAD RESULT] Publish At: {response_publish_at if response_publish_at else 'NOT SET - Video will be public immediately!'}")
            
            if publish_at and not response_publish_at:
                print("[ERROR] publishAt was set in request but NOT in response! Video may be public immediately.")
                print(f"[DEBUG] Request body status: {body.get('status')}")
                print(f"[DEBUG] Full response status: {response_status}")
            elif response_publish_at:
                print(f"[SUCCESS] Video is scheduled to publish at: {response_publish_at}")
            
            return {
                "video_id": response['id'],
                "title": response['snippet']['title'],
                "status": response_privacy,
                "upload_status": response_upload_status,
                "publish_at": response_publish_at
            }
        except HttpError as e:
            raise Exception(f"YouTube upload error: {e}")
    
    def upload_thumbnail(self, video_id: str, thumbnail_path: str):
        """Upload thumbnail for a video"""
        import os
        from googleapiclient.http import MediaFileUpload
        
        service = self._get_service()
        
        # Check if file exists
        if not os.path.exists(thumbnail_path):
            raise FileNotFoundError(f"Thumbnail file not found: {thumbnail_path}")
        
        try:
            # Create MediaFileUpload object for thumbnail
            media = MediaFileUpload(
                thumbnail_path,
                mimetype='image/jpeg'
            )
            
            service.thumbnails().set(
                videoId=video_id,
                media_body=media
            ).execute()
        except HttpError as e:
            raise Exception(f"Thumbnail upload error: {e}")
    
    def get_video_status(self, video_id: str) -> Dict[str, Any]:
        """Get current video status from YouTube"""
        service = self._get_service()
        try:
            response = service.videos().list(
                part='status,snippet',
                id=video_id
            ).execute()
            
            if not response.get('items'):
                return None
            
            video = response['items'][0]
            return {
                'video_id': video_id,
                'privacy_status': video['status']['privacyStatus'],
                'publish_at': video['status'].get('publishAt'),
                'title': video['snippet']['title'],
                'description': video['snippet']['description']
            }
        except HttpError as e:
            raise Exception(f"YouTube API error: {e}")
    
    def update_video_privacy(self, video_id: str, privacy_status: str):
        """Update video privacy status"""
        service = self._get_service()
        try:
            service.videos().update(
                part='status',
                body={
                    'id': video_id,
                    'status': {
                        'privacyStatus': privacy_status
                    }
                }
            ).execute()
        except HttpError as e:
            raise Exception(f"Privacy update error: {e}")
    
    def schedule_video_publish(self, video_id: str, publish_datetime: datetime):
        """Schedule a video to be published at a specific datetime using YouTube's scheduling"""
        service = self._get_service()
        try:
            # Format datetime for YouTube API (RFC 3339 format)
            publish_at = publish_datetime.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            
            service.videos().update(
                part='status',
                body={
                    'id': video_id,
                    'status': {
                        'privacyStatus': 'private',
                        'publishAt': publish_at,
                        'selfDeclaredMadeForKids': False
                    }
                }
            ).execute()
        except HttpError as e:
            raise Exception(f"Schedule publish error: {e}")