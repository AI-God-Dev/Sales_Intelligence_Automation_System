# Setup Complete - Phase 1 Ready for Deployment

## ✅ What Has Been Created

### Automated Setup Scripts

1. **`setup_complete.ps1`** - Master orchestration script
   - Runs all setup steps in sequence
   - Handles errors and provides clear feedback

2. **`enable_apis.ps1`** - Enables all required GCP APIs
   - BigQuery, Cloud Functions, Secret Manager, etc.
   - Checks if APIs are already enabled

3. **`create_secrets.ps1`** - Creates and populates Secret Manager secrets
   - Creates all 10 required secrets
   - Prompts for credential values
   - Grants service account access

### BigQuery Setup

4. **`scripts/setup_bigquery.ps1`** - Creates dataset and tables
   - Creates `sales_intelligence` dataset
   - Creates all 13 tables from SQL schema
   - Creates view `v_unmatched_emails`
   - Verifies table creation

5. **`bigquery/schemas/create_tables.sql`** - Updated with project ID
   - All `{project_id}` placeholders replaced with `maharani-sales-hub-11-2025`

### Cloud Functions Deployment

6. **`scripts/deploy_functions.ps1`** - Deploys all 5 Cloud Functions
   - gmail-sync
   - salesforce-sync
   - dialpad-sync
   - hubspot-sync
   - entity-resolution
   - Sets IAM permissions for Cloud Scheduler

### Cloud Scheduler

7. **`scripts/create_scheduler_jobs.ps1`** - Creates all 7 scheduled jobs
   - gmail-full-sync (daily 2 AM)
   - gmail-incremental-sync (hourly)
   - salesforce-full-sync (weekly Sunday 3 AM)
   - salesforce-incremental-sync (every 6 hours)
   - dialpad-sync (daily 1 AM)
   - hubspot-sync (daily 4 AM)
   - entity-resolution (every 4 hours)

### Pub/Sub

8. **`scripts/create_pubsub_topic.ps1`** - Creates error notification topic
   - Topic: `ingestion-errors`

### Testing & Verification

9. **`scripts/test_ingestion.ps1`** - Tests all ingestion functions
   - Triggers each Cloud Function manually
   - Displays results

10. **`scripts/check_logs.ps1`** - Checks Cloud Function logs
    - Shows recent logs for all functions

11. **`scripts/check_bigquery.ps1`** - Checks BigQuery data
    - Shows row counts for all tables
    - Displays recent ETL runs

12. **`scripts/verify_deployment.ps1`** - Comprehensive verification
    - Checks BigQuery dataset and tables
    - Verifies Cloud Functions exist
    - Verifies Cloud Scheduler jobs
    - Verifies Pub/Sub topic
    - Verifies Secret Manager secrets

### Documentation

13. **`QUICK_START.md`** - Quick start guide
    - Fastest path to get running
    - Step-by-step instructions

14. **`MANUAL_STEPS.md`** - Manual credential creation guide
    - Gmail OAuth setup
    - Salesforce Connected App setup
    - Dialpad API key generation
    - HubSpot Private App setup

15. **`docs/INGESTION_TRIGGERS.md`** - Manual trigger commands
    - curl commands for each ingestion function
    - PowerShell examples

16. **`docs/PHASE1_HANDOFF.md`** - Complete handoff documentation
    - Architecture overview
    - Deployment instructions
    - Testing procedures

## 🚀 How to Use

### Option 1: Automated Setup (Recommended)

```powershell
# 1. Prepare credentials (see MANUAL_STEPS.md)
# 2. Run master setup script
.\setup_complete.ps1
```

### Option 2: Step-by-Step Setup

```powershell
# 1. Enable APIs
.\enable_apis.ps1

# 2. Create secrets (enter credentials when prompted)
.\create_secrets.ps1

# 3. Setup BigQuery
.\scripts\setup_bigquery.ps1

# 4. Create Pub/Sub topic
.\scripts\create_pubsub_topic.ps1

# 5. Deploy Cloud Functions
.\scripts\deploy_functions.ps1

# 6. Create Scheduler jobs
.\scripts\create_scheduler_jobs.ps1

# 7. Verify deployment
.\scripts\verify_deployment.ps1
```

