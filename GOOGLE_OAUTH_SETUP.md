# Google OAuth Setup Guide

## Fix: redirect_uri_mismatch Error

This error occurs when the redirect URI in Google Cloud Console doesn't match what your app is sending.

### Current App Configuration

Your app is configured to use:
```
http://localhost:8000/api/youtube/callback
```

### Steps to Fix

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Select your project (or create a new one)

2. **Navigate to OAuth 2.0 Credentials**
   - Go to: **APIs & Services** → **Credentials**
   - Find your OAuth 2.0 Client ID (or create one if you don't have it)
   - Click on the client ID to edit it

3. **Add Authorized Redirect URIs**
   In the "Authorized redirect URIs" section, add **EXACTLY** these URIs (case-sensitive, must match exactly):
   
   ```
   http://localhost:8000/api/youtube/callback
   http://127.0.0.1:8000/api/youtube/callback
   ```
   
   **Important Notes:**
   - Use `http://` (not `https://`) for localhost
   - Use `localhost` (not `127.0.0.1`) - or add both
   - Include the full path: `/api/youtube/callback`
   - No trailing slash
   - Case-sensitive

4. **Save the Changes**
   - Click "Save" at the bottom
   - Wait a few seconds for changes to propagate

5. **Verify Your .env File**
   Make sure your `.env` file has:
   ```
   OAUTH_REDIRECT_URI=http://localhost:8000/api/youtube/callback
   ```

6. **Restart Your Server**
   After making changes, restart your server:
   ```powershell
   python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

### Common Mistakes to Avoid

❌ **Wrong:**
- `https://localhost:8000/api/youtube/callback` (using https)
- `http://localhost:8000/` (missing path)
- `http://localhost:8000/api/youtube/callback/` (trailing slash)
- `http://127.0.0.1:8000/api/youtube/callback` (if you only added localhost)

✅ **Correct:**
- `http://localhost:8000/api/youtube/callback`
- `http://127.0.0.1:8000/api/youtube/callback` (add both to be safe)

### For Production/Deployment

When deploying to Render or another service, you'll need to:
1. Add your production URL to authorized redirect URIs:
   ```
   https://your-app-name.onrender.com/api/youtube/callback
   ```
2. Update your `.env` file on the server with:
   ```
   OAUTH_REDIRECT_URI=https://your-app-name.onrender.com/api/youtube/callback
   ```

### Testing

After making changes:
1. Wait 1-2 minutes for Google's changes to propagate
2. Clear your browser cache/cookies for Google
3. Try connecting YouTube again
