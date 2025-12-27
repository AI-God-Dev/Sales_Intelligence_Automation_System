#!/bin/bash
# Deploy Phase 2 Intelligence & Automation Cloud Functions
# IMPORTANT: Deploys from project root to include shared modules

set -e

PROJECT_ID="${GCP_PROJECT_ID:-maharani-sales-hub-11-2025}"
REGION="${GCP_REGION:-us-central1}"
DATASET_NAME="${BQ_DATASET_NAME:-${BIGQUERY_DATASET:-sales_intelligence}}"
SERVICE_ACCOUNT_NAME="${GCP_SERVICE_ACCOUNT_NAME:-sales-intel-poc-sa}"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "Deploying Phase 2 Cloud Functions to project: $PROJECT_ID"
echo "Using service account: $SERVICE_ACCOUNT"

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Deploy Embeddings Generator
echo "Deploying Embeddings Generator Function..."
gcloud functions deploy generate-embeddings \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=. \
  --entry-point=generate_embeddings \
  --trigger-http \
  --service-account=$SERVICE_ACCOUNT \
  --memory=1024MB \
  --timeout=540s \
  --max-instances=5 \
  --min-instances=0 \
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,BQ_DATASET_NAME=$DATASET_NAME,LLM_PROVIDER=vertex_ai,LLM_MODEL=gemini-2.5-pro,EMBEDDING_PROVIDER=vertex_ai" \
  --project=$PROJECT_ID

# Deploy Account Scoring Function
echo "Deploying Account Scoring Function..."
gcloud functions deploy account-scoring \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=. \
  --entry-point=account_scoring_job \
  --trigger-http \
  --service-account=$SERVICE_ACCOUNT \
  --memory=2048MB \
  --timeout=540s \
  --max-instances=3 \
  --min-instances=0 \
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,BQ_DATASET_NAME=$DATASET_NAME,LLM_PROVIDER=vertex_ai,LLM_MODEL=gemini-2.5-pro" \
  --project=$PROJECT_ID

# Deploy NLP Query Function
echo "Deploying NLP Query Function..."
gcloud functions deploy nlp-query \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=. \
  --entry-point=nlp_query \
  --trigger-http \
  --service-account=$SERVICE_ACCOUNT \
  --memory=1024MB \
  --timeout=60s \
  --max-instances=10 \
  --min-instances=0 \
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,BQ_DATASET_NAME=$DATASET_NAME,LLM_PROVIDER=vertex_ai,LLM_MODEL=gemini-2.5-pro" \
  --project=$PROJECT_ID

# Deploy Lead Creation Function
echo "Deploying Lead Creation Function..."
gcloud functions deploy create-leads \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=. \
  --entry-point=create_leads \
  --trigger-http \
  --service-account=$SERVICE_ACCOUNT \
  --memory=512MB \
  --timeout=300s \
  --max-instances=5 \
  --min-instances=0 \
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,BQ_DATASET_NAME=$DATASET_NAME" \
  --project=$PROJECT_ID

# Deploy HubSpot Enrollment Function
echo "Deploying HubSpot Enrollment Function..."
gcloud functions deploy enroll-hubspot \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=. \
  --entry-point=enroll_hubspot \
  --trigger-http \
  --service-account=$SERVICE_ACCOUNT \
  --memory=512MB \
  --timeout=300s \
  --max-instances=5 \
  --min-instances=0 \
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,BQ_DATASET_NAME=$DATASET_NAME" \
  --project=$PROJECT_ID

# Deploy Get HubSpot Sequences Function
echo "Deploying Get HubSpot Sequences Function..."
gcloud functions deploy get-hubspot-sequences \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=. \
  --entry-point=get_hubspot_sequences \
  --trigger-http \
  --service-account=$SERVICE_ACCOUNT \
  --memory=512MB \
  --timeout=60s \
  --max-instances=10 \
  --min-instances=0 \
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,BQ_DATASET_NAME=$DATASET_NAME" \
  --project=$PROJECT_ID

# Deploy Email Reply Generator Function
echo "Deploying Email Reply Generator Function..."
gcloud functions deploy generate-email-reply \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=. \
  --entry-point=generate_email_reply \
  --trigger-http \
  --service-account=$SERVICE_ACCOUNT \
  --memory=1024MB \
  --timeout=120s \
  --max-instances=10 \
  --min-instances=0 \
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,BQ_DATASET_NAME=$DATASET_NAME,LLM_PROVIDER=vertex_ai,LLM_MODEL=gemini-2.5-pro" \
  --project=$PROJECT_ID

# Deploy Semantic Search Function
echo "Deploying Semantic Search Function..."
gcloud functions deploy semantic-search \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=. \
  --entry-point=semantic_search \
  --trigger-http \
  --service-account=$SERVICE_ACCOUNT \
  --memory=1024MB \
  --timeout=60s \
  --max-instances=10 \
  --min-instances=0 \
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,BQ_DATASET_NAME=$DATASET_NAME,EMBEDDING_PROVIDER=vertex_ai" \
  --project=$PROJECT_ID

# Grant Cloud Scheduler permission to invoke functions
echo "Granting Cloud Scheduler permission to invoke functions..."
for func in generate-embeddings account-scoring create-leads enroll-hubspot get-hubspot-sequences generate-email-reply semantic-search; do
  gcloud functions add-iam-policy-binding $func \
    --region=$REGION \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/cloudfunctions.invoker" \
    --project=$PROJECT_ID || echo "Warning: Could not add IAM binding for $func"
done

# Grant allUsers permission for web app (or use authenticated access)
echo "Granting public access for web app integration..."
for func in nlp-query get-hubspot-sequences semantic-search; do
  gcloud functions add-iam-policy-binding $func \
    --region=$REGION \
    --member="allUsers" \
    --role="roles/cloudfunctions.invoker" \
    --project=$PROJECT_ID || echo "Warning: Could not add public access for $func"
done

echo "Phase 2 deployment complete!"
echo ""
echo "Next steps:"
echo "1. Enable Vertex AI API: gcloud services enable aiplatform.googleapis.com --project=$PROJECT_ID"
echo "2. Verify service account has Vertex AI User role"
echo "3. Create Cloud Scheduler jobs for daily scoring and embeddings"
echo "4. Deploy web application"

