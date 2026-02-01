# Render Deployment Guide

Complete step-by-step guide to deploy the YouTube Video Scheduler to Render.

## Prerequisites

1. **GitHub Account** - Your code must be in a GitHub repository
2. **Render Account** - Sign up at [render.com](https://render.com)
3. **Google Cloud Console Access** - For OAuth credentials

## Step 1: Prepare Your Code

1. **Commit all changes to GitHub:**
   ```bash
   git add .
   git commit -m "Ready for Render deployment"
   git push origin main
   ```

2. **Verify your repository structure:**
   - `app/` directory with all Python files
   - `requirements.txt` file
   - `render.yaml` file (optional, but recommended)

## Step 2: Create Render Web Service

1. **Log in to Render Dashboard:**
   - Go to [dashboard.render.com](https://dashboard.render.com)
   - Click "New +" → "Web Service"

2. **Connect Repository:**
   - Connect your GitHub account if not already connected
   - Select your repository: `Leo Automation`
   - Click "Connect"

3. **Configure Service:**
   - **Name:** `youtube-scheduler` (or your preferred name)
   - **Environment:** `Python 3`
   - **Region:** Choose closest to you (e.g., `Oregon (US West)`)
   - **Branch:** `main` (or your default branch)
   - **Root Directory:** Leave empty (or `.` if needed)
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

4. **Click "Create Web Service"**

## Step 3: Set Environment Variables

In the Render dashboard, go to your service → "Environment" tab → Add these variables:

### Required Variables:

1. **GOOGLE_CLIENT_ID**
   - Value: Your Google OAuth Client ID from Google Cloud Console
   - Example: `123456789-abcdefghijklmnop.apps.googleusercontent.com`

2. **GOOGLE_CLIENT_SECRET**
   - Value: Your Google OAuth Client Secret from Google Cloud Console
   - Example: `GOCSPX-abcdefghijklmnopqrstuvwxyz`

3. **OAUTH_REDIRECT_URI**
   - Value: `https://your-app-name.onrender.com/api/youtube/callback`
   - ⚠️ Replace `your-app-name` with your actual Render service name
   - Example: `https://youtube-scheduler.onrender.com/api/youtube/callback`

4. **JWT_SECRET_KEY**
   - Value: Generate a secure random string (at least 32 characters)
   - You can generate one using:
     ```bash
     python -c "import secrets; print(secrets.token_urlsafe(32))"
     ```
   - Example: `your-super-secret-jwt-key-here-min-32-chars`

5. **JWT_ALGORITHM**
   - Value: `HS256`
   - (Fixed value)

6. **HOST**
   - Value: `0.0.0.0`
   - (Fixed value)

### Optional Variables (with defaults):

- `PORT` - Auto-set by Render (don't set manually)
- `STORAGE_DIR` - Defaults to `storage` (optional)
- `USERS_FILE` - Defaults to `storage/users.json` (optional)
- `TOKENS_FILE` - Defaults to `storage/youtube_tokens.json` (optional)
- `JOBS_FILE` - Defaults to `storage/scheduled_jobs.json` (optional)
- `RECENT_VIDEOS_FILE` - Defaults to `storage/recent_videos.json` (optional)
- `FAILED_VIDEOS_FILE` - Defaults to `storage/failed_videos.json` (optional)

## Step 4: Update Google Cloud Console

1. **Go to Google Cloud Console:**
   - Visit [console.cloud.google.com](https://console.cloud.google.com)
   - Select your project

2. **Navigate to OAuth Consent Screen:**
   - Go to "APIs & Services" → "OAuth consent screen"

3. **Add Authorized Redirect URI:**
   - Go to "APIs & Services" → "Credentials"
   - Click on your OAuth 2.0 Client ID
   - Under "Authorized redirect URIs", click "ADD URI"
   - Add: `https://your-app-name.onrender.com/api/youtube/callback`
   - ⚠️ Replace `your-app-name` with your actual Render service name
   - Click "SAVE"

4. **Verify APIs are enabled:**
   - YouTube Data API v3
   - Google Drive API

## Step 5: Deploy

1. **Manual Deploy:**
   - In Render dashboard, click "Manual Deploy" → "Deploy latest commit"
   - Or push a new commit to trigger auto-deploy

2. **Monitor Deployment:**
   - Watch the build logs in Render dashboard
   - Wait for "Your service is live" message

3. **Get Your URL:**
   - Your app will be available at: `https://your-app-name.onrender.com`
   - Example: `https://youtube-scheduler.onrender.com`

## Step 6: Verify Deployment

1. **Health Check:**
   - Visit: `https://your-app-name.onrender.com/health`
   - Should return: `{"status":"healthy"}`

2. **Access Application:**
   - Visit: `https://your-app-name.onrender.com`
   - You should see the login page

3. **Test OAuth:**
   - Sign up/Login
   - Try connecting a YouTube channel
   - Verify OAuth redirect works

## Troubleshooting

### Build Fails

**Error: "Module not found"**
- Check `requirements.txt` includes all dependencies
- Verify Python version (Render uses Python 3.11 by default)

**Error: "Command failed"**
- Check build command: `pip install -r requirements.txt`
- Check start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### App Crashes on Start

**Error: "Port already in use"**
- Make sure start command uses `$PORT` (not hardcoded port)
- Verify: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**Error: "Environment variable not found"**
- Check all required environment variables are set in Render dashboard
- Verify variable names match exactly (case-sensitive)

### OAuth Not Working

**Error: "redirect_uri_mismatch"**
- Verify `OAUTH_REDIRECT_URI` in Render matches Google Console exactly
- Check for trailing slashes (should NOT have one)
- Verify using `https://` not `http://`
- Make sure URL matches: `https://your-app-name.onrender.com/api/youtube/callback`

**Error: "access_denied"**
- Add your email as a test user in Google Cloud Console
- Go to "OAuth consent screen" → "Test users" → "ADD USERS"

### Storage Issues

**Data not persisting:**
- Render's free tier has ephemeral storage (data lost on restart)
- Consider upgrading to paid plan for persistent storage
- Or use external database (PostgreSQL, MongoDB, etc.)

## Important Notes

1. **Free Tier Limitations:**
   - Service spins down after 15 minutes of inactivity
   - First request after spin-down takes ~30 seconds
   - Storage is ephemeral (data lost on restart)
   - Upgrade to paid plan for always-on and persistent storage

2. **Security:**
   - Never commit `.env` file to Git
   - Use Render's environment variables for secrets
   - Generate strong `JWT_SECRET_KEY` (32+ characters)

3. **Performance:**
   - First deployment may take 5-10 minutes
   - Subsequent deployments are faster
   - Consider using Render's paid plans for better performance

4. **Monitoring:**
   - Check Render dashboard for logs
   - Monitor service health in dashboard
   - Set up alerts for service failures

## Next Steps After Deployment

1. **Test all features:**
   - User signup/login
   - YouTube channel connection
   - Video scheduling
   - Recent videos view
   - Failed videos view

2. **Set up custom domain (optional):**
   - In Render dashboard → "Settings" → "Custom Domain"
   - Add your domain
   - Update `OAUTH_REDIRECT_URI` and Google Console accordingly

3. **Enable auto-deploy:**
   - Render auto-deploys on push to main branch by default
   - Verify in "Settings" → "Auto-Deploy"

## Support

- Render Documentation: [render.com/docs](https://render.com/docs)
- Render Status: [status.render.com](https://status.render.com)
- Render Support: [render.com/support](https://render.com/support)

---

**Your app URL:** `https://your-app-name.onrender.com`  
**Health Check:** `https://your-app-name.onrender.com/health`  
**API Docs:** `https://your-app-name.onrender.com/docs` (FastAPI auto-generated)
