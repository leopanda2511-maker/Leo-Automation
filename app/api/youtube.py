from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import RedirectResponse
from app.youtube.oauth import get_authorization_url, exchange_code_for_token
from app.youtube.client import YouTubeClient
from app.auth.dependencies import get_current_user
from app.storage.storage_manager import storage_manager
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/api/youtube", tags=["youtube"])


@router.get("/authorize")
async def authorize_youtube(current_user: dict = Depends(get_current_user)):
    """Get YouTube OAuth authorization URL"""
    authorization_url, state = get_authorization_url(user_id=current_user["id"])
    return {
        "authorization_url": authorization_url,
        "state": state
    }


@router.get("/callback")
async def oauth_callback(code: str = Query(...), state: str = Query(None)):
    """Handle OAuth callback and store tokens"""
    try:
        if not state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="State parameter required"
            )
        
        # State contains user_id
        user_id = state
        
        token_data = exchange_code_for_token(code)
        
        # Get channel info
        temp_client = YouTubeClient(user_id, "temp")
        # We need to update this to handle the first-time token
        # For now, we'll store and then fetch channel info
        
        # Store token temporarily to get channel info
        temp_channel_id = str(uuid.uuid4())
        storage_manager.save_token(user_id, temp_channel_id, {
            **token_data,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Get actual channel info
        client = YouTubeClient(user_id, temp_channel_id)
        channel_info = client.get_channel_info()
        actual_channel_id = channel_info["id"]
        
        # Store with actual channel ID
        storage_manager.save_token(user_id, actual_channel_id, {
            **token_data,
            "channel_id": actual_channel_id,
            "channel_name": channel_info["title"],
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Remove temp token
        tokens = storage_manager.get_user_tokens(user_id)
        if temp_channel_id in tokens:
            del tokens[temp_channel_id]
            storage_manager._write_json(
                storage_manager.tokens_file,
                {**storage_manager.get_tokens(), user_id: tokens}
            )
        
        # Redirect to frontend with success
        return RedirectResponse(
            url=f"/?oauth_success=true&channel={channel_info['title']}",
            status_code=302
        )
    except Exception as e:
        # Redirect to frontend with error
        return RedirectResponse(
            url=f"/?oauth_error={str(e)}",
            status_code=302
        )


@router.get("/channels")
async def get_channels(current_user: dict = Depends(get_current_user)):
    """Get all connected YouTube channels for current user"""
    tokens = storage_manager.get_user_tokens(current_user["id"])
    
    channels = []
    for channel_id, token_data in tokens.items():
        try:
            client = YouTubeClient(current_user["id"], channel_id)
            channel_info = client.get_channel_info()
            channels.append(channel_info)
        except Exception as e:
            # Skip channels with invalid tokens
            continue
    
    return {"channels": channels}
