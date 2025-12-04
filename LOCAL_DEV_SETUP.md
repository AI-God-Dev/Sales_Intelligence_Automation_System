# Local Development Setup

## Overview
For local development, use your own Google account credentials (via `gcloud auth login`). You already have `run.invoker` permission on the Cloud Run functions, so no service account impersonation is needed.

## Setup Steps

### Step 1: Authenticate with Your Google Account

```powershell
# Login with your Google account
gcloud auth login

# Set the project
gcloud config set project maharani-sales-hub-11-2025

# Set Application Default Credentials
gcloud auth application-default login
```

### Step 2: Verify Authentication

```powershell
# Check your active account
gcloud auth list

# Test Application Default Credentials
gcloud auth application-default print-access-token
```

### Step 3: Run the Web App

```powershell
cd web_app
streamlit run app.py
```

## How It Works

1. **Local Development:**
   - Your user account (from `gcloud auth login`) is used via Application Default Credentials
   - The code gets an ID token directly using `id_token.fetch_id_token()`
   - Your account already has `run.invoker` permission on Cloud Run services
   - No service account impersonation needed

2. **Production:**
   - The web app runs as `web-app-runtime-sa` (automatically via Cloud Run)
   - `web-app-runtime-sa` has `run.invoker` permission
   - No code changes needed - it works automatically

## Authentication Flow

```
Local Dev:
Your Google Account → Application Default Credentials → Get ID Token → Call Cloud Run

Production:
web-app-runtime-sa → Application Default Credentials → Get ID Token → Call Cloud Run
```

## Troubleshooting

### Error: "Could not get default credentials"
- Run: `gcloud auth application-default login`
- Verify: `gcloud auth list` shows your account

### Error: "Identity token generation failed"
- Ensure you're logged in: `gcloud auth login`
- Verify project is set: `gcloud config get-value project`
- Check you have `run.invoker` permission (ask Anand if needed)

### Error: "Permission denied" (403)
- Verify you have `run.invoker` permission on the Cloud Run service
- Ask Anand to verify your permissions if needed

## Security Notes

- **No service account key files** - Uses Application Default Credentials
- **No impersonation needed** - Your account has direct `run.invoker` permission
- **Auditable** - All calls are logged with your user identity
