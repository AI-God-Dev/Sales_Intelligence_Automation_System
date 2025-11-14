# Deployment Checklist

Complete checklist for deploying the Sales Intelligence System to production.

## Pre-Deployment

### Project Information
- [x] GCP Project ID: `maharani-sales-hub-11-2025`
- [x] Service Account: `sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com`
- [x] Region: `us-central1`
- [x] BigQuery Dataset: `sales_intelligence`

### Prerequisites
- [ ] GCP account with billing enabled
- [ ] GCP SDK (`gcloud`) installed and configured
- [ ] Terraform >= 1.0 installed
- [ ] Python 3.11+ installed
- [ ] Access to Google Workspace Admin Console (for Gmail DWD)
- [ ] Access to Salesforce Admin (for API credentials)
- [ ] Access to Dialpad Admin (for API key)
- [ ] Access to HubSpot Admin (for Private App creation)

## Step 1: Configure GCP Project

- [ ] Set GCP project: `gcloud config set project maharani-sales-hub-11-2025`
- [ ] Enable required APIs:
  ```bash
  gcloud services enable cloudfunctions.googleapis.com
  gcloud services enable cloudscheduler.googleapis.com
  gcloud services enable secretmanager.googleapis.com
  gcloud services enable bigquery.googleapis.com
  gcloud services enable run.googleapis.com
  gcloud services enable pubsub.googleapis.com
  gcloud services enable iam.googleapis.com
  gcloud services enable gmail.googleapis.com
  ```

## Step 2: Setup Secrets in Secret Manager

- [ ] Run setup script: `./scripts/setup_secrets.sh`
- [ ] Add Gmail OAuth credentials:
  - [ ] `gmail-oauth-client-id`
  - [ ] `gmail-oauth-client-secret`
- [ ] Add Salesforce credentials:
  - [ ] `salesforce-client-id`
  - [ ] `salesforce-client-secret`
  - [ ] `salesforce-username`
  - [ ] `salesforce-password`
  - [ ] `salesforce-security-token`
  - [ ] `salesforce-refresh-token`
- [ ] Add Dialpad API key: `dialpad-api-key`
- [ ] Add HubSpot API key: `hubspot-api-key`
- [ ] Add LLM API keys (optional):
  - [ ] `openai-api-key`
  - [ ] `anthropic-api-key`

See [SECRETS_LIST.md](SECRETS_LIST.md) for detailed instructions.

## Step 3: Configure Gmail Domain-Wide Delegation

- [ ] Create OAuth 2.0 credentials in Google Cloud Console
- [ ] Note the Client ID
- [ ] In Google Workspace Admin Console:
  - [ ] Navigate to Security → API Controls → Domain-wide Delegation
  - [ ] Click "Add new"
  - [ ] Enter Client ID from OAuth credentials
  - [ ] Add scopes:
    - `https://www.googleapis.com/auth/gmail.readonly`
    - `https://www.googleapis.com/auth/gmail.modify`
  - [ ] Authorize
- [ ] Verify service account can access Gmail API

## Step 4: Deploy Infrastructure with Terraform

- [ ] Navigate to infrastructure directory: `cd infrastructure`
- [ ] Copy terraform.tfvars.example: `cp terraform.tfvars.example terraform.tfvars`
- [ ] Verify terraform.tfvars has correct values:
  ```hcl
  project_id  = "maharani-sales-hub-11-2025"
  region      = "us-central1"
  environment = "prod"
  dataset_id  = "sales_intelligence"
  ```
- [ ] Initialize Terraform: `terraform init`
- [ ] Review plan: `terraform plan`
- [ ] Apply infrastructure: `terraform apply`
- [ ] Verify outputs:
  - [ ] BigQuery dataset created
  - [ ] Pub/Sub topics created
  - [ ] Cloud Scheduler jobs created
  - [ ] Service account permissions configured

## Step 5: Create BigQuery Tables

- [ ] Update project_id in SQL file:
  ```bash
  sed "s/{project_id}/maharani-sales-hub-11-2025/g" bigquery/schemas/create_tables.sql > /tmp/create_tables.sql
  ```
- [ ] Create tables: `bq query --use_legacy_sql=false < /tmp/create_tables.sql`
- [ ] Verify tables created: `bq ls sales_intelligence`
- [ ] Verify all 13 tables exist:
  - [ ] gmail_messages
  - [ ] gmail_participants
  - [ ] gmail_sync_state
  - [ ] sf_accounts
  - [ ] sf_contacts
  - [ ] sf_leads
  - [ ] sf_opportunities
  - [ ] sf_activities
  - [ ] dialpad_calls
  - [ ] hubspot_sequences
  - [ ] account_recommendations
  - [ ] etl_runs
  - [ ] manual_mappings

