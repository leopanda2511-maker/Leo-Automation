# Render Deployment Checklist

Use this checklist before deploying to Render.

## Pre-Deployment Checklist

### Code Preparation
- [ ] All code committed to GitHub
- [ ] `requirements.txt` is up to date
- [ ] `render.yaml` exists and is configured
- [ ] `.gitignore` includes `storage/` and `*.env`
- [ ] No hardcoded secrets in code
- [ ] All environment variables use settings from `.env`

### Google Cloud Console Setup
- [ ] Project created/selected in Google Cloud Console
- [ ] YouTube Data API v3 enabled
- [ ] Google Drive API enabled
- [ ] OAuth 2.0 credentials created (Web application)
- [ ] Client ID and Client Secret copied
- [ ] Test user added (if app is in testing mode)

### Render Account Setup
- [ ] Render account created at [render.com](https://render.com)
- [ ] GitHub account connected to Render
- [ ] Repository access granted to Render

## Deployment Steps

### Step 1: Create Web Service
- [ ] Go to Render Dashboard → "New +" → "Web Service"
- [ ] Connect GitHub repository
- [ ] Select repository: `Leo Automation`
- [ ] Name: `youtube-scheduler` (or your choice)
- [ ] Environment: `Python 3`
- [ ] Region: Selected
- [ ] Branch: `main`
- [ ] Build Command: `pip install -r requirements.txt`
- [ ] Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] Click "Create Web Service"

### Step 2: Set Environment Variables
- [ ] `GOOGLE_CLIENT_ID` - Your Google OAuth Client ID
- [ ] `GOOGLE_CLIENT_SECRET` - Your Google OAuth Client Secret
- [ ] `OAUTH_REDIRECT_URI` - `https://your-app-name.onrender.com/api/youtube/callback`
- [ ] `JWT_SECRET_KEY` - Generated secure random string (32+ chars)
- [ ] `JWT_ALGORITHM` - `HS256`
- [ ] `HOST` - `0.0.0.0`

### Step 3: Update Google Cloud Console
- [ ] Go to Google Cloud Console → Credentials
- [ ] Edit OAuth 2.0 Client ID
- [ ] Add Authorized Redirect URI: `https://your-app-name.onrender.com/api/youtube/callback`
- [ ] Save changes

### Step 4: Deploy
- [ ] Click "Manual Deploy" or push to main branch
- [ ] Monitor build logs
- [ ] Wait for "Your service is live" message
- [ ] Note your app URL: `https://your-app-name.onrender.com`

### Step 5: Verify Deployment
- [ ] Health check: `https://your-app-name.onrender.com/health` returns `{"status":"healthy"}`
- [ ] Homepage loads: `https://your-app-name.onrender.com`
- [ ] Can sign up/login
- [ ] Can connect YouTube channel
- [ ] OAuth redirect works correctly

## Post-Deployment

### Testing
- [ ] Test user signup
- [ ] Test user login
- [ ] Test YouTube channel connection
- [ ] Test video scheduling
- [ ] Test recent videos view
- [ ] Test failed videos view
- [ ] Test refresh buttons

### Configuration
- [ ] Auto-deploy enabled (default)
- [ ] Custom domain configured (optional)
- [ ] Monitoring/alerts set up (optional)

## Important Reminders

⚠️ **Before deploying:**
- Replace `your-app-name` with your actual Render service name in:
  - `OAUTH_REDIRECT_URI` environment variable
  - Google Cloud Console redirect URI

⚠️ **Free Tier Limitations:**
- Service spins down after 15 min inactivity
- First request after spin-down takes ~30 seconds
- Storage is ephemeral (data lost on restart)
- Consider paid plan for production use

⚠️ **Security:**
- Never commit `.env` file
- Use strong `JWT_SECRET_KEY` (32+ characters)
- Keep `GOOGLE_CLIENT_SECRET` secure

## Quick Commands

**Generate JWT Secret Key:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Test locally before deploying:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Check health endpoint:**
```bash
curl https://your-app-name.onrender.com/health
```

---

**Ready to deploy?** Follow the detailed guide in `RENDER_DEPLOYMENT.md`
