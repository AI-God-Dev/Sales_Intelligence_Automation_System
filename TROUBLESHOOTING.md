# Troubleshooting Guide - Sales Intelligence Automation System

This guide provides solutions to common deployment and runtime issues.

---

## Table of Contents

1. [Deployment Issues](#deployment-issues)
2. [IAM & Permission Errors](#iam--permission-errors)
3. [Secret Manager Issues](#secret-manager-issues)
4. [Cloud Functions Errors](#cloud-functions-errors)
5. [BigQuery Issues](#bigquery-issues)
6. [Entry Point Errors](#entry-point-errors)
7. [Import Errors](#import-errors)
8. [API Integration Issues](#api-integration-issues)
9. [Performance Issues](#performance-issues)

---

## Deployment Issues

### Error: "Permission 'iam.serviceaccounts.actAs' denied"

**Cause**: Your user account doesn't have permission to use the service account.

**Solution**:
```powershell
$PROJECT_ID = "YOUR_PROJECT_ID"
$SERVICE_ACCOUNT = "sales-intelligence-sa@${PROJECT_ID}.iam.gserviceaccount.com"
$YOUR_EMAIL = "your-email@example.com"

gcloud iam service-accounts add-iam-policy-binding $SERVICE_ACCOUNT `
  --member="user:$YOUR_EMAIL" `
  --role="roles/iam.serviceAccountUser" `
  --project=$PROJECT_ID
```

---

### Error: "API 'xxx.googleapis.com' is not enabled"

**Cause**: Required GCP API is not enabled for your project.

**Solution**:
```powershell
$PROJECT_ID = "YOUR_PROJECT_ID"
gcloud services enable API_NAME --project=$PROJECT_ID

# Enable all required APIs at once:
$apis = @(
    "cloudfunctions.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "bigquery.googleapis.com",
    "secretmanager.googleapis.com",
    "aiplatform.googleapis.com"
)
foreach ($api in $apis) {
    gcloud services enable $api --project=$PROJECT_ID
}
```

---

### Error: "Source directory does not have file [main.py]"

**Cause**: Deployment script is not running from project root, or entry point is incorrect.

**Solution**:
1. Ensure you're in the project root directory:
   ```powershell
   cd C:\Users\Administrator\Desktop\Projects\SALES
   ```

2. Verify `main.py` or `config\config.py` exists:
   ```powershell
   Test-Path "main.py"
   Test-Path "config\config.py"
   ```

3. Check entry point format in deployment script:
   - **Gen2 requires root-level exports.** Use `--entry-point=gmail_sync` (or the short name) that is imported in root `main.py`.
   - Do **not** use module paths like `cloud_functions.gmail_sync.main.gmail_sync` for Gen2.

---

### Error: "Function deployment failed: Build failed"

**Cause**: Build errors during Cloud Function deployment (missing dependencies, syntax errors, etc.).

**Solution**:
1. Check build logs:
   ```powershell
   gcloud builds list --project=$PROJECT_ID --limit=5
   gcloud builds log BUILD_ID --project=$PROJECT_ID
   ```

2. Verify `requirements.txt` files exist and are correct:
   ```powershell
   Get-Content cloud_functions\gmail_sync\requirements.txt
   ```

3. Test locally first:
   ```powershell
   pip install -r cloud_functions\gmail_sync\requirements.txt
   python -m cloud_functions.gmail_sync.main
   ```

---

## IAM & Permission Errors

### Error: "Permission denied on resource"

**Cause**: Service account or user account lacks required IAM role.

**Solution**:
```powershell
$PROJECT_ID = "YOUR_PROJECT_ID"
$SERVICE_ACCOUNT = "sales-intelligence-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant required roles
$roles = @(
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
    "roles/aiplatform.user",
    "roles/secretmanager.secretAccessor",
    "roles/cloudfunctions.invoker",
    "roles/run.invoker"
)

foreach ($role in $roles) {
    gcloud projects add-iam-policy-binding $PROJECT_ID `
      --member="serviceAccount:$SERVICE_ACCOUNT" `
      --role=$role
}
```

---

### Error: "The caller does not have permission"

**Cause**: Your user account lacks deployment permissions.

**Solution**:
```powershell
$PROJECT_ID = "YOUR_PROJECT_ID"
$YOUR_EMAIL = "your-email@example.com"

$userRoles = @(
    "roles/cloudfunctions.admin",
    "roles/run.admin",
    "roles/secretmanager.admin",
    "roles/bigquery.admin"
)

foreach ($role in $userRoles) {
    gcloud projects add-iam-policy-binding $PROJECT_ID `
      --member="user:$YOUR_EMAIL" `
      --role=$role
}
```

---

## Secret Manager Issues

### Error: "Secret 'xxx' not found in Secret Manager"

**Cause**: Secret doesn't exist or has wrong name.

**Solution**:
1. List all secrets:
   ```powershell
   gcloud secrets list --project=$PROJECT_ID
   ```

2. Create missing secret:
   ```powershell
   gcloud secrets create SECRET_NAME --project=$PROJECT_ID
   echo -n "SECRET_VALUE" | gcloud secrets versions add SECRET_NAME --data-file=- --project=$PROJECT_ID
   ```

3. Verify secret exists:
   ```powershell
   gcloud secrets describe SECRET_NAME --project=$PROJECT_ID
   ```

---

### Error: "Permission denied on secret"

**Cause**: Service account doesn't have access to secret.

**Solution**:
```powershell
$PROJECT_ID = "YOUR_PROJECT_ID"
$SERVICE_ACCOUNT = "sales-intelligence-sa@${PROJECT_ID}.iam.gserviceaccount.com"
$SECRET_NAME = "salesforce-client-id"

gcloud secrets add-iam-policy-binding $SECRET_NAME `
  --member="serviceAccount:$SERVICE_ACCOUNT" `
  --role="roles/secretmanager.secretAccessor" `
  --project=$PROJECT_ID
```

---

### Error: "Failed to retrieve secret 'xxx'"

**Cause**: Secret exists but has no versions, or service account lacks access.

**Solution**:
1. Check secret versions:
   ```powershell
   gcloud secrets versions list SECRET_NAME --project=$PROJECT_ID
   ```

2. Add a version if missing:
   ```powershell
   echo -n "SECRET_VALUE" | gcloud secrets versions add SECRET_NAME --data-file=- --project=$PROJECT_ID
   ```

3. Verify service account access:
   ```powershell
   gcloud secrets get-iam-policy SECRET_NAME --project=$PROJECT_ID
   ```

---

## Cloud Functions Errors

### Error: "Function execution failed: Memory limit exceeded"

**Cause**: Function requires more memory than allocated.

**Solution**:
1. Increase memory allocation in deployment:
   ```powershell
   # For account-scoring, use 2048MB minimum
   gcloud functions deploy account-scoring `
     --gen2 `
     --memory=2048MB `
     --region=us-central1 `
     --project=$PROJECT_ID
   ```

2. Check function logs for memory usage:
   ```powershell
   gcloud functions logs read FUNCTION_NAME --gen2 --region=us-central1 --limit=50
   ```

---

### Error: "Function execution timed out"

**Cause**: Function takes longer than timeout limit.

**Solution**:
1. Increase timeout:
   ```powershell
   gcloud functions deploy FUNCTION_NAME `
     --gen2 `
     --timeout=540s `
     --region=us-central1 `
     --project=$PROJECT_ID
   ```

2. Optimize function code (reduce batch sizes, add pagination, etc.)

---

### Error: "Entry point 'xxx' not found"

**Cause**: Entry point doesn't match actual function name or module path.

**Solution**:
1. Verify function exists in code:
   ```powershell
   # Check gmail_sync function
   Select-String -Path "cloud_functions\gmail_sync\main.py" -Pattern "@functions_framework"
   ```

2. Use correct entry point format:
   - For Gen2 deployments use root exports from `main.py`, e.g., `--entry-point=gmail_sync`
   - For functions in `intelligence/`: `intelligence.scoring.main.account_scoring_job`

3. Redeploy with correct entry point:
   ```powershell
   gcloud functions deploy FUNCTION_NAME `
     --gen2 `
     --entry-point=correct.module.path.function_name `
     --region=us-central1 `
     --project=$PROJECT_ID
   ```

---

### Error: "Function not found" or "404 Not Found"

**Cause**: Function doesn't exist or wrong region/project specified.

**Solution**:
1. List all functions:
   ```powershell
   gcloud functions list --gen2 --region=us-central1 --project=$PROJECT_ID
   ```

2. Verify function exists:
   ```powershell
   gcloud functions describe FUNCTION_NAME --gen2 --region=us-central1 --project=$PROJECT_ID
   ```

3. Check region matches deployment region

---

## BigQuery Issues

### Error: "Table 'xxx' not found"

**Cause**: Table doesn't exist in BigQuery dataset.

**Solution**:
1. Verify tables exist:
   ```powershell
   bq ls --project_id=$PROJECT_ID sales_intelligence
   ```

2. Create missing tables:
   ```powershell
   # Update project ID in SQL file first
   bq query --use_legacy_sql=false --project_id=$PROJECT_ID < bigquery\schemas\create_tables.sql
   ```

3. Check dataset name matches configuration:
   ```powershell
   # In config/config.py, verify:
   # bigquery_dataset: str = "sales_intelligence"
   ```

---

### Error: "Dataset 'xxx' not found"

**Cause**: BigQuery dataset doesn't exist.

**Solution**:
```powershell
$PROJECT_ID = "YOUR_PROJECT_ID"
$DATASET_ID = "sales_intelligence"
$REGION = "us-central1"

bq mk --dataset `
  --location=$REGION `
  --description="Sales Intelligence data warehouse" `
  --project_id=$PROJECT_ID `
  $DATASET_ID
```

---

### Error: "Access Denied: BigQuery BigQuery: Permission denied"

**Cause**: Service account lacks BigQuery permissions.

**Solution**:
```powershell
$PROJECT_ID = "YOUR_PROJECT_ID"
$SERVICE_ACCOUNT = "sales-intelligence-sa@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:$SERVICE_ACCOUNT" `
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:$SERVICE_ACCOUNT" `
  --role="roles/bigquery.jobUser"
```

---

## Entry Point Errors

### Error: "Could not load the function entry point"

**Cause**: Entry point path is incorrect or function doesn't exist.

**Solution**:
1. Verify function decorator:
   ```python
   # In main.py, ensure function has @functions_framework.http decorator
   @functions_framework.http
   def gmail_sync(request):
       ...
   ```

2. Check entry point format:
   - ✅ Correct for Gen2: `--entry-point=gmail_sync` (root `main.py`)
   - ❌ Wrong: `gmail_sync`
   - ❌ Wrong: `main.gmail_sync`

3. Verify Python path includes project root (functions handle this automatically)

---

### Error: "ModuleNotFoundError: No module named 'xxx'"

**Cause**: Python can't find required modules.

**Solution**:
1. Verify project structure:
   ```
   SALES/
   ├── cloud_functions/
   ├── intelligence/
   ├── utils/
   ├── config/
   └── main.py
   ```

2. Check imports in function code:
   ```python
   # Should use absolute imports from project root
   from utils.bigquery_client import BigQueryClient
   from config.config import settings
   ```

3. Verify `requirements.txt` includes all dependencies

---

## Import Errors

### Error: "ImportError: cannot import name 'xxx'"

**Cause**: Module import path is incorrect or module doesn't exist.

**Solution**:
1. Verify module exists:
   ```powershell
   Test-Path "utils\bigquery_client.py"
   Test-Path "config\config.py"
   ```

2. Check import statements:
   ```python
   # Correct imports
   from utils.bigquery_client import BigQueryClient
   from config.config import settings
   
   # NOT:
   # from bigquery_client import BigQueryClient  # Wrong
   ```

3. Verify `__init__.py` files exist:
   ```powershell
   Test-Path "utils\__init__.py"
   Test-Path "config\__init__.py"
   ```

---

## API Integration Issues

### Error: "Salesforce authentication failed: INVALID_LOGIN"

**Cause**: Invalid Salesforce credentials or security token.

**Solution**:
1. Verify credentials in Secret Manager:
   ```powershell
   gcloud secrets versions access latest --secret=salesforce-username --project=$PROJECT_ID
   ```

2. For sandbox, ensure:
   - Username ends with `.sandbox`
   - Domain is set to `test` (not `login`)
   - Security token is correct (reset in Salesforce if needed)

3. Check Salesforce domain setting:
   ```python
   # In config/config.py
   salesforce_domain: str = "test"  # For sandbox
   # salesforce_domain: str = "login"  # For production
   ```

---

### Error: "Dialpad API error: 401 Unauthorized"

**Cause**: Invalid or expired Dialpad API key.

**Solution**:
1. Verify API key in Secret Manager:
   ```powershell
   gcloud secrets versions access latest --secret=dialpad-api-key --project=$PROJECT_ID
   ```

2. Regenerate API key in Dialpad admin console

3. Update secret:
   ```powershell
   echo -n "NEW_API_KEY" | gcloud secrets versions add dialpad-api-key --data-file=- --project=$PROJECT_ID
   ```

---

### Error: "HubSpot API error: 401 Unauthorized"

**Cause**: Invalid HubSpot API key or wrong format.

**Solution**:
1. Verify API key format (should be Private App token):
   - Format: `pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
   - NOT: OAuth access token

2. Create new Private App in HubSpot:
   - Go to Settings > Integrations > Private Apps
   - Create new app with required scopes
   - Copy access token

3. Update secret:
   ```powershell
   echo -n "pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" | gcloud secrets versions add hubspot-api-key --data-file=- --project=$PROJECT_ID
   ```

---

### Error: "Gmail API error: 403 Forbidden"

**Cause**: Domain-wide delegation not configured or OAuth scopes incorrect.

**Solution**:
1. Verify domain-wide delegation is enabled:
   - Go to Service Accounts in GCP Console
   - Enable "Domain-wide Delegation"
   - Note the Client ID

2. Configure in Google Workspace Admin:
   - Go to Security > API Controls > Domain-wide Delegation
   - Add API client with the Client ID
   - OAuth scopes: `https://www.googleapis.com/auth/gmail.readonly`

3. Verify service account has Gmail API access

---

## Performance Issues

### Issue: "Function execution is slow"

**Solution**:
1. Increase memory allocation (more memory = faster execution)
2. Optimize batch sizes in code
3. Use incremental sync instead of full sync
4. Check BigQuery query performance

---

### Issue: "BigQuery queries are slow"

**Solution**:
1. Verify tables are clustered:
   ```sql
   -- Tables should be clustered by frequently queried columns
   CLUSTER BY mailbox_email, from_email
   ```

2. Use partitioned tables (already configured for date-based tables)

3. Optimize queries (add WHERE clauses, limit results, etc.)

---

## Getting Help

If you encounter an issue not covered here:

1. **Check Function Logs**:
   ```powershell
   gcloud functions logs read FUNCTION_NAME --gen2 --region=us-central1 --limit=100
   ```

2. **Check Build Logs**:
   ```powershell
   gcloud builds list --project=$PROJECT_ID --limit=5
   gcloud builds log BUILD_ID --project=$PROJECT_ID
   ```

3. **Verify Configuration**:
   - Check environment variables
   - Verify IAM permissions
   - Confirm secrets exist and are accessible

4. **Review Documentation**:
   - [README_DEPLOYMENT.md](README_DEPLOYMENT.md)
   - [CLIENT_DEPLOYMENT_GUIDE.md](CLIENT_DEPLOYMENT_GUIDE.md)

---

**Last Updated**: 2025-01-XX  
**Version**: 1.0
