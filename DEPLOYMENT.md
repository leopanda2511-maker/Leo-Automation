# Deployment Guide

## Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   - Copy `.env.example` to `.env`
   - Fill in your Google OAuth credentials:
     - `GOOGLE_CLIENT_ID`: From Google Cloud Console
     - `GOOGLE_CLIENT_SECRET`: From Google Cloud Console
     - `OAUTH_REDIRECT_URI`: Must match your Google Console settings
     - `JWT_SECRET_KEY`: Generate a secure random string

3. **Set up Google Cloud Console:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable APIs:
     - YouTube Data API v3
     - Google Drive API
   - Create OAuth 2.0 credentials (Web application)
   - Add authorized redirect URI: `http://localhost:8000/api/youtube/callback`

4. **Run the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Access the application:**
   - Open browser: `http://localhost:8000`

## Deploy to Render

1. **Create a new Web Service on Render:**
   - Connect your GitHub repository
   - Select "Python" as environment
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

2. **Set environment variables in Render:**
   - `GOOGLE_CLIENT_ID`: Your Google OAuth client ID
   - `GOOGLE_CLIENT_SECRET`: Your Google OAuth client secret
   - `OAUTH_REDIRECT_URI`: `https://your-app-name.onrender.com/api/youtube/callback`
   - `JWT_SECRET_KEY`: Generate a secure random string
   - `JWT_ALGORITHM`: `HS256`
   - `HOST`: `0.0.0.0`
   - `PORT`: (Auto-set by Render)

3. **Update Google Cloud Console:**
   - Add your Render URL to authorized redirect URIs:
     - `https://your-app-name.onrender.com/api/youtube/callback`

4. **Deploy:**
   - Render will automatically deploy on push to main branch
   - Or manually trigger deployment from Render dashboard

## Important Notes

- The `storage/` directory will be created automatically
- JSON files will be created on first use:
  - `users.json`: User accounts
  - `youtube_tokens.json`: OAuth tokens
  - `scheduled_jobs.json`: Video scheduling jobs
  - `recent_videos.json`: Recent videos cache (latest 20 per channel)
  - `failed_videos.json`: Failed uploads cache (latest 20 per channel)
- For production, consider using a persistent volume or database for storage
- Make sure your Google OAuth redirect URI matches exactly (including http/https and trailing slashes)
