# Project Structure

This document describes the complete project structure and architecture.

## Folder Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py        # Configuration and environment variables
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py            # User data models
│   │   ├── youtube.py         # YouTube channel/token models
│   │   ├── video.py           # Video schedule models
│   │   └── job.py             # Scheduled job models
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   └── storage_manager.py # JSON file storage operations
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── password.py        # Password hashing utilities
│   │   ├── jwt_handler.py     # JWT token generation/validation
│   │   └── dependencies.py    # FastAPI auth dependencies
│   │
│   ├── youtube/
│   │   ├── __init__.py
│   │   ├── oauth.py           # YouTube OAuth 2.0 flow
│   │   └── client.py          # YouTube API client wrapper
│   │
│   ├── drive/
│   │   ├── __init__.py
│   │   └── downloader.py      # Google Drive file downloader
│   │
│   ├── json_handler/
│   │   ├── __init__.py
│   │   └── validator.py       # JSON schema validation
│   │
│   ├── scheduler/
│   │   ├── __init__.py
│   │   └── job_manager.py     # APScheduler job management
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── youtube.py         # YouTube channel endpoints
│   │   └── videos.py          # Video scheduling endpoints
│   │
│   └── frontend/
│       └── index.html         # Single-page frontend application
│
├── storage/                    # Auto-created JSON storage files
│   ├── users.json
│   ├── youtube_tokens.json
│   └── scheduled_jobs.json
│
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── README.md                  # Project overview
├── DEPLOYMENT.md              # Deployment instructions
├── render.yaml                # Render deployment config
└── sample_videos.json         # Example JSON file format
```

## Architecture Principles

### Clean Architecture
- **Separation of Concerns**: Each module has a single responsibility
- **Dependency Inversion**: High-level modules don't depend on low-level modules
- **Interface Segregation**: Small, focused interfaces

### SOLID Principles
- **Single Responsibility**: Each class/module has one job
- **Open/Closed**: Open for extension, closed for modification
- **Liskov Substitution**: Subtypes are substitutable
- **Interface Segregation**: No client forced to depend on unused methods
- **Dependency Inversion**: Depend on abstractions, not concretions

## Data Flow

1. **User Authentication**
   - User signs up/logs in → JWT token generated
   - Token stored in localStorage (frontend)
   - Token validated on each API request

2. **YouTube Authorization**
   - User clicks "Connect YouTube" → OAuth flow initiated
   - Google redirects to callback → Tokens stored
   - Channel info fetched and displayed

3. **Video Scheduling**
   - User uploads JSON file → Validated
   - For each video:
     - Download from Google Drive
     - Upload to YouTube (Private)
     - Schedule publish job
   - Results returned (success/failed)

4. **Video Publishing**
   - APScheduler triggers at scheduled time
   - Video privacy changed to Public
   - Job status updated

## Storage

All data stored in JSON files:
- `users.json`: User accounts (email, password hash)
- `youtube_tokens.json`: OAuth tokens per user/channel
- `scheduled_jobs.json`: Video scheduling jobs
- `recent_videos.json`: Recent videos cache (latest 20 per channel, synced from YouTube)
- `failed_videos.json`: Failed uploads cache (latest 20 per channel)

## API Endpoints

### Authentication
- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user

### YouTube
- `GET /api/youtube/authorize` - Get OAuth URL
- `GET /api/youtube/callback` - OAuth callback handler
- `GET /api/youtube/channels` - List connected channels

### Videos
- `POST /api/videos/schedule` - Upload JSON and schedule videos
- `GET /api/videos/jobs` - List scheduled jobs
- `GET /api/videos/jobs/{job_id}` - Get job status
- `POST /api/videos/jobs/sync` - Sync jobs with YouTube
- `GET /api/videos/recent?channel_id=...` - Get recent videos (cached)
- `POST /api/videos/recent/refresh?channel_id=...` - Refresh recent videos from YouTube
- `GET /api/videos/failed?channel_id=...` - Get failed videos (cached)
- `POST /api/videos/failed/refresh?channel_id=...` - Refresh failed videos from jobs

## Frontend

Single-page application with:
- Authentication UI
- Channel management
- JSON file upload
- Job status display
- Recent videos view (latest 20 per channel)
- Failed videos view (latest 20 per channel)
- Refresh buttons for all sections
- Real-time updates

## Security

- Password hashing with bcrypt
- JWT token authentication
- OAuth 2.0 for YouTube access
- Environment variables for secrets
- Input validation with Pydantic