## Step 6: Deploy Cloud Functions

- [ ] Navigate to project root
- [ ] Deploy functions: `./scripts/deploy_functions.sh`
- [ ] Verify functions deployed:
  ```bash
  gcloud functions list --region=us-central1
  ```
- [ ] Verify each function:
  - [ ] gmail-sync
  - [ ] salesforce-sync
  - [ ] dialpad-sync
  - [ ] hubspot-sync
  - [ ] entity-resolution

## Step 7: Configure Gmail Mailboxes

- [ ] Update `config/config.py` with all 3 mailbox emails:
  ```python
  gmail_mailboxes: list[str] = [
      "anand@maharaniweddings.com",
      "email2@maharaniweddings.com",  # Add second mailbox
      "email3@maharaniweddings.com",  # Add third mailbox
  ]
  ```
- [ ] Redeploy Gmail sync function if needed

## Step 8: Verify Cloud Scheduler Jobs

- [ ] List scheduler jobs: `gcloud scheduler jobs list --location=us-central1`
- [ ] Verify all jobs exist:
  - [ ] gmail-incremental-sync
  - [ ] gmail-full-sync
  - [ ] salesforce-incremental-sync
  - [ ] salesforce-full-sync
  - [ ] dialpad-sync
  - [ ] hubspot-sync
  - [ ] entity-resolution
- [ ] Test one job manually:
  ```bash
  gcloud scheduler jobs run gmail-incremental-sync --location=us-central1
  ```

## Step 9: Initial Data Load

- [ ] Trigger Gmail full sync manually or wait for scheduled run
- [ ] Trigger Salesforce full sync manually or wait for scheduled run
- [ ] Trigger Dialpad sync manually or wait for scheduled run
- [ ] Trigger HubSpot sync manually or wait for scheduled run
- [ ] Verify data in BigQuery:
```bash
  bq query --use_legacy_sql=false \
    "SELECT COUNT(*) as count FROM \`maharani-sales-hub-11-2025.sales_intelligence.gmail_messages\`"
  ```

## Step 10: Run Entity Resolution

- [ ] Trigger entity resolution manually:
  ```bash
  gcloud scheduler jobs run entity-resolution --location=us-central1
  ```
- [ ] Verify matches in BigQuery:
```bash
  bq query --use_legacy_sql=false \
    "SELECT COUNT(*) as matched FROM \`maharani-sales-hub-11-2025.sales_intelligence.gmail_participants\` WHERE sf_contact_id IS NOT NULL"
  ```

## Step 11: Monitoring Setup

- [ ] Verify error notifications are working:
  - [ ] Check Pub/Sub topic `ingestion-errors` exists
  - [ ] Set up Cloud Monitoring alerts for error topic
- [ ] Set up Cloud Monitoring dashboards:
  - [ ] ETL job success/failure rates
  - [ ] Data ingestion volumes
  - [ ] Entity resolution match rates
  - [ ] Function execution times
- [ ] Configure alerting:
  - [ ] ETL job failures
  - [ ] High error rates
  - [ ] Function timeouts
  - [ ] API quota exhaustion

## Step 12: Verification & Testing

- [ ] Check Cloud Functions logs:
  ```bash
  gcloud functions logs read gmail-sync --limit=50 --region=us-central1
  ```
- [ ] Verify ETL runs table:
  ```bash
  bq query --use_legacy_sql=false \
    "SELECT * FROM \`maharani-sales-hub-11-2025.sales_intelligence.etl_runs\` ORDER BY started_at DESC LIMIT 10"
  ```
- [ ] Run automated tests:
  ```bash
  pytest tests/ -v
  ```
- [ ] Verify data quality:
  - [ ] Email match percentage > 90%
  - [ ] Call match percentage > 85%
  - [ ] No duplicate records
  - [ ] All timestamps are valid

## Post-Deployment

- [ ] Document any custom configurations
- [ ] Train team on monitoring and operations
- [ ] Set up backup procedures
- [ ] Schedule regular data quality reviews
- [ ] Plan for scaling if needed

## Troubleshooting

If any step fails:
1. Check Cloud Logging for errors
2. Verify service account permissions
3. Check Secret Manager secrets exist
4. Verify API quotas are not exceeded
5. Review [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## Support

For issues:
- Check Cloud Logging
- Review Pub/Sub error notifications
- Check BigQuery `etl_runs` table
- Review test results
