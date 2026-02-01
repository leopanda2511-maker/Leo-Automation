# Fix: OAuth 403 access_denied Error

## Problem
Your Google OAuth app is in "Testing" mode, which means only approved test users can access it.

## Solution: Add Test Users

### Step 1: Go to OAuth Consent Screen
1. Visit: https://console.cloud.google.com/
2. Select your project
3. Navigate to: **APIs & Services** → **OAuth consent screen**

### Step 2: Add Test Users
1. Scroll down to the **"Test users"** section
2. Click **"+ ADD USERS"**
3. Add your email address: `Raj1225288@gmail.com`
4. Click **"ADD"**
5. You can add multiple test users if needed

### Step 3: Save and Try Again
1. The changes are saved automatically
2. Wait a few seconds
3. Try connecting YouTube again in your app

## Alternative Solutions

### Option 1: Change to Internal (Google Workspace Only)
If you're using a Google Workspace account:
1. In OAuth consent screen, change **User Type** to **"Internal"**
2. This allows all users in your organization automatically
3. Only works for Google Workspace accounts

### Option 2: Publish the App (For Production)
If you want anyone to use your app:
1. Complete the OAuth consent screen setup
2. Click **"PUBLISH APP"**
3. Note: This requires verification for sensitive scopes (YouTube, Drive)
4. Verification can take several days/weeks

## Quick Fix (Recommended for Development)
**Just add your email as a test user** - this is the fastest solution for development/testing.

## Current Status
- Your app is in **Testing** mode
- You need to add: `Raj1225288@gmail.com` as a test user
- After adding, you'll be able to connect YouTube
