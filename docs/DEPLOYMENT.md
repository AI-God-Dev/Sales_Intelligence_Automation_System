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

Create `terraform.tfvars`:

```hcl
project_id  = "your-gcp-project-id"
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
- Service accounts
- IAM roles
- Cloud Storage buckets
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

Required secrets:
- `salesforce-username`
- `salesforce-password`
- `salesforce-security-token`
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

```bash
# Gmail incremental sync (every hour)
gcloud scheduler jobs create http gmail-incremental-sync \
  --location=us-central1 \
  --schedule="0 * * * *" \
  --uri="https://us-central1-PROJECT_ID.cloudfunctions.net/gmail-sync" \
  --http-method=POST \
  --message-body='{"mailbox_email":"user@example.com","sync_type":"incremental"}' \
  --oauth-service-account-email=SERVICE_ACCOUNT_EMAIL

# Salesforce daily sync
gcloud scheduler jobs create http salesforce-daily-sync \
  --location=us-central1 \
  --schedule="0 2 * * *" \
  --uri="https://us-central1-PROJECT_ID.cloudfunctions.net/salesforce-sync" \
  --http-method=POST \
  --message-body='{"object_type":"Account","sync_type":"incremental"}'
```

## Create BigQuery Tables

```bash
# Update project_id in SQL file
sed "s/{project_id}/YOUR_PROJECT_ID/g" bigquery/schemas/create_tables.sql | \
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
  "SELECT * FROM \`PROJECT_ID.sales_intelligence.etl_runs\` ORDER BY started_at DESC LIMIT 10"

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

- [ ] All secrets configured in Secret Manager
- [ ] IAM roles properly configured
- [ ] Cloud Scheduler jobs created
- [ ] BigQuery tables created
- [ ] Monitoring and alerting configured
- [ ] Backup and disaster recovery plan in place
- [ ] Documentation updated
- [ ] Team trained on operations

## Troubleshooting

### Common Issues

1. **Permission Denied**: Check IAM roles for service account
2. **Secret Not Found**: Verify secrets exist in Secret Manager
3. **Function Timeout**: Increase timeout or optimize code
4. **Quota Exceeded**: Request quota increase or implement rate limiting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more details.

