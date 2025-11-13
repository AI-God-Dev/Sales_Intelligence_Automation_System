# Setup Guide

This guide walks through setting up the Sales Intelligence & Automation System.

## Prerequisites

1. **Google Cloud Platform Account**
   - Active GCP project with billing enabled
   - GCP SDK installed and configured (`gcloud` CLI)
   - Appropriate IAM permissions

2. **API Access**
   - Salesforce API credentials (username, password, security token)
   - Gmail OAuth credentials (for 3 mailboxes)
   - Dialpad API key
   - HubSpot API credentials
   - LLM API keys (OpenAI or Anthropic)

3. **Python Environment**
   - Python 3.11+
   - pip package manager

## Step 1: GCP Project Setup

```bash
# Set your project ID
export GCP_PROJECT_ID="your-project-id"
gcloud config set project $GCP_PROJECT_ID

# Enable required APIs
gcloud services enable \
  cloudfunctions.googleapis.com \
  cloudscheduler.googleapis.com \
  secretmanager.googleapis.com \
  bigquery.googleapis.com \
  run.googleapis.com \
  logging.googleapis.com
```

## Step 2: Create BigQuery Dataset

```bash
# Create dataset
bq mk --dataset \
  --location=us-central1 \
  $GCP_PROJECT_ID:sales_intelligence

# Create tables (update project_id placeholder in SQL file)
sed "s/{project_id}/$GCP_PROJECT_ID/g" bigquery/schemas/create_tables.sql | bq query --use_legacy_sql=false
```

## Step 3: Setup Secrets

```bash
# Run setup script
chmod +x scripts/setup_secrets.sh
./scripts/setup_secrets.sh

# Add secret values (example)
echo -n "your-salesforce-username" | \
  gcloud secrets versions add salesforce-username --data-file=-
```

## Step 4: Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 5: Configure Environment

Create a `.env` file:

```env
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1
BIGQUERY_DATASET=sales_intelligence
SALESFORCE_DOMAIN=login
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022
EMBEDDING_MODEL=text-embedding-3-small
```

## Step 6: Deploy Cloud Functions

```bash
# Deploy functions
chmod +x scripts/deploy_functions.sh
./scripts/deploy_functions.sh
```

## Step 7: Setup Cloud Scheduler Jobs

```bash
# Gmail incremental sync (every hour)
gcloud scheduler jobs create http gmail-incremental-sync \
  --location=us-central1 \
  --schedule="0 * * * *" \
  --uri="https://us-central1-$GCP_PROJECT_ID.cloudfunctions.net/gmail-sync" \
  --http-method=POST \
  --message-body='{"mailbox_email":"anand@maharaniweddings.com","sync_type":"incremental"}' \
  --oauth-service-account-email="$GCP_PROJECT_ID@appspot.gserviceaccount.com"

# Salesforce daily sync
gcloud scheduler jobs create http salesforce-daily-sync \
  --location=us-central1 \
  --schedule="0 2 * * *" \
  --uri="https://us-central1-$GCP_PROJECT_ID.cloudfunctions.net/salesforce-sync" \
  --http-method=POST \
  --message-body='{"object_type":"Account","sync_type":"incremental"}'
```

## Step 8: Initial Data Load

For the first run, perform full syncs:

```bash
# Full Gmail sync
curl -X POST \
  "https://us-central1-$GCP_PROJECT_ID.cloudfunctions.net/gmail-sync" \
  -H "Content-Type: application/json" \
  -d '{
    "mailbox_email": "anand@maharaniweddings.com",
    "sync_type": "full",
    "access_token": "YOUR_OAUTH_TOKEN"
  }'

# Full Salesforce sync for each object
for object in Account Contact Lead Opportunity Task Event; do
  curl -X POST \
    "https://us-central1-$GCP_PROJECT_ID.cloudfunctions.net/salesforce-sync" \
    -H "Content-Type: application/json" \
    -d "{\"object_type\":\"$object\",\"sync_type\":\"full\"}"
done
```

## Step 9: Run Entity Resolution

After initial data load, run entity resolution:

```python
from entity_resolution.matcher import EntityMatcher
from utils.bigquery_client import BigQueryClient

bq_client = BigQueryClient()
matcher = EntityMatcher(bq_client)

# Update participant matches
stats = matcher.update_participant_matches(batch_size=1000)
print(f"Matched {stats['matched']} out of {stats['processed']} participants")
```

## Step 10: Verify Setup

```bash
# Check BigQuery tables
bq ls $GCP_PROJECT_ID:sales_intelligence

# Check ETL runs
bq query --use_legacy_sql=false \
  "SELECT * FROM \`$GCP_PROJECT_ID.sales_intelligence.etl_runs\` ORDER BY started_at DESC LIMIT 10"

# Check data quality
bq query --use_legacy_sql=false \
  "SELECT 
    COUNT(*) as total_participants,
    COUNT(sf_contact_id) as matched_participants,
    ROUND(COUNT(sf_contact_id) * 100.0 / COUNT(*), 2) as match_percentage
   FROM \`$GCP_PROJECT_ID.sales_intelligence.gmail_participants\`"
```

## Troubleshooting

### Cloud Function Deployment Fails
- Check IAM permissions
- Verify billing is enabled
- Check function logs: `gcloud functions logs read gmail-sync --limit=50`

### BigQuery Permission Errors
- Grant BigQuery Data Editor role to Cloud Functions service account
- Verify dataset exists and is accessible

### API Rate Limits
- Implement exponential backoff (already in code)
- Request quota increases if needed
- Monitor usage in GCP Console

### Entity Resolution Low Accuracy
- Check data quality in source systems
- Review manual_mappings table
- Run weekly reconciliation job

## Next Steps

After completing Phase 1 setup:
1. Proceed to Phase 2: Intelligence & Automation
2. Set up embeddings generation
3. Implement daily account scoring
4. Build web application

See main README.md for project phases and roadmap.

