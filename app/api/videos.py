from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Query
from app.models.video import VideoScheduleRequest, VideoScheduleResponse
from app.json_handler.validator import JSONValidator
from app.youtube.client import YouTubeClient
from app.drive.downloader import DriveDownloader
from app.scheduler.job_manager import job_manager
from app.auth.dependencies import get_current_user
from app.storage.storage_manager import storage_manager
from datetime import datetime, timezone
import json
import uuid

router = APIRouter(prefix="/api/videos", tags=["videos"])


@router.post("/schedule")
async def schedule_videos(
    channel_id: str = Query(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload JSON file and schedule videos"""
    
    # Validate file type
    if not file.filename.endswith('.json'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a JSON file"
        )
    
    # Read and parse JSON
    content = await file.read()
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON format"
        )
    
    # Validate JSON structure
    is_valid, valid_videos, errors = JSONValidator.validate_request(data)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid videos found in JSON",
            errors=errors
        )
    
    # Verify channel access
    token = storage_manager.get_token(current_user["id"], channel_id)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found or not authorized"
        )
    
    # Process videos
    success_list = []
    failed_list = []
    
    drive_downloader = DriveDownloader(current_user["id"], channel_id)
    youtube_client = YouTubeClient(current_user["id"], channel_id)
    
    for video in valid_videos:
        job_id = str(uuid.uuid4())
        video_path = None
        thumbnail_path = None
        
        try:
            # Download video from Drive
            video_path = drive_downloader.download_file(
                video.video_drive_url,
                filename=f"{job_id}_video.mp4"
            )
            
            # Download thumbnail if provided
            thumbnail_path = None
            if video.thumbnail_drive_url and video.thumbnail_drive_url.strip():
                try:
                    thumbnail_path = drive_downloader.download_file(
                        video.thumbnail_drive_url,
                        filename=f"{job_id}_thumbnail.jpg"
                    )
                except Exception as e:
                    # Thumbnail download failure is not critical
                    print(f"Thumbnail download failed: {e}")
                    thumbnail_path = None
            
            # Parse publish datetime first (handle timezone-aware strings)
            publish_datetime_str = video.publish_datetime
            if publish_datetime_str.endswith('Z'):
                publish_datetime_str = publish_datetime_str.replace('Z', '+00:00')
            publish_datetime = datetime.fromisoformat(publish_datetime_str)
            
            # Ensure datetime is timezone-aware (convert to UTC if needed)
            if publish_datetime.tzinfo is None:
                # If naive, assume it's already UTC
                publish_datetime = publish_datetime.replace(tzinfo=timezone.utc)
            else:
                # Convert to UTC
                publish_datetime = publish_datetime.astimezone(timezone.utc)
            
            # Upload to YouTube as Private WITH SCHEDULING (publishAt in status object)
            upload_result = youtube_client.upload_video(
                video_path=video_path,
                title=video.title,
                description=video.description,
                tags=video.tags,
                category_id=video.category_id,
                made_for_kids=video.made_for_kids,
                privacy_status="private",
                publish_at=publish_datetime  # Set publishAt during upload
            )
            
            video_id = upload_result["video_id"]
            
            # Upload thumbnail if available
            if thumbnail_path:
                try:
                    youtube_client.upload_thumbnail(video_id, thumbnail_path)
                except Exception as e:
                    # Thumbnail upload failure is not critical
                    print(f"Thumbnail upload failed: {e}")
            
            # Create job record
            job_data = {
                "job_id": job_id,
                "user_id": current_user["id"],
                "channel_id": channel_id,
                "video_id": video_id,
                "video_title": video.title,
                "status": "scheduled",  # Already scheduled during upload
                "publish_datetime": publish_datetime.isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "error_message": None,
                "metadata": {
                    "description": video.description,
                    "tags": video.tags,
                    "category_id": video.category_id
                }
            }
            storage_manager.save_job(job_id, job_data)
            
            # Also add to APScheduler as backup (in case YouTube scheduling fails)
            job_manager.schedule_publish(
                current_user["id"],
                channel_id,
                video_id,
                publish_datetime,
                job_id
            )
            
            success_list.append({
                "job_id": job_id,
                "video_id": video_id,
                "title": video.title,
                "publish_datetime": video.publish_datetime
            })
            
        except Exception as e:
            error_message = str(e)
            failed_list.append({
                "title": video.title,
                "error": error_message
            })
            
            # Save to failed videos storage
            try:
                failed_video_data = {
                    'title': video.title,
                    'attempted_schedule_time': video.publish_datetime,
                    'failure_time': datetime.now(timezone.utc).isoformat(),
                    'failure_reason': error_message,
                    'job_id': job_id,
                    'video_id': None
                }
                storage_manager.save_failed_video(
                    current_user["id"],
                    channel_id,
                    failed_video_data,
                    max_entries=20
                )
            except Exception as save_error:
                print(f"Failed to save failed video to storage: {save_error}")
        
        finally:
            # Cleanup temporary files
            if video_path:
                drive_downloader.cleanup_file(video_path)
            if thumbnail_path:
                drive_downloader.cleanup_file(thumbnail_path)
    
    return VideoScheduleResponse(
        success=success_list,
        failed=failed_list,
        total=len(valid_videos),
        success_count=len(success_list),
        failed_count=len(failed_list)
    )


@router.get("/jobs")
async def get_jobs(current_user: dict = Depends(get_current_user), channel_id: str = Query(None)):
    """Get all scheduled jobs for current user - shows videos that are scheduled and not yet public"""
    jobs = storage_manager.get_user_jobs(current_user["id"])
    
    # Fetch scheduled videos directly from YouTube
    youtube_scheduled_videos = {}
    
    # If channel_id is provided, use it; otherwise try all connected channels
    channels_to_check = []
    if channel_id:
        channels_to_check = [channel_id]
    else:
        # Get all connected channels for this user
        from app.api.youtube import get_channels
        try:
            channels_response = await get_channels(current_user)
            channels_to_check = [ch['id'] for ch in channels_response.get('channels', [])]
        except Exception as e:
            print(f"Error getting channels: {e}")
    
    # Fetch scheduled videos from each channel
    for ch_id in channels_to_check:
        try:
            print(f"Fetching scheduled videos for channel: {ch_id}")
            youtube_client = YouTubeClient(current_user["id"], ch_id)
            scheduled_videos = youtube_client.get_scheduled_videos()
            print(f"Found {len(scheduled_videos)} scheduled videos from channel {ch_id}")
            for video in scheduled_videos:
                youtube_scheduled_videos[video['video_id']] = video
        except Exception as e:
            import traceback
            print(f"Error fetching scheduled videos from YouTube channel {ch_id}: {e}")
            print(traceback.format_exc())
    
    # Sync status with YouTube for each job and filter
    synced_jobs = []
    current_time = datetime.now(timezone.utc)
    
    for job in jobs:
        is_scheduled_and_not_public = False
        
        # Extract video_description from metadata if available
        if job.get('metadata') and isinstance(job['metadata'], dict):
            job['video_description'] = job['metadata'].get('description', '')
        else:
            job['video_description'] = ''
        
        if job.get('video_id') and job.get('channel_id'):
            try:
                youtube_client = YouTubeClient(current_user["id"], job['channel_id'])
                video_status = youtube_client.get_video_status(job['video_id'])
                
                if video_status:
                    # Update job status based on YouTube status
                    youtube_privacy = video_status['privacy_status']
                    publish_at = video_status.get('publish_at')
                    
                    # Update description from YouTube if available and not already set
                    if not job.get('video_description') and video_status.get('description'):
                        job['video_description'] = video_status.get('description', '')
                    
                    # Determine status based on YouTube privacy and publish time
                    if youtube_privacy == 'public':
                        job['status'] = 'published'
                        # Skip public videos - don't include in scheduled jobs list
                        is_scheduled_and_not_public = False
                    elif youtube_privacy in ['private', 'unlisted'] and publish_at:
                        # Check if scheduled time has passed
                        try:
                            scheduled_time = datetime.fromisoformat(publish_at.replace('Z', '+00:00'))
                            if scheduled_time <= current_time:
                                # Time has passed but still private - might be processing
                                job['status'] = 'published'
                                is_scheduled_and_not_public = False
                            else:
                                # Still scheduled for future
                                job['status'] = 'scheduled'
                                is_scheduled_and_not_public = True
                        except:
                            job['status'] = 'scheduled'
                            is_scheduled_and_not_public = True
                    elif youtube_privacy in ['private', 'unlisted']:
                        # Private but no publish_at - check if we have a scheduled time in job
                        job_publish_time = None
                        try:
                            if job.get('publish_datetime'):
                                job_publish_time = datetime.fromisoformat(
                                    job['publish_datetime'].replace('Z', '+00:00')
                                )
                                if job_publish_time > current_time:
                                    job['status'] = 'scheduled'
                                    is_scheduled_and_not_public = True
                                else:
                                    job['status'] = 'uploaded'
                                    is_scheduled_and_not_public = False
                            else:
                                job['status'] = 'uploaded'
                                is_scheduled_and_not_public = False
                        except:
                            job['status'] = 'uploaded'
                            is_scheduled_and_not_public = False
                    else:
                        job['status'] = 'uploaded'
                        is_scheduled_and_not_public = False
                    
                    # Update metadata
                    job['youtube_privacy'] = youtube_privacy
                    job['youtube_publish_at'] = publish_at
            except Exception as e:
                # If we can't sync, check job's own publish_datetime
                print(f"Error syncing job {job.get('job_id')}: {e}")
                try:
                    if job.get('publish_datetime'):
                        job_publish_time = datetime.fromisoformat(
                            job['publish_datetime'].replace('Z', '+00:00')
                        )
                        if job_publish_time > current_time and job.get('status') in ['scheduled', 'uploaded']:
                            is_scheduled_and_not_public = True
                            job['status'] = 'scheduled'
                except:
                    pass
        else:
            # No video_id yet - check if it's scheduled for future
            try:
                if job.get('publish_datetime'):
                    job_publish_time = datetime.fromisoformat(
                        job['publish_datetime'].replace('Z', '+00:00')
                    )
                    if job_publish_time > current_time and job.get('status') in ['scheduled', 'uploaded', 'pending']:
                        is_scheduled_and_not_public = True
            except:
                pass
        
        # Only include jobs that are scheduled and not yet public
        if is_scheduled_and_not_public:
            synced_jobs.append(job)
            # Remove from YouTube scheduled videos if it's already in our DB
            if job.get('video_id') in youtube_scheduled_videos:
                del youtube_scheduled_videos[job.get('video_id')]
    
    # Add videos from YouTube that aren't in our database
    print(f"Processing {len(youtube_scheduled_videos)} videos from YouTube")
    for video_id, video_data in youtube_scheduled_videos.items():
        try:
            publish_at = video_data.get('publish_at')
            if publish_at:
                scheduled_time = datetime.fromisoformat(publish_at.replace('Z', '+00:00'))
                if scheduled_time > current_time:
                    # This is a scheduled video not in our DB - add it
                    synced_jobs.append({
                        'job_id': f"youtube_{video_id}",
                        'video_id': video_id,
                        'video_title': video_data['title'],
                        'video_description': video_data.get('description', ''),
                        'status': 'scheduled',
                        'publish_datetime': publish_at,
                        'channel_id': channel_id or (channels_to_check[0] if channels_to_check else ''),
                        'user_id': current_user["id"],
                        'youtube_privacy': video_data['privacy_status'],
                        'youtube_publish_at': publish_at,
                        'created_at': datetime.now(timezone.utc).isoformat(),
                        'from_youtube': True  # Flag to indicate this came from YouTube
                    })
                    print(f"Added scheduled video: {video_data['title']} (publish: {publish_at})")
        except Exception as e:
            import traceback
            print(f"Error processing YouTube video {video_id}: {e}")
            print(traceback.format_exc())
    
    # Sort by publish_datetime (earliest first - so upcoming videos appear first)
    synced_jobs.sort(key=lambda x: x.get('publish_datetime', ''))
    
    print(f"Returning {len(synced_jobs)} scheduled jobs (from DB: {len(jobs)}, from YouTube: {len(youtube_scheduled_videos)})")
    
    return {"jobs": synced_jobs}


@router.get("/jobs/debug")
async def debug_scheduled_videos(current_user: dict = Depends(get_current_user), channel_id: str = Query(...)):
    """Debug endpoint to test YouTube scheduled videos fetching"""
    try:
        youtube_client = YouTubeClient(current_user["id"], channel_id)
        scheduled_videos = youtube_client.get_scheduled_videos()
        
        return {
            "channel_id": channel_id,
            "scheduled_videos_count": len(scheduled_videos),
            "scheduled_videos": scheduled_videos
        }
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str, current_user: dict = Depends(get_current_user)):
    """Get status of a specific job"""
    job = storage_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Sync with YouTube if video_id exists
    if job.get('video_id') and job.get('channel_id'):
        try:
            youtube_client = YouTubeClient(current_user["id"], job['channel_id'])
            video_status = youtube_client.get_video_status(job['video_id'])
            
            if video_status:
                youtube_privacy = video_status['privacy_status']
                publish_at = video_status.get('publish_at')
                
                # Update status based on YouTube
                if youtube_privacy == 'public':
                    job['status'] = 'published'
                elif youtube_privacy == 'private' and publish_at:
                    try:
                        scheduled_time = datetime.fromisoformat(publish_at.replace('Z', '+00:00'))
                        if scheduled_time <= datetime.now(timezone.utc):
                            job['status'] = 'published'
                        else:
                            job['status'] = 'scheduled'
                    except:
                        job['status'] = 'scheduled'
                else:
                    job['status'] = 'uploaded'
                
                job['youtube_privacy'] = youtube_privacy
                job['youtube_publish_at'] = publish_at
        except Exception as e:
            print(f"Error syncing job {job_id}: {e}")
    
    # Get scheduler status
    job_status = job_manager.get_job_status(job_id)
    
    return job_status or job


@router.post("/jobs/sync")
async def sync_jobs_with_youtube(current_user: dict = Depends(get_current_user)):
    """Sync all jobs with YouTube to get current status"""
    jobs = storage_manager.get_user_jobs(current_user["id"])
    
    synced_count = 0
    for job in jobs:
        if job.get('video_id') and job.get('channel_id'):
            try:
                youtube_client = YouTubeClient(current_user["id"], job['channel_id'])
                video_status = youtube_client.get_video_status(job['video_id'])
                
                if video_status:
                    youtube_privacy = video_status['privacy_status']
                    publish_at = video_status.get('publish_at')
                    
                    # Update status
                    if youtube_privacy == 'public':
                        new_status = 'published'
                    elif youtube_privacy == 'private' and publish_at:
                        try:
                            scheduled_time = datetime.fromisoformat(publish_at.replace('Z', '+00:00'))
                            if scheduled_time <= datetime.now(timezone.utc):
                                new_status = 'published'
                            else:
                                new_status = 'scheduled'
                        except:
                            new_status = 'scheduled'
                    else:
                        new_status = 'uploaded'
                    
                    if job.get('status') != new_status:
                        storage_manager.update_job_status(job['job_id'], new_status, video_id=job['video_id'])
                        synced_count += 1
            except Exception as e:
                print(f"Error syncing job {job.get('job_id')}: {e}")
    
    return {
        "message": f"Synced {synced_count} jobs with YouTube",
        "total_jobs": len(jobs),
        "synced": synced_count
    }


@router.get("/recent")
async def get_recent_videos(
    channel_id: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    """Get recent videos for the selected channel"""
    if not channel_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="channel_id is required"
        )
    
    # Verify channel access
    token = storage_manager.get_token(current_user["id"], channel_id)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found or not authorized"
        )
    
    # Get from storage
    recent_videos = storage_manager.get_channel_recent_videos(current_user["id"], channel_id)
    
    return {"videos": recent_videos}


@router.post("/recent/refresh")
async def refresh_recent_videos(
    channel_id: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    """Refresh recent videos from YouTube API and update storage"""
    if not channel_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="channel_id is required"
        )
    
    # Verify channel access
    token = storage_manager.get_token(current_user["id"], channel_id)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found or not authorized"
        )
    
    try:
        # Fetch from YouTube
        youtube_client = YouTubeClient(current_user["id"], channel_id)
        recent_videos = youtube_client.get_recent_videos(max_results=20)
        
        # Save to storage (auto-deletes older entries, keeps max 20)
        storage_manager.save_recent_videos(
            current_user["id"],
            channel_id,
            recent_videos,
            max_entries=20
        )
        
        return {
            "message": f"Refreshed {len(recent_videos)} recent videos",
            "videos": recent_videos
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh recent videos: {str(e)}"
        )


@router.get("/failed")
async def get_failed_videos(
    channel_id: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    """Get failed videos for the selected channel"""
    if not channel_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="channel_id is required"
        )
    
    # Verify channel access
    token = storage_manager.get_token(current_user["id"], channel_id)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found or not authorized"
        )
    
    # Get from storage
    failed_videos = storage_manager.get_channel_failed_videos(current_user["id"], channel_id)
    
    return {"videos": failed_videos}


@router.post("/failed/refresh")
async def refresh_failed_videos(
    channel_id: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    """Refresh failed videos from jobs and update storage"""
    if not channel_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="channel_id is required"
        )
    
    # Verify channel access
    token = storage_manager.get_token(current_user["id"], channel_id)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found or not authorized"
        )
    
    try:
        # Get failed jobs for this channel
        all_jobs = storage_manager.get_user_jobs(current_user["id"])
        failed_jobs = [
            job for job in all_jobs
            if job.get('channel_id') == channel_id
            and job.get('status') == 'failed'
            and job.get('error_message')
        ]
        
        # Convert to failed videos format
        failed_videos = []
        for job in failed_jobs:
            failed_videos.append({
                'title': job.get('video_title', 'Unknown'),
                'attempted_schedule_time': job.get('publish_datetime', ''),
                'failure_time': job.get('created_at', ''),
                'failure_reason': job.get('error_message', 'Unknown error'),
                'job_id': job.get('job_id', ''),
                'video_id': job.get('video_id', '')
            })
        
        # Sort by failure_time (most recent first)
        failed_videos.sort(key=lambda x: x.get('failure_time', ''), reverse=True)
        
        # Keep only the most recent 20
        failed_videos = failed_videos[:20]
        
        # Save to storage (this will auto-limit to 20)
        for failed_video in failed_videos:
            storage_manager.save_failed_video(
                current_user["id"],
                channel_id,
                failed_video,
                max_entries=20
            )
        
        return {
            "message": f"Refreshed {len(failed_videos)} failed videos",
            "videos": failed_videos
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh failed videos: {str(e)}"
        )