### Testing

```powershell
# Test all ingestion functions
.\scripts\test_ingestion.ps1

# Check logs
.\scripts\check_logs.ps1

# Check BigQuery data
.\scripts\check_bigquery.ps1
```

## 📋 Prerequisites Checklist

Before running setup, ensure:

- [ ] Google Cloud SDK installed (`gcloud`, `bq`)
- [ ] Authenticated: `gcloud auth login`
- [ ] Project set: `gcloud config set project maharani-sales-hub-11-2025`
- [ ] All credentials collected (see `MANUAL_STEPS.md`):
  - [ ] Gmail OAuth Client ID & Secret
  - [ ] Salesforce credentials (5 values)
  - [ ] Dialpad API Key
  - [ ] HubSpot Private App Access Token

## 🎯 What Gets Created

### GCP Resources

- **1 BigQuery Dataset**: `sales_intelligence`
- **13 BigQuery Tables**: All Phase 1 tables
- **1 BigQuery View**: `v_unmatched_emails`
- **5 Cloud Functions**: All ingestion and processing functions
- **7 Cloud Scheduler Jobs**: Automated ingestion schedules
- **1 Pub/Sub Topic**: `ingestion-errors`
- **10 Secret Manager Secrets**: All API credentials

### Automated Schedules

- Gmail full sync: Daily at 2 AM
- Gmail incremental: Every hour
- Salesforce full sync: Weekly Sunday 3 AM
- Salesforce incremental: Every 6 hours
- Dialpad sync: Daily at 1 AM
- HubSpot sync: Daily at 4 AM
- Entity resolution: Every 4 hours

## 🔍 Verification

After setup, verify everything works:

```powershell
# Comprehensive verification
.\scripts\verify_deployment.ps1

# Test ingestion
.\scripts\test_ingestion.ps1

# Check results
.\scripts\check_bigquery.ps1
```

## 📚 Documentation

- **Quick Start**: `QUICK_START.md`
- **Manual Steps**: `MANUAL_STEPS.md`
- **Ingestion Triggers**: `docs/INGESTION_TRIGGERS.md`
- **Complete Handoff**: `docs/PHASE1_HANDOFF.md`
- **Testing Guide**: `docs/PHASE1_TESTING_GUIDE.md`

## ⚠️ Important Notes

1. **Credentials**: You must create third-party API credentials manually (see `MANUAL_STEPS.md`). These cannot be automated.

2. **Service Account**: The scripts assume the service account `sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com` exists. If it doesn't, create it first:
   ```powershell
   gcloud iam service-accounts create sales-intel-poc-sa --display-name="Sales Intelligence POC Service Account" --project=maharani-sales-hub-11-2025
   ```

3. **Permissions**: The service account needs these roles:
   - BigQuery Data Editor
   - BigQuery Job User
   - Secret Manager Secret Accessor
   - Pub/Sub Publisher

4. **First Run**: The first ingestion run may take longer as it processes all historical data.

## 🎉 Success Criteria

Setup is successful when:

- ✅ All verification checks pass (`.\scripts\verify_deployment.ps1`)
- ✅ All Cloud Functions deploy without errors
- ✅ Test ingestion runs successfully (`.\scripts\test_ingestion.ps1`)
- ✅ Data appears in BigQuery tables
- ✅ ETL runs are recorded in `etl_runs` table

## 🆘 Troubleshooting

If something fails:

1. Check `gcloud auth list` - ensure authenticated
2. Check project: `gcloud config get-value project`
3. Check APIs: `gcloud services list --enabled`
4. Check logs: `.\scripts\check_logs.ps1`
5. See `docs/TROUBLESHOOTING.md` for detailed help

## 📞 Next Steps

After successful setup:

1. Monitor ETL runs in BigQuery
2. Review data quality
3. Check Cloud Scheduler execution history
4. Proceed to Phase 2 development

---

**Phase 1 is now ready for real-world deployment and testing!** 🚀

