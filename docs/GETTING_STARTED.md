# Getting Started: From Credentials to Running System

This guide walks you through the complete process of going from credentials to a fully running production system.

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] All required credentials (see [Deployment Checklist](DEPLOYMENT_CHECKLIST.md))
- [ ] GCP account with billing enabled
- [ ] GCP SDK (`gcloud`) installed and configured
- [ ] Terraform installed (>= 1.0)
- [ ] Python 3.11+ installed
- [ ] Docker installed (optional, for local development)

## Step-by-Step Process

### Step 1: Add Credentials to Secret Manager ✅

**This is what you mentioned - but it's just the first step!**

```bash
# Set your project
export GCP_PROJECT_ID="your-project-id"
gcloud config set project $GCP_PROJECT_ID

# Create secrets (you'll add values in next step)
./scripts/setup_secrets.sh

# Add actual values to secrets
echo -n "your-salesforce-username" | \
  gcloud secrets versions add salesforce-username --data-file=-

echo -n "your-salesforce-password" | \
  gcloud secrets versions add salesforce-password --data-file=-

echo -n "your-salesforce-security-token" | \
  gcloud secrets versions add salesforce-security-token --data-file=-

echo -n "your-dialpad-api-key" | \
  gcloud secrets versions add dialpad-api-key --data-file=-

echo -n "your-hubspot-api-key" | \
  gcloud secrets versions add hubspot-api-key --data-file=-

echo -n "your-anthropic-api-key" | \
  gcloud secrets versions add anthropic-api-key --data-file=-

# Or use OpenAI instead
echo -n "your-openai-api-key" | \
  gcloud secrets versions add openai-api-key --data-file=-
```

**Status after Step 1**: Credentials stored, but system is NOT running yet.

---

### Step 2: Set Up Infrastructure (Terraform) 🏗️

Create the GCP infrastructure (BigQuery, Service Accounts, IAM roles):

```bash
cd infrastructure

# Create terraform.tfvars file
cat > terraform.tfvars << EOF
project_id  = "your-project-id"
region      = "us-central1"
environment = "prod"
dataset_id  = "sales_intelligence"
EOF

# Initialize Terraform
terraform init

# Review what will be created
terraform plan

# Create infrastructure
terraform apply
```

**This creates:**
- BigQuery dataset
- Service accounts with proper IAM roles
- Cloud Storage bucket for function source code
- Enables required APIs

**Status after Step 2**: Infrastructure ready, but no code deployed yet.

---

### Step 3: Create BigQuery Tables 📊

Create all required database tables:

```bash
# Update project_id in SQL file
sed "s/{project_id}/$GCP_PROJECT_ID/g" bigquery/schemas/create_tables.sql > /tmp/create_tables.sql

# Create tables
bq query --use_legacy_sql=false < /tmp/create_tables.sql

# Verify tables were created
bq ls $GCP_PROJECT_ID:sales_intelligence
```

**Status after Step 3**: Database schema ready, but no data yet.

---

### Step 4: Deploy Cloud Functions ☁️

Deploy the data ingestion functions:

```bash
# Make sure you're in project root
cd ..

# Deploy all functions
./scripts/deploy_functions.sh

# Or deploy individually:
gcloud functions deploy gmail-sync \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=cloud_functions/gmail_sync \
  --entry-point=gmail_sync \
  --trigger-http \
  --service-account=YOUR_SERVICE_ACCOUNT_EMAIL \
  --memory=512MB \
  --timeout=540s \
  --max-instances=10 \
  --project=$GCP_PROJECT_ID

# Repeat for salesforce-sync, dialpad-sync, hubspot-sync
```

**Status after Step 4**: Functions deployed, but not scheduled yet.

---

### Step 5: Set Up Cloud Scheduler Jobs ⏰

Schedule automatic data syncs:

```bash
# Get your service account email from Terraform output
SERVICE_ACCOUNT=$(cd infrastructure && terraform output -raw service_account_email)

# Gmail incremental sync (every hour)
gcloud scheduler jobs create http gmail-incremental-sync \
  --location=us-central1 \
  --schedule="0 * * * *" \
  --uri="https://us-central1-$GCP_PROJECT_ID.cloudfunctions.net/gmail-sync" \
  --http-method=POST \
  --message-body='{"mailbox_email":"anand@maharaniweddings.com","sync_type":"incremental","access_token":"YOUR_OAUTH_TOKEN"}' \
  --oauth-service-account-email=$SERVICE_ACCOUNT \
  --project=$GCP_PROJECT_ID

# Salesforce daily sync (2 AM daily)
gcloud scheduler jobs create http salesforce-daily-sync \
  --location=us-central1 \
  --schedule="0 2 * * *" \
  --uri="https://us-central1-$GCP_PROJECT_ID.cloudfunctions.net/salesforce-sync" \
  --http-method=POST \
  --message-body='{"object_type":"Account","sync_type":"incremental"}' \
  --oauth-service-account-email=$SERVICE_ACCOUNT \
  --project=$GCP_PROJECT_ID

# Dialpad daily sync
gcloud scheduler jobs create http dialpad-daily-sync \
  --location=us-central1 \
  --schedule="0 3 * * *" \
  --uri="https://us-central1-$GCP_PROJECT_ID.cloudfunctions.net/dialpad-sync" \
  --http-method=POST \
  --message-body='{"user_id":"USER_ID","sync_type":"incremental"}' \
  --oauth-service-account-email=$SERVICE_ACCOUNT \
  --project=$GCP_PROJECT_ID
```

