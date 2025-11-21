# How to View Cloud Function Logs

## For Gen2 Cloud Functions (Cloud Run)

Gen2 Cloud Functions run on Cloud Run, so use Cloud Run logging commands.

### Option 1: View Recent Logs (Read)

```bash
# View recent logs for Gmail sync
gcloud functions logs read gmail-sync \
    --region=us-central1 \
    --project=maharani-sales-hub-11-2025 \
    --limit=50

# Or use Cloud Run logging (more detailed)
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=gmail-sync" \
    --project=maharani-sales-hub-11-2025 \
    --limit=50 \
    --format="table(timestamp,severity,textPayload)"
```

### Option 2: Real-Time Log Streaming (Tail)

**Linux/Mac:**
```bash
bash scripts/view_gmail_sync_logs.sh
```

**Windows/PowerShell:**
```powershell
.\scripts\view_gmail_sync_logs.ps1
```

**Or manually:**
```bash
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=gmail-sync" \
    --project=maharani-sales-hub-11-2025 \
    --format="table(timestamp,severity,textPayload)"
```

### Option 3: GCP Console (Web UI)

1. Go to: https://console.cloud.google.com/logs/query?project=maharani-sales-hub-11-2025
2. Use this filter:
   ```
   resource.type="cloud_run_revision"
   resource.labels.service_name="gmail-sync"
   ```
3. Click "Run Query"
4. Logs appear in real-time

### Option 4: View All Function Logs

```bash
# List all functions and their recent logs
gcloud functions list --region=us-central1 --project=maharani-sales-hub-11-2025

# View logs for each function:
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=gmail-sync" \
    --project=maharani-sales-hub-11-2025 \
    --limit=10

gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=salesforce-sync" \
    --project=maharani-sales-hub-11-2025 \
    --limit=10
```

### Filter Logs by Severity

```bash
# Only errors
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=gmail-sync AND severity>=ERROR" \
    --project=maharani-sales-hub-11-2025 \
    --limit=50

# Only info/warnings
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=gmail-sync AND severity>=INFO" \
    --project=maharani-sales-hub-11-2025 \
    --limit=50
```

## Notes

- **Gen2 Functions** = Cloud Run, so use `cloud_run_revision` resource type
- **Gen1 Functions** = Cloud Functions, use `cloud_function` resource type
- **Real-time streaming** = Use `gcloud logging tail` (not `gcloud functions logs tail`)
- **Logs persist** for 30 days by default

