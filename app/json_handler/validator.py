from app.models.video import VideoScheduleRequest, VideoSchedule
from typing import List, Dict, Any
from pydantic import ValidationError


class JSONValidator:
    """Validates JSON video schedule requests"""
    
    @staticmethod
    def validate_request(data: Dict[str, Any]) -> tuple[bool, List[VideoSchedule], List[Dict[str, Any]]]:
        """
        Validate video schedule request
        
        Returns:
            (is_valid, valid_videos, errors)
        """
        errors = []
        valid_videos = []
        
        if not isinstance(data, dict):
            return False, [], [{"error": "Invalid JSON structure. Expected object."}]
        
        if "videos" not in data:
            return False, [], [{"error": "Missing 'videos' field"}]
        
        if not isinstance(data["videos"], list):
            return False, [], [{"error": "'videos' must be an array"}]
        
        if len(data["videos"]) == 0:
            return False, [], [{"error": "'videos' array cannot be empty"}]
        
        for idx, video_data in enumerate(data["videos"]):
            try:
                video = VideoSchedule(**video_data)
                valid_videos.append(video)
            except ValidationError as e:
                errors.append({
                    "index": idx,
                    "video": video_data.get("title", "Unknown"),
                    "errors": [err["msg"] for err in e.errors()]
                })
        
        is_valid = len(valid_videos) > 0
        return is_valid, valid_videos, errors