**Status after Step 5**: Automated syncs scheduled, but no historical data yet.

---

### Step 6: Run Initial Data Sync (Historical Data) 📥

Load historical data for the first time:

```bash
# Gmail full sync (for each mailbox)
curl -X POST \
  "https://us-central1-$GCP_PROJECT_ID.cloudfunctions.net/gmail-sync" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -d '{
    "mailbox_email": "anand@maharaniweddings.com",
    "sync_type": "full",
    "access_token": "YOUR_OAUTH_REFRESH_TOKEN"
  }'

# Salesforce full sync (for each object)
for object in Account Contact Lead Opportunity Task Event; do
  curl -X POST \
    "https://us-central1-$GCP_PROJECT_ID.cloudfunctions.net/salesforce-sync" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    -d "{\"object_type\":\"$object\",\"sync_type\":\"full\"}"
done

# Dialpad full sync
curl -X POST \
  "https://us-central1-$GCP_PROJECT_ID.cloudfunctions.net/dialpad-sync" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -d '{
    "user_id": "USER_ID",
    "sync_type": "full"
  }'
```

**Status after Step 6**: Historical data loaded, system is syncing!

---

### Step 7: Run Entity Resolution 🔗

Match emails and calls to Salesforce contacts:

```python
# Run entity resolution script
python -c "
from entity_resolution.matcher import EntityMatcher
from utils.bigquery_client import BigQueryClient

bq_client = BigQueryClient()
matcher = EntityMatcher(bq_client)

# Update participant matches
stats = matcher.update_participant_matches(batch_size=1000)
print(f'Matched {stats[\"matched\"]} out of {stats[\"processed\"]} participants')
"
```

**Status after Step 7**: Data matched and linked!

---

### Step 8: Verify System is Running ✅

Check that everything is working:

```bash
# Check ETL runs
bq query --use_legacy_sql=false \
  "SELECT * FROM \`$GCP_PROJECT_ID.sales_intelligence.etl_runs\` 
   ORDER BY started_at DESC LIMIT 10"

# Check data quality
bq query --use_legacy_sql=false \
  "SELECT 
    COUNT(*) as total_participants,
    COUNT(sf_contact_id) as matched_participants,
    ROUND(COUNT(sf_contact_id) * 100.0 / COUNT(*), 2) as match_percentage
   FROM \`$GCP_PROJECT_ID.sales_intelligence.gmail_participants\`"

# Check Cloud Function logs
gcloud functions logs read gmail-sync --limit=20 --region=us-central1

# Check scheduled jobs
gcloud scheduler jobs list --location=us-central1
```

**Status after Step 8**: ✅ **SYSTEM IS RUNNING!**

---

### Step 9: Set Up Web Application (Phase 3) 🌐

**Note**: The web application is Phase 3 and may not be implemented yet. If it is:

```bash
# Deploy web app to Cloud Run
gcloud run deploy sales-intelligence-app \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=$GCP_PROJECT_ID
```

---

## Quick Answer to Your Question

**Q: After adding required credentials/API keys, can I run this product?**

**A: Not yet!** Adding credentials is **Step 1 of 8**. You still need to:

1. ✅ Add credentials (you mentioned this)
2. ⏭️ Set up infrastructure (Terraform)
3. ⏭️ Create BigQuery tables
4. ⏭️ Deploy Cloud Functions
5. ⏭️ Set up Cloud Scheduler jobs
6. ⏭️ Run initial data sync
7. ⏭️ Run entity resolution
8. ⏭️ Verify everything works

**The system will be running after completing all 8 steps.**

---

## Estimated Time

- **Step 1** (Credentials): 30 minutes
- **Step 2** (Infrastructure): 15 minutes
- **Step 3** (BigQuery Tables): 5 minutes
- **Step 4** (Deploy Functions): 20 minutes
- **Step 5** (Scheduler Jobs): 15 minutes
- **Step 6** (Initial Sync): 1-4 hours (depends on data volume)
- **Step 7** (Entity Resolution): 30 minutes
- **Step 8** (Verification): 15 minutes

**Total: ~3-6 hours** (depending on data volume)

---

## Troubleshooting

If something doesn't work:

1. Check [Troubleshooting Guide](TROUBLESHOOTING.md)
2. Review Cloud Function logs: `gcloud functions logs read FUNCTION_NAME`
3. Check ETL runs in BigQuery: Query `etl_runs` table
4. Verify secrets are accessible: `gcloud secrets versions access latest --secret=SECRET_NAME`

---

## Next Steps After System is Running

1. **Monitor Performance**: Set up monitoring dashboards
2. **Set Up Alerts**: Configure alerting for failures
3. **Optimize**: Review and optimize based on usage patterns
4. **Scale**: Adjust resources based on load
5. **Maintain**: Regular updates and maintenance

---

## Summary

**Just adding credentials is NOT enough!** You need to complete all 8 steps to have a fully running system. The credentials are the foundation, but you still need to build and deploy the infrastructure, deploy the code, schedule the jobs, and load the data.

Use this guide to go from credentials to a fully operational system! 🚀

