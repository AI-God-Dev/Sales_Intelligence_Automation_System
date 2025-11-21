# Deploy Dialpad Sync Function - Client Guide

This script allows the client to deploy the Dialpad Sync Cloud Function with dynamic variables.

## Quick Start

### Windows (PowerShell)

```powershell
# Option 1: Run with prompts
.\scripts\deploy_dialpad_sync.ps1

# Option 2: Set environment variables first
$env:GCP_PROJECT_ID = "maharani-sales-hub-11-2025"
$env:GCP_REGION = "us-central1"
.\scripts\deploy_dialpad_sync.ps1

# Option 3: Pass parameters
.\scripts\deploy_dialpad_sync.ps1 -ProjectId "your-project-id" -Region "us-central1" -SourcePath "."
```

### Linux/Mac (Bash)

```bash
# Make script executable (first time only)
chmod +x scripts/deploy_dialpad_sync.sh

# Option 1: Run with prompts
./scripts/deploy_dialpad_sync.sh

# Option 2: Set environment variables first
export GCP_PROJECT_ID="maharani-sales-hub-11-2025"
export GCP_REGION="us-central1"
./scripts/deploy_dialpad_sync.sh

# Option 3: Pass parameters
./scripts/deploy_dialpad_sync.sh --project-id "your-project-id" --region "us-central1" --source "."
```

## Parameters

### PowerShell Parameters

- `-ProjectId`: GCP Project ID (default: from `$env:GCP_PROJECT_ID`)
- `-Region`: GCP Region (default: from `$env:GCP_REGION`, or `us-central1`)
- `-SourcePath`: Path to source code (default: `.`)
- `-FunctionName`: Function name (default: `dialpad-sync`)
- `-EntryPoint`: Entry point function (default: `dialpad_sync`)
- `-Runtime`: Runtime version (default: `python311`)

### Bash Parameters

- `--project-id`: GCP Project ID (default: from `$GCP_PROJECT_ID`)
- `--region`: GCP Region (default: from `$GCP_REGION`, or `us-central1`)
- `--source`: Path to source code (default: `.`)
- `--function-name`: Function name (default: `dialpad-sync`)
- `--entry-point`: Entry point function (default: `dialpad_sync`)
- `--runtime`: Runtime version (default: `python311`)

## Environment Variables

The script automatically uses these environment variables if set:

- `GCP_PROJECT_ID`: Your GCP Project ID
- `GCP_REGION`: Your GCP Region (default: `us-central1`)
- `SOURCE_PATH`: Path to source code (default: current directory)

## Prerequisites

1. **gcloud CLI installed and authenticated:**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Project cloned:**
   ```bash
   git clone https://github.com/AI-God-Dev/Sales_Intelligence_Automation_System.git
   cd Sales_Intelligence_Automation_System
   ```

3. **Required APIs enabled** (script will show errors if not):
   - Cloud Functions API
   - Cloud Build API
   - Cloud Run API

## Usage Examples

### Example 1: Default deployment (prompts for project ID)
```powershell
.\scripts\deploy_dialpad_sync.ps1
```

### Example 2: Using environment variables
```powershell
$env:GCP_PROJECT_ID = "maharani-sales-hub-11-2025"
$env:GCP_REGION = "us-central1"
.\scripts\deploy_dialpad_sync.ps1
```

### Example 3: Custom source path
```powershell
.\scripts\deploy_dialpad_sync.ps1 -SourcePath "C:\Projects\Sales_Intelligence"
```

### Example 4: All parameters specified
```powershell
.\scripts\deploy_dialpad_sync.ps1 `
    -ProjectId "maharani-sales-hub-11-2025" `
    -Region "us-central1" `
    -SourcePath "." `
    -FunctionName "dialpad-sync" `
    -Runtime "python311"
```

## What the Script Does

1. ✅ Checks gcloud authentication
2. ✅ Validates project ID and region
3. ✅ Verifies source path exists
4. ✅ Waits for any in-progress deployments to complete
5. ✅ Deploys the function with correct parameters
6. ✅ Shows function URL after successful deployment
7. ✅ Provides test command

## Troubleshooting

### Error: "unable to queue the operation" (409 error)
- **Cause**: Another deployment is in progress
- **Solution**: Wait a few minutes and try again. The script automatically waits for operations to complete.

### Error: "Project ID is required"
- **Solution**: Set `$env:GCP_PROJECT_ID` or pass `-ProjectId` parameter

### Error: "Source path does not exist"
- **Solution**: Ensure you're in the project root directory, or specify `-SourcePath` with correct path

### Error: "Not authenticated"
- **Solution**: Run `gcloud auth login` and authenticate

### Error: "Function already exists"
- **Solution**: This is normal - the script will update the existing function

## After Deployment

Test the deployed function:

```bash
gcloud functions call dialpad-sync \
  --region=us-central1 \
  --project=maharani-sales-hub-11-2025 \
  --data='{"user_id":"5286401882669056","sync_type":"full"}'
```

## Notes

- Deployment typically takes 5-10 minutes
- The script automatically handles 409 conflicts by waiting
- All parameters use `=` syntax (not `-` syntax) for gcloud commands
- Function is deployed with `--allow-unauthenticated` for easy testing

