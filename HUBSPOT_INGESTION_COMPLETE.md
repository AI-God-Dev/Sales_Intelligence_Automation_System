# HubSpot Ingestion - Completion Summary

## ✅ Completed Steps

### 1. HubSpot Sync Function Redeployed with 1GB Memory
- **Status**: ✅ Complete
- **Memory**: Updated from 512MB to 1024MB (1GB)
- **Function URL**: `https://us-central1-maharani-sales-hub-11-2025.cloudfunctions.net/hubspot-sync`
- **Deployment Time**: November 22, 2025
- **Revision**: hubspot-sync-00002-jib

### 2. Deployment Configuration Updated
- **Main Deployment Script**: Updated `scripts/deploy_functions.sh` to use 1024MB memory for HubSpot
- **Status**: ✅ Complete

### 3. Function Status
- **State**: ACTIVE
- **Runtime**: Python 3.11
- **Service Account**: sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com
- **Timeout**: 540 seconds (9 minutes)
- **Memory**: 1024MB ✅

## ⚠️ Remaining Step

### HubSpot API Key in Secret Manager

The HubSpot sync function requires a valid HubSpot Private App access token to be stored in Secret Manager.

**Current Status:**
- Secret `hubspot-api-key` exists in Secret Manager
- Has version 1 created on 2025-11-17
- May need to verify/update the API key value

**To Complete Ingestion:**

1. **Get HubSpot Access Token**:
   - Log in to HubSpot
   - Go to Settings → Integrations → Private Apps
   - Create or open "Sales Intelligence System" app
   - Copy the access token (format: `pat-[region]-[random-string]`)
   - ⚠️ **Important**: Token is only shown once!

2. **Add/Update API Key in Secret Manager**:
   ```powershell
   # Option 1: Use the helper script
   .\scripts\add_hubspot_api_key.ps1
   
   # Option 2: Manual command
   $apiKey = Read-Host "Enter HubSpot API key"
   $tempFile = New-TemporaryFile
   $apiKey | Out-File -FilePath $tempFile -Encoding utf8 -NoNewline
   gcloud secrets versions add hubspot-api-key --data-file=$tempFile --project=maharani-sales-hub-11-2025
   Remove-Item $tempFile
   ```

3. **Verify Service Account Has Access**:
   ```powershell
   $serviceAccount = "sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com"
   gcloud secrets add-iam-policy-binding hubspot-api-key `
       --member="serviceAccount:$serviceAccount" `
       --role="roles/secretmanager.secretAccessor" `
       --project=maharani-sales-hub-11-2025
   ```

4. **Trigger HubSpot Ingestion**:
   ```powershell
   $token = gcloud auth print-access-token
   $url = "https://us-central1-maharani-sales-hub-11-2025.cloudfunctions.net/hubspot-sync"
   $headers = @{
       "Authorization" = "Bearer $token"
       "Content-Type" = "application/json"
   }
   Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body '{"sync_type":"full"}'
   ```

   Or use the test script:
   ```powershell
   .\scripts\test_ingestion.ps1
   ```

## 📋 Verification Steps

After adding the API key, verify ingestion:

1. **Check Function Logs**:
   ```powershell
   gcloud functions logs read hubspot-sync --region=us-central1 --project=maharani-sales-hub-11-2025 --limit=50
   ```

2. **Check BigQuery for Ingested Data**:
   ```powershell
   bq query --use_legacy_sql=false --project_id=maharani-sales-hub-11-2025 `
       "SELECT COUNT(*) as sequence_count FROM \`maharani-sales-hub-11-2025.sales_intelligence.hubspot_sequences\`"
   ```

3. **Check ETL Run History**:
   ```powershell
   bq query --use_legacy_sql=false --project_id=maharani-sales-hub-11-2025 `
       "SELECT * FROM \`maharani-sales-hub-11-2025.sales_intelligence.etl_runs\` WHERE source_system='hubspot' ORDER BY started_at DESC LIMIT 5"
   ```

## 📚 Documentation References

- **HubSpot Setup Guide**: `docs/HUBSPOT_SETUP.md`
- **Ingestion Triggers**: `docs/INGESTION_TRIGGERS.md`
- **Troubleshooting**: `docs/TROUBLESHOOTING.md`

## 🎯 Summary

**Completed:**
- ✅ Function redeployed with 1GB memory (fixes memory limit exceeded error)
- ✅ Deployment scripts updated
- ✅ Function is active and ready

**Remaining:**
- ⚠️ Add/verify HubSpot API key in Secret Manager
- ⚠️ Trigger ingestion after API key is added

Once the HubSpot API key is added to Secret Manager, the ingestion should work successfully with the increased memory allocation!





