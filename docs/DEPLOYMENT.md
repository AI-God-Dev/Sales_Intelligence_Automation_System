# Deployment Guide

## Prerequisites

1. Google Cloud Platform account with billing enabled
2. GCP SDK installed and configured
3. Terraform >= 1.0 installed
4. Docker installed (for local development)
5. Python 3.11+

## Infrastructure Setup

### 1. Initialize Terraform

```bash
cd infrastructure
terraform init
```

### 2. Create Terraform Variables File

Create `terraform.tfvars` (copy from `terraform.tfvars.example`):

```hcl
project_id  = "maharani-sales-hub-11-2025"
region      = "us-central1"
environment = "prod"
dataset_id  = "sales_intelligence"
```

### 3. Plan and Apply Infrastructure

```bash
terraform plan
terraform apply
```

This will create:
- BigQuery dataset
- Service accounts with IAM roles
- Pub/Sub topics and subscriptions
- Cloud Scheduler jobs
- Cloud Storage buckets
- Dead letter queues for error handling
- Required APIs enabled

## Secret Management

### Setup Secrets in Secret Manager

```bash
# Run setup script
./scripts/setup_secrets.sh

# Add secret values
echo -n "your-value" | \
  gcloud secrets versions add secret-name --data-file=-
```

Required secrets (see [SECRETS_LIST.md](../docs/SECRETS_LIST.md) for complete list):
- `gmail-oauth-client-id`
- `gmail-oauth-client-secret`
- `salesforce-client-id`
- `salesforce-client-secret`
- `salesforce-username`
- `salesforce-password`
- `salesforce-security-token`
- `salesforce-refresh-token`
- `dialpad-api-key`
- `hubspot-api-key`
- `openai-api-key`
- `anthropic-api-key`

## Deploy Cloud Functions

### Option 1: Using Deployment Script

```bash
chmod +x scripts/deploy_functions.sh
./scripts/deploy_functions.sh
```

### Option 2: Manual Deployment

```bash
# Deploy Gmail Sync
gcloud functions deploy gmail-sync \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=cloud_functions/gmail_sync \
  --entry-point=gmail_sync \
  --trigger-http \
  --service-account=YOUR_SERVICE_ACCOUNT \
  --memory=512MB \
  --timeout=540s \
  --max-instances=10

# Repeat for other functions...
```

## Setup Cloud Scheduler

**Note**: Cloud Scheduler jobs are automatically created by Terraform. If deploying manually:

```bash
# Gmail incremental sync (every hour)
gcloud scheduler jobs create http gmail-incremental-sync \
  --location=us-central1 \
  --schedule="0 * * * *" \
  --uri="https://us-central1-maharani-sales-hub-11-2025.cloudfunctions.net/gmail-sync" \
  --http-method=POST \
  --message-body='{"sync_type":"incremental"}' \
  --oauth-service-account-email=sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com

# Gmail full sync (daily at 2 AM)
gcloud scheduler jobs create http gmail-full-sync \
  --location=us-central1 \
  --schedule="0 2 * * *" \
  --uri="https://us-central1-maharani-sales-hub-11-2025.cloudfunctions.net/gmail-sync" \
  --http-method=POST \
  --message-body='{"sync_type":"full"}' \
  --oauth-service-account-email=sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com

# Salesforce incremental sync (every 6 hours)
gcloud scheduler jobs create http salesforce-incremental-sync \
  --location=us-central1 \
  --schedule="0 */6 * * *" \
  --uri="https://us-central1-maharani-sales-hub-11-2025.cloudfunctions.net/salesforce-sync" \
  --http-method=POST \
  --message-body='{"object_type":"Account","sync_type":"incremental"}' \
  --oauth-service-account-email=sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com

# Entity resolution (every 4 hours)
gcloud scheduler jobs create http entity-resolution \
  --location=us-central1 \
  --schedule="0 */4 * * *" \
  --uri="https://us-central1-maharani-sales-hub-11-2025.cloudfunctions.net/entity-resolution" \
  --http-method=POST \
  --message-body='{"batch_size":1000,"entity_type":"all"}' \
  --oauth-service-account-email=sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com
```

**Recommended**: Use Terraform to manage all Cloud Scheduler jobs (see `infrastructure/scheduler.tf`).

## Create BigQuery Tables

```bash
# Update project_id in SQL file
sed "s/{project_id}/maharani-sales-hub-11-2025/g" bigquery/schemas/create_tables.sql | \
  bq query --use_legacy_sql=false
```

## Verify Deployment

```bash
# Check Cloud Functions
gcloud functions list --region=us-central1

# Check BigQuery tables
bq ls sales_intelligence

# Check ETL runs
bq query --use_legacy_sql=false \
  "SELECT * FROM \`maharani-sales-hub-11-2025.sales_intelligence.etl_runs\` ORDER BY started_at DESC LIMIT 10"

# Test health check
curl https://YOUR_FUNCTION_URL/health
```

## Monitoring

### View Logs

```bash
# Cloud Functions logs
gcloud functions logs read gmail-sync --limit=50

# BigQuery logs
gcloud logging read "resource.type=bigquery_dataset" --limit=50
```

### Set Up Alerts

Create alerting policies in Cloud Monitoring for:
- ETL job failures
- High error rates
- Slow query performance
- API quota exhaustion

## Rollback

If deployment fails:

```bash
# Rollback Terraform
cd infrastructure
terraform destroy

# Or rollback specific function
gcloud functions deploy gmail-sync --version=VERSION_ID
```

## Production Checklist

- [ ] All secrets configured in Secret Manager (see [SECRETS_LIST.md](../docs/SECRETS_LIST.md))
- [ ] Gmail domain-wide delegation configured in Google Workspace Admin
- [ ] Service account IAM roles properly configured
- [ ] Pub/Sub topics and subscriptions created (via Terraform)
- [ ] Cloud Scheduler jobs created (via Terraform)
- [ ] BigQuery dataset and tables created
- [ ] Cloud Functions deployed with service account
- [ ] Error notification monitoring configured
- [ ] Monitoring and alerting configured
- [ ] Backup and disaster recovery plan in place
- [ ] Documentation reviewed and updated
- [ ] Team trained on operations

See [DEPLOYMENT_SUMMARY.md](../docs/DEPLOYMENT_SUMMARY.md) for complete deployment guide.

## Troubleshooting

### Common Issues

1. **Permission Denied**: Check IAM roles for service account
2. **Secret Not Found**: Verify secrets exist in Secret Manager
3. **Function Timeout**: Increase timeout or optimize code
4. **Quota Exceeded**: Request quota increase or implement rate limiting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more details.

