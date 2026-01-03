# Troubleshooting Guide

Solutions for common issues with the Sales Intelligence Automation System.

## Quick Diagnostics

```bash
# Check function status
gcloud functions list --gen2 --region=us-central1

# View recent errors
gcloud logging read "severity>=ERROR" --limit=20

# Check ETL status
bq query --use_legacy_sql=false "
SELECT source_system, status, error_message, started_at
FROM \`PROJECT_ID.sales_intelligence.etl_runs\`
WHERE DATE(started_at) = CURRENT_DATE()
ORDER BY started_at DESC
"
```

---

## Deployment Issues

### Error: "Permission denied on resource"

**Cause**: Service account missing required IAM role.

**Solution**:
```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:sales-intelligence-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"
```

### Error: "API not enabled"

**Cause**: Required GCP API not enabled.

**Solution**:
```bash
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

### Error: "Source directory does not have file [main.py]"

**Cause**: Deployment not running from project root.

**Solution**:
```bash
cd /path/to/Sales_Intelligence_Automation_System
gcloud functions deploy gmail-sync --source=.
```

---

## Authentication Issues

### Error: "Secret not found"

**Cause**: Secret doesn't exist or wrong name.

**Solution**:
```bash
# List secrets
gcloud secrets list

# Create if missing
gcloud secrets create salesforce-client-id

# Add value
echo -n "YOUR_VALUE" | gcloud secrets versions add salesforce-client-id --data-file=-
```

### Error: "Permission denied on secret"

**Cause**: Service account can't access secret.

**Solution**:
```bash
gcloud secrets add-iam-policy-binding salesforce-client-id \
  --member="serviceAccount:sales-intelligence-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Error: "Salesforce authentication failed"

**Cause**: Invalid credentials or expired token.

**Solution**:
1. Verify credentials in Secret Manager
2. For sandbox, set `SALESFORCE_DOMAIN=test`
3. Check security token is appended to password
4. Regenerate refresh token if using OAuth

---

## AI/Model Issues

### Error: "404 Publisher Model not found"

**Cause**: Invalid model name or model not available.

**Solution**:
```bash
# Set correct model name
export LLM_MODEL=gemini-2.5-pro

# Verify in function deployment
gcloud functions deploy account-scoring \
  --set-env-vars="LLM_MODEL=gemini-2.5-pro"
```

### Error: "Permission denied accessing Vertex AI"

**Cause**: Service account missing AI Platform role.

**Solution**:
```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:sales-intelligence-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

### Error: "Embeddings not generated"

**Cause**: Embedding function not running or failing.

**Solution**:
```bash
# Check embedding status
bq query --use_legacy_sql=false "
SELECT COUNT(*) as total, COUNTIF(embedding IS NULL) as missing
FROM \`PROJECT_ID.sales_intelligence.gmail_messages\`
"

# Trigger manually
gcloud functions call generate-embeddings --gen2 --region=us-central1
```

---

## BigQuery Issues

### Error: "Table not found"

**Cause**: Table doesn't exist in dataset.

**Solution**:
```bash
# List tables
bq ls $PROJECT_ID:sales_intelligence

# Create tables
bq query --use_legacy_sql=false < bigquery/schemas/create_tables.sql
```

### Error: "Access Denied: BigQuery"

**Cause**: Service account missing BigQuery permissions.

**Solution**:
```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:sales-intelligence-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:sales-intelligence-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"
```

---

## Cloud Function Issues

### Error: "Function execution timed out"

**Cause**: Function taking too long.

**Solution**:
```bash
# Increase timeout
gcloud functions deploy account-scoring \
  --timeout=540s \
  --memory=2048MB
```

### Error: "Memory limit exceeded"

**Cause**: Function needs more memory.

**Solution**:
```bash
gcloud functions deploy account-scoring \
  --memory=2048MB
```

### Error: "Entry point not found"

**Cause**: Entry point doesn't match function name.

**Solution**:
Verify entry point in deployment matches function decorator:
```python
# In main.py
@functions_framework.http
def gmail_sync(request):  # This must match --entry-point=gmail_sync
    ...
```

---

## Web Application Issues

### Error: "BigQuery client not available"

**Cause**: Application Default Credentials not set.

**Solution**:
```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project $PROJECT_ID
```

### Error: "Function not responding"

**Cause**: Cloud Run service cold start or error.

**Solution**:
1. Check Cloud Run logs
2. Verify environment variables are set
3. Restart service if needed

### Error: "Permission denied calling function"

**Cause**: User/service account missing invoker role.

**Solution**:
```bash
gcloud run services add-iam-policy-binding sales-intelligence-web \
  --region=us-central1 \
  --member="user:your-email@example.com" \
  --role="roles/run.invoker"
```

---

## Data Quality Issues

### Low Entity Resolution Match Rate

**Symptoms**: Many unmatched emails

**Diagnosis**:
```sql
SELECT 
  COUNTIF(sf_contact_id IS NOT NULL) * 100.0 / COUNT(*) as match_rate
FROM `PROJECT_ID.sales_intelligence.gmail_participants`
```

**Solutions**:
1. Re-run entity resolution
2. Check email normalization
3. Verify Salesforce data is synced
4. Add manual mappings for known emails

### Stale Data

**Symptoms**: Data not updating

**Diagnosis**:
```sql
SELECT MAX(sent_at) as latest_email
FROM `PROJECT_ID.sales_intelligence.gmail_messages`
```

**Solutions**:
1. Check Cloud Scheduler jobs are running
2. Verify function credentials are valid
3. Manually trigger sync

---

## Common Commands

```bash
# View function logs
gcloud functions logs read gmail-sync --gen2 --region=us-central1 --limit=50

# Test function
gcloud functions call gmail-sync --gen2 --region=us-central1

# Check scheduler jobs
gcloud scheduler jobs list --location=us-central1

# Verify secrets
gcloud secrets versions access latest --secret=salesforce-client-id
```

---

## Getting Help

1. Check Cloud Logging for detailed errors
2. Review function logs
3. Verify IAM permissions
4. Check BigQuery for data issues

See [Operations Runbook](RUNBOOK.md) for operational procedures.

