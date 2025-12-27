# Configuration Guide

This document provides complete configuration details for the Sales Intelligence System.

## Project Information

- **GCP Project ID**: `maharani-sales-hub-11-2025`
- **Service Account**: `sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com`
- **Region**: `us-central1`
- **BigQuery Dataset**: `BQ_DATASET_NAME` (`sales_intelligence` default; `sales_intelligence_dev` in client env)

## Environment Variables

Create a `.env` file in the project root (see `.env.example`):

```bash
# GCP Configuration
GCP_PROJECT_ID=maharani-sales-hub-11-2025
GCP_REGION=us-central1
BQ_DATASET_NAME=sales_intelligence  # override to sales_intelligence_dev in client env

# Salesforce Configuration
# Use "login" for production, "test" for sandbox
SALESFORCE_DOMAIN=test

# LLM Configuration (Vertex-only)
LLM_PROVIDER=vertex_ai
LLM_MODEL=gemini-2.5-pro
EMBEDDING_MODEL=textembedding-gecko@001
```

## Terraform Variables

Create `infrastructure/terraform.tfvars` (see `infrastructure/terraform.tfvars.example`):

```hcl
project_id  = "maharani-sales-hub-11-2025"
region      = "us-central1"
environment = "prod"
dataset_id  = "sales_intelligence"
```

## Gmail Configuration

### Mailboxes

Configure mailboxes in `config/config.py`:

```python
gmail_mailboxes: list[str] = [
    "anand@maharaniweddings.com",
    # Add other 2 sales rep emails here
]
```

### Domain-Wide Delegation Setup

1. **Enable Domain-Wide Delegation in Google Workspace Admin**:
   - Go to Google Workspace Admin Console
   - Navigate to Security → API Controls → Domain-wide Delegation
   - Click "Add new"
   - Enter Client ID from OAuth credentials
   - Add scopes:
     - `https://www.googleapis.com/auth/gmail.readonly`
     - `https://www.googleapis.com/auth/gmail.modify`

2. **Store OAuth Credentials in Secret Manager**:
   ```bash
   echo -n "YOUR_CLIENT_ID" | gcloud secrets versions add gmail-oauth-client-id --data-file=-
   echo -n "YOUR_CLIENT_SECRET" | gcloud secrets versions add gmail-oauth-client-secret --data-file=-
   ```

## Salesforce Configuration

### Sandbox vs Production

For **Salesforce Sandbox**:
- Set `SALESFORCE_DOMAIN=test` in environment variables
- Username typically includes `.sandbox` suffix (e.g., `user@example.com.sandbox`)
- Use sandbox Connected App credentials

For **Salesforce Production**:
- Set `SALESFORCE_DOMAIN=login` in environment variables
- Use production Connected App credentials

**📖 See [SALESFORCE_SANDBOX_SETUP.md](SALESFORCE_SANDBOX_SETUP.md) for complete sandbox setup guide.**

## HubSpot Configuration

HubSpot uses Private Apps for API access. The access token is stored in Secret Manager.

**📖 See [HUBSPOT_SETUP.md](HUBSPOT_SETUP.md) for complete setup guide.**

Required scopes:
- `contacts.read` - Read contacts
- `companies.read` - Read companies
- `sequences.read` - Read sequences
- `sequences.write` - Enroll contacts in sequences
- `timeline.read` (recommended) - Read timeline events
- `timeline.write` (recommended) - Write timeline events

## Secret Manager Secrets

All secrets should be stored in Google Secret Manager. See [SECRETS_LIST.md](SECRETS_LIST.md) for complete list.

Required secrets:
- `gmail-oauth-client-id`
- `gmail-oauth-client-secret`
- `salesforce-client-id`
- `salesforce-client-secret`
- `salesforce-username`
- `salesforce-password`
- `salesforce-security-token`
- `salesforce-refresh-token` (optional, if using OAuth flow)
- `dialpad-api-key`
- `hubspot-api-key` (Private App access token)
- Vertex-only: no OpenAI/Anthropic secrets required (ADC)

## Service Account Permissions

The service account `sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com` requires:

- `roles/bigquery.dataEditor` - Write to BigQuery
- `roles/secretmanager.secretAccessor` - Read secrets
- `roles/logging.logWriter` - Write logs
- `roles/monitoring.metricWriter` - Write metrics
- `roles/cloudfunctions.invoker` - Invoke Cloud Functions
- `roles/pubsub.publisher` - Publish to Pub/Sub
- `roles/pubsub.subscriber` - Subscribe to Pub/Sub
- `roles/iam.serviceAccountTokenCreator` - Impersonate service account

These are automatically configured via Terraform.

## Cloud Scheduler Jobs

All scheduled jobs are configured in `infrastructure/scheduler.tf`:

- **Gmail Incremental Sync**: Every hour (`0 * * * *`)
- **Gmail Full Sync**: Daily at 2 AM (`0 2 * * *`)
- **Salesforce Incremental Sync**: Every 6 hours (`0 */6 * * *`)
- **Salesforce Full Sync**: Weekly on Sunday at 3 AM (`0 3 * * 0`)
- **Dialpad Sync**: Daily at 1 AM (`0 1 * * *`)
- **HubSpot Sync**: Daily at 4 AM (`0 4 * * *`)
- **Entity Resolution**: Every 4 hours (`0 */4 * * *`)

## Pub/Sub Topics

All Pub/Sub topics are configured in `infrastructure/pubsub.tf`:

- `gmail-ingestion` - Gmail data ingestion
- `salesforce-ingestion` - Salesforce data ingestion
- `dialpad-ingestion` - Dialpad data ingestion
- `hubspot-ingestion` - HubSpot data ingestion
- `ingestion-errors` - Error notifications
- Dead letter queues for all topics

## BigQuery Tables

All tables are defined in `bigquery/schemas/create_tables.sql`:

1. `gmail_messages` - Gmail messages
2. `gmail_participants` - Email participants
3. `gmail_sync_state` - Gmail sync state tracking
4. `sf_accounts` - Salesforce accounts
5. `sf_contacts` - Salesforce contacts
6. `sf_leads` - Salesforce leads
7. `sf_opportunities` - Salesforce opportunities
8. `sf_activities` - Salesforce activities
9. `dialpad_calls` - Dialpad call logs
10. `hubspot_sequences` - HubSpot sequences
11. `account_recommendations` - Account scoring
12. `etl_runs` - ETL job tracking
13. `manual_mappings` - Manual entity mappings

## Verification

After configuration, verify setup:

```bash
# Check GCP project
gcloud config get-value project

# Verify service account exists
gcloud iam service-accounts describe sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com

# List secrets
gcloud secrets list --project=maharani-sales-hub-11-2025

# Check BigQuery dataset
bq ls sales_intelligence
```

## Troubleshooting

### Service Account Not Found
- Verify the service account exists in project `maharani-sales-hub-11-2025`
- Check IAM permissions

### Secrets Not Found
- Verify secrets exist in Secret Manager
- Check service account has `secretmanager.secretAccessor` role

### Gmail DWD Not Working
- Verify domain-wide delegation is enabled in Google Workspace Admin
- Check OAuth client ID matches the one in Admin Console
- Verify scopes are correctly configured

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more details.

