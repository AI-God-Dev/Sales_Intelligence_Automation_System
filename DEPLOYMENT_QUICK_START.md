# Deployment Quick Start Guide

## 🚀 Fastest Path to Deployment

This guide provides the absolute fastest way to deploy the Sales Intelligence System. For detailed instructions, see [README_DEPLOYMENT.md](README_DEPLOYMENT.md).

---

## Prerequisites Checklist

- [ ] Google Cloud SDK installed (`gcloud --version`)
- [ ] Authenticated with GCP (`gcloud auth login`)
- [ ] GCP project created with billing enabled
- [ ] Required API credentials obtained (Salesforce, Dialpad, HubSpot, Gmail OAuth)

---

## 4-Step Deployment

### Step 1: Set Environment Variables

```powershell
# Windows PowerShell
$env:GCP_PROJECT_ID = "your-project-id"
$env:GCP_REGION = "us-central1"
$env:GCP_USER_EMAIL = "your-email@example.com"
$env:GCP_SERVICE_ACCOUNT_NAME = "sales-intelligence-sa"
```

```bash
# Linux/Mac
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"
export GCP_USER_EMAIL="your-email@example.com"
export GCP_SERVICE_ACCOUNT_NAME="sales-intelligence-sa"
```

---

### Step 2: Setup Service Account & APIs

```powershell
# PowerShell
.\scripts\setup_service_account.ps1
```

```bash
# Bash
chmod +x scripts/setup_service_account.sh
./scripts/setup_service_account.sh
```

**What this does:**
- Creates service account
- Grants all required IAM roles
- Enables all required GCP APIs

---

### Step 3: Create BigQuery Dataset & Tables

```powershell
# PowerShell
.\scripts\create_bigquery_datasets.ps1
```

```bash
# Bash
chmod +x scripts/create_bigquery_datasets.sh
./scripts/create_bigquery_datasets.sh
```

**What this does:**
- Creates BigQuery dataset (`sales_intelligence`)
- Creates all required tables

**⚠️ Important**: Update project ID in `bigquery/schemas/create_tables.sql` before running if needed.

---

### Step 4: Configure Secrets

```powershell
$PROJECT_ID = $env:GCP_PROJECT_ID

# Create secrets
gcloud secrets create salesforce-client-id --project=$PROJECT_ID
gcloud secrets create salesforce-client-secret --project=$PROJECT_ID
gcloud secrets create salesforce-username --project=$PROJECT_ID
gcloud secrets create salesforce-password --project=$PROJECT_ID
gcloud secrets create salesforce-security-token --project=$PROJECT_ID
gcloud secrets create dialpad-api-key --project=$PROJECT_ID
gcloud secrets create hubspot-api-key --project=$PROJECT_ID

# Add secret values (replace with your actual values)
echo -n "YOUR_VALUE" | gcloud secrets versions add SECRET_NAME --data-file=- --project=$PROJECT_ID

# Grant service account access
$SERVICE_ACCOUNT = "sales-intelligence-sa@${PROJECT_ID}.iam.gserviceaccount.com"
$secrets = @("salesforce-client-id", "salesforce-client-secret", "salesforce-username", 
             "salesforce-password", "salesforce-security-token", "dialpad-api-key", "hubspot-api-key")
foreach ($secret in $secrets) {
    gcloud secrets add-iam-policy-binding $secret `
      --member="serviceAccount:$SERVICE_ACCOUNT" `
      --role="roles/secretmanager.secretAccessor" `
      --project=$PROJECT_ID
}
```

**See [README_DEPLOYMENT.md](README_DEPLOYMENT.md) for detailed secret setup instructions.**

---

### Step 5: Deploy All Cloud Functions

```powershell
# PowerShell
.\scripts\deploy_all.ps1
```

```bash
# Bash
chmod +x scripts/deploy_all.sh
./scripts/deploy_all.sh
```

**What this does:**
- Deploys all 13 Cloud Functions (Phase 1 + Phase 2)
- Configures IAM permissions
- Sets up function-to-function access

**Deployment Time**: ~15-20 minutes

---

## Verify Deployment

```powershell
# List all functions
gcloud functions list --gen2 --region=us-central1 --project=$env:GCP_PROJECT_ID

# Test a function
gcloud functions call gmail-sync --gen2 --region=us-central1 --project=$env:GCP_PROJECT_ID

# Check BigQuery data
bq query --use_legacy_sql=false --project_id=$env:GCP_PROJECT_ID "
SELECT COUNT(*) as total_accounts 
FROM \`$env:GCP_PROJECT_ID.sales_intelligence.sf_accounts\`
"
```

---

## Next Steps

1. **Create Cloud Scheduler Jobs** (see [README_DEPLOYMENT.md](README_DEPLOYMENT.md#step-6-cloud-scheduler-setup))
2. **Deploy Web Application** (see [README_DEPLOYMENT.md](README_DEPLOYMENT.md#step-7-web-application-deployment))
3. **Test All Functions** (see [README_DEPLOYMENT.md](README_DEPLOYMENT.md#verification--testing))

---

## Troubleshooting

If you encounter any issues:

1. **Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)** for common errors and solutions
2. **Review function logs**:
   ```powershell
   gcloud functions logs read FUNCTION_NAME --gen2 --region=us-central1 --limit=50
   ```
3. **Verify IAM permissions**:
   ```powershell
   gcloud projects get-iam-policy $env:GCP_PROJECT_ID
   ```

---

## Scripts Reference

| Script | Purpose | Platform |
|--------|---------|----------|
| `scripts/setup_service_account.ps1` | Create service account & grant IAM roles | Windows |
| `scripts/setup_service_account.sh` | Create service account & grant IAM roles | Linux/Mac |
| `scripts/create_bigquery_datasets.ps1` | Create BigQuery dataset & tables | Windows |
| `scripts/create_bigquery_datasets.sh` | Create BigQuery dataset & tables | Linux/Mac |
| `scripts/deploy_all.ps1` | Deploy all Cloud Functions | Windows |
| `scripts/deploy_all.sh` | Deploy all Cloud Functions | Linux/Mac |

---

## Deployment Checklist

- [ ] Environment variables set
- [ ] Service account created and configured
- [ ] BigQuery dataset and tables created
- [ ] All secrets created and configured
- [ ] All Cloud Functions deployed
- [ ] Functions tested successfully
- [ ] Cloud Scheduler jobs created
- [ ] Web application deployed (optional)
- [ ] Data syncing from all sources

---

## Support

- **Detailed Guide**: [README_DEPLOYMENT.md](README_DEPLOYMENT.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

**Last Updated**: 2025-01-XX  
**Version**: 1.0
