# YouTube Video Scheduling Automation System

A web-based automation system for scheduling YouTube video uploads from Google Drive using JSON-based configuration.

## Features

- User authentication (email + password)
- Multiple YouTube channel support per user
- OAuth 2.0 YouTube authorization
- Batch video scheduling from JSON file
- Google Drive video download
- Automatic video publishing at scheduled times
- Recent videos tracking (latest 20 per channel)
- Failed videos tracking (latest 20 per channel)
- Refresh functionality for all sections
- Clean architecture with SOLID principles

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Google OAuth credentials:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable YouTube Data API v3 and Google Drive API
   - Create OAuth 2.0 credentials
   - Add authorized redirect URI: `http://localhost:8000/auth/youtube/callback`

3. Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

4. Run the application:
```bash
uvicorn app.main:app --reload
```

5. Open browser: `http://localhost:8000`

## JSON Schema

Upload a JSON file with the following structure:

```json
{
  "videos": [
    {
      "title": "Video Title",
      "description": "Video description",
      "video_drive_url": "https://drive.google.com/file/d/...",
      "thumbnail_drive_url": "https://drive.google.com/file/d/...",
      "publish_datetime": "2024-12-25T10:00:00",
      "tags": ["tag1", "tag2"],
      "category_id": "22",
      "made_for_kids": false
    }
  ]
}
```

## Deployment

This application is designed to be deployed on Render. Set environment variables in Render dashboard.
