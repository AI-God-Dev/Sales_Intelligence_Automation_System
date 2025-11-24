# HubSpot API Endpoint Fix

## Issue

HubSpot sync was failing with a 404 error:
```
404 Client Error: Not Found for url: https://api.hubapi.com/marketing/v3/sequences
```

## Root Cause

The code was using an incorrect API endpoint:
- **Wrong endpoint**: `/marketing/v3/sequences` (does not exist)
- **Correct endpoint**: `/automation/v4/workflows` (returns sequences/workflows)

## Solution

### 1. Updated API Endpoint
- Changed from `/marketing/v3/sequences` to `/automation/v4/workflows`
- This is the correct HubSpot API endpoint for retrieving sequences

### 2. Updated Response Parsing
- Automation API v4 returns workflows in format: `{"results": [...], "paging": {...}}`
- Updated parsing to handle the workflow response format
- Filter for sequence-type workflows only (type = "DRIP_DELAY" or "SEQUENCE")

### 3. Updated Field Mapping
- Automation API v4 uses different field names:
  - `id` or `workflowId` (instead of `sequenceId`)
  - `name` or `workflowName` (instead of `sequenceName`)
  - `enabled` or `active` (for status)
  - `enrolledContacts` (for enrollment count)

## Code Changes

### `cloud_functions/hubspot_sync/main.py`

1. **Updated endpoint URL**:
   ```python
   # Before:
   url = "https://api.hubapi.com/marketing/v3/sequences"
   
   # After:
   url = "https://api.hubapi.com/automation/v4/workflows"
   ```

2. **Updated response parsing**:
   - Handles Automation API v4 response format
   - Filters for sequence-type workflows

3. **Updated field mapping**:
   - Maps workflow fields to sequence fields correctly
   - Handles multiple possible field names

## API Key Confirmation

✅ **Confirmed**: The code correctly pulls from `hubspot-api-key` secret in Secret Manager (see `config/config.py` line 122).

## Testing

After deployment, verify:
1. Sync completes successfully without 404 errors
2. Sequences are retrieved from HubSpot
3. Data is correctly inserted into BigQuery `hubspot_sequences` table

## Deployment

Deploy the updated function:
```powershell
gcloud functions deploy hubspot-sync --gen2 --runtime=python311 --region=us-central1 --source=. --entry-point=hubspot_sync --trigger-http --service-account=sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com --memory=1024MB --timeout=540s --max-instances=10 --min-instances=0 --set-env-vars=GCP_PROJECT_ID=maharani-sales-hub-11-2025,GCP_REGION=us-central1 --project=maharani-sales-hub-11-2025
```

## Status

✅ **Fix implemented and ready for deployment**



