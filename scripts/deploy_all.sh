#!/bin/bash
# ============================================================================
# MASTER DEPLOYMENT SCRIPT - Sales Intelligence Automation System
# ============================================================================
# This script deploys ALL Cloud Functions (Phase 1 + Phase 2) to GCP
# 
# Prerequisites:
#   1. gcloud CLI installed and authenticated
#   2. GCP_PROJECT_ID environment variable set (or edit below)
#   3. Service account created with required permissions
#   4. Required APIs enabled
#   5. BigQuery dataset and tables created
#   6. Secrets configured in Secret Manager
#
# Usage:
#   chmod +x scripts/deploy_all.sh
#   ./scripts/deploy_all.sh
# ============================================================================

set -e  # Exit on error

# ============================================================================
# CONFIGURATION - Update these values for your environment
# ============================================================================
PROJECT_ID="${GCP_PROJECT_ID:-YOUR_PROJECT_ID}"
REGION="${GCP_REGION:-us-central1}"
DATASET_NAME="${BQ_DATASET_NAME:-${BIGQUERY_DATASET:-sales_intelligence}}"
SERVICE_ACCOUNT_NAME="${GCP_SERVICE_ACCOUNT_NAME:-sales-intelligence-sa}"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Validate configuration
if [ "$PROJECT_ID" = "YOUR_PROJECT_ID" ] || [ -z "$PROJECT_ID" ]; then
    echo "[ERROR] GCP_PROJECT_ID not set!"
    echo "Set it with: export GCP_PROJECT_ID='your-project-id'"
    echo "Or edit this script and set PROJECT_ID directly"
    exit 1
fi

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

print_header() {
    echo ""
    echo "========================================"
    echo "$1"
    echo "========================================"
}

print_step() {
    echo "→ $1"
}

deploy_function() {
    local function_name=$1
    local entry_point=$2
    local description=$3
    local memory_mb=${4:-512}
    local timeout_seconds=${5:-540}
    local max_instances=${6:-10}
    shift 6
    local additional_env_vars=("$@")
    
    print_step "Deploying $function_name ($description)"
    echo "  Entry Point: $entry_point"
    echo "  Memory: ${memory_mb}MB, Timeout: ${timeout_seconds}s"
    
    # Build environment variables
    local env_vars=("GCP_PROJECT_ID=$PROJECT_ID" "GCP_REGION=$REGION" "BQ_DATASET_NAME=$DATASET_NAME")
    env_vars+=("${additional_env_vars[@]}")
    local env_vars_string=$(IFS=','; echo "${env_vars[*]}")
    
    # Deploy function
    if gcloud functions deploy "$function_name" \
        --gen2 \
        --runtime=python311 \
        --region="$REGION" \
        --source=. \
        --entry-point="$entry_point" \
        --trigger-http \
        --no-allow-unauthenticated \
        --service-account="$SERVICE_ACCOUNT" \
        --memory="${memory_mb}MB" \
        --timeout="${timeout_seconds}s" \
        --max-instances="$max_instances" \
        --min-instances=0 \
        --set-env-vars="$env_vars_string" \
        --project="$PROJECT_ID"; then
        echo "  [✓] Successfully deployed $function_name"
        return 0
    else
        echo "  [✗] Failed to deploy $function_name"
        return 1
    fi
}

# ============================================================================
# MAIN DEPLOYMENT
# ============================================================================

print_header "Sales Intelligence System - Master Deployment"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Service Account: $SERVICE_ACCOUNT"

# Ensure we're in project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

if [ ! -f "main.py" ] && [ ! -f "config/config.py" ]; then
    echo "[ERROR] Not in project root! Expected to find main.py or config/config.py"
    echo "Current directory: $(pwd)"
    exit 1
fi

echo "Project root: $PROJECT_ROOT"
echo ""

# ============================================================================
# PHASE 1: DATA INGESTION FUNCTIONS
# ============================================================================

print_header "Phase 1: Data Ingestion Functions"

# Deploy Phase 1 functions
deploy_function "gmail-sync" \
    "gmail_sync" \
    "Gmail message ingestion" \
    2048 540 && PHASE1_GMAIL=1 || PHASE1_GMAIL=0

deploy_function "salesforce-sync" \
    "salesforce_sync" \
    "Salesforce object ingestion" \
    512 540 && PHASE1_SF=1 || PHASE1_SF=0

deploy_function "dialpad-sync" \
    "dialpad_sync" \
    "Dialpad call logs ingestion" \
    512 540 && PHASE1_DIALPAD=1 || PHASE1_DIALPAD=0

deploy_function "hubspot-sync" \
    "hubspot_sync" \
    "HubSpot sequences ingestion" \
    512 300 && PHASE1_HUBSPOT=1 || PHASE1_HUBSPOT=0

deploy_function "entity-resolution" \
    "entity_resolution" \
    "Entity resolution and matching" \
    1024 540 && PHASE1_ER=1 || PHASE1_ER=0

# ============================================================================
# PHASE 2: INTELLIGENCE & AUTOMATION FUNCTIONS
# ============================================================================

print_header "Phase 2: Intelligence & Automation Functions"

# Deploy Phase 2 functions
deploy_function "generate-embeddings" \
    "generate_embeddings" \
    "Generate vector embeddings for emails and calls" \
    1024 540 10 \
    "LLM_PROVIDER=vertex_ai" "EMBEDDING_PROVIDER=vertex_ai" && PHASE2_EMBED=1 || PHASE2_EMBED=0

deploy_function "account-scoring" \
    "account_scoring_job" \
    "AI-powered account scoring and prioritization" \
    2048 540 3 \
    "LLM_PROVIDER=vertex_ai" && PHASE2_SCORING=1 || PHASE2_SCORING=0

deploy_function "nlp-query" \
    "nlp_query" \
    "Natural language to SQL query conversion" \
    1024 60 10 \
    "LLM_PROVIDER=vertex_ai" && PHASE2_NLP=1 || PHASE2_NLP=0

deploy_function "semantic-search" \
    "semantic_search" \
    "Semantic search using vector embeddings" \
    1024 60 10 \
    "EMBEDDING_PROVIDER=vertex_ai" && PHASE2_SEARCH=1 || PHASE2_SEARCH=0

deploy_function "create-leads" \
    "create_leads" \
    "Create Salesforce leads from unmatched emails" \
    512 300 5 && PHASE2_LEADS=1 || PHASE2_LEADS=0

deploy_function "enroll-hubspot" \
    "enroll_hubspot" \
    "Enroll contacts in HubSpot sequences" \
    512 300 5 && PHASE2_ENROLL=1 || PHASE2_ENROLL=0

deploy_function "get-hubspot-sequences" \
    "get_hubspot_sequences" \
    "Get available HubSpot sequences" \
    512 60 10 && PHASE2_SEQUENCES=1 || PHASE2_SEQUENCES=0

deploy_function "generate-email-reply" \
    "generate_email_reply" \
    "Generate AI email replies" \
    1024 120 10 \
    "LLM_PROVIDER=vertex_ai" && PHASE2_EMAIL=1 || PHASE2_EMAIL=0

# ============================================================================
# CONFIGURE IAM PERMISSIONS
# ============================================================================

print_header "Configuring IAM Permissions"

print_step "Granting Cloud Scheduler permission to invoke functions"

# Collect successful functions
SUCCESSFUL_FUNCTIONS=()
[ $PHASE1_GMAIL -eq 1 ] && SUCCESSFUL_FUNCTIONS+=("gmail-sync")
[ $PHASE1_SF -eq 1 ] && SUCCESSFUL_FUNCTIONS+=("salesforce-sync")
[ $PHASE1_DIALPAD -eq 1 ] && SUCCESSFUL_FUNCTIONS+=("dialpad-sync")
[ $PHASE1_HUBSPOT -eq 1 ] && SUCCESSFUL_FUNCTIONS+=("hubspot-sync")
[ $PHASE1_ER -eq 1 ] && SUCCESSFUL_FUNCTIONS+=("entity-resolution")
[ $PHASE2_EMBED -eq 1 ] && SUCCESSFUL_FUNCTIONS+=("generate-embeddings")
[ $PHASE2_SCORING -eq 1 ] && SUCCESSFUL_FUNCTIONS+=("account-scoring")
[ $PHASE2_NLP -eq 1 ] && SUCCESSFUL_FUNCTIONS+=("nlp-query")
[ $PHASE2_SEARCH -eq 1 ] && SUCCESSFUL_FUNCTIONS+=("semantic-search")
[ $PHASE2_LEADS -eq 1 ] && SUCCESSFUL_FUNCTIONS+=("create-leads")
[ $PHASE2_ENROLL -eq 1 ] && SUCCESSFUL_FUNCTIONS+=("enroll-hubspot")
[ $PHASE2_SEQUENCES -eq 1 ] && SUCCESSFUL_FUNCTIONS+=("get-hubspot-sequences")
[ $PHASE2_EMAIL -eq 1 ] && SUCCESSFUL_FUNCTIONS+=("generate-email-reply")

for func_name in "${SUCCESSFUL_FUNCTIONS[@]}"; do
    if gcloud functions add-iam-policy-binding "$func_name" \
        --region="$REGION" \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/cloudfunctions.invoker" \
        --project="$PROJECT_ID" 2>/dev/null; then
        echo "  [✓] IAM policy set for $func_name"
    else
        echo "  [⚠] Could not set IAM policy for $func_name"
    fi
done

# Grant public access for web app functions (optional)
print_step "Granting public access for web app functions (if needed)"
PUBLIC_FUNCTIONS=("nlp-query" "get-hubspot-sequences" "semantic-search")
for func_name in "${PUBLIC_FUNCTIONS[@]}"; do
    if [[ " ${SUCCESSFUL_FUNCTIONS[@]} " =~ " ${func_name} " ]]; then
        if gcloud functions add-iam-policy-binding "$func_name" \
            --region="$REGION" \
            --member="allUsers" \
            --role="roles/cloudfunctions.invoker" \
            --project="$PROJECT_ID" 2>/dev/null; then
            echo "  [✓] Public access granted for $func_name"
        else
            echo "  [⚠] Could not grant public access for $func_name"
        fi
    fi
done

# ============================================================================
# DEPLOYMENT SUMMARY
# ============================================================================

print_header "Deployment Summary"

echo "Phase 1 Functions:"
echo "  gmail-sync: $([ $PHASE1_GMAIL -eq 1 ] && echo '✓ Success' || echo '✗ Failed')"
echo "  salesforce-sync: $([ $PHASE1_SF -eq 1 ] && echo '✓ Success' || echo '✗ Failed')"
echo "  dialpad-sync: $([ $PHASE1_DIALPAD -eq 1 ] && echo '✓ Success' || echo '✗ Failed')"
echo "  hubspot-sync: $([ $PHASE1_HUBSPOT -eq 1 ] && echo '✓ Success' || echo '✗ Failed')"
echo "  entity-resolution: $([ $PHASE1_ER -eq 1 ] && echo '✓ Success' || echo '✗ Failed')"

echo ""
echo "Phase 2 Functions:"
echo "  generate-embeddings: $([ $PHASE2_EMBED -eq 1 ] && echo '✓ Success' || echo '✗ Failed')"
echo "  account-scoring: $([ $PHASE2_SCORING -eq 1 ] && echo '✓ Success' || echo '✗ Failed')"
echo "  nlp-query: $([ $PHASE2_NLP -eq 1 ] && echo '✓ Success' || echo '✗ Failed')"
echo "  semantic-search: $([ $PHASE2_SEARCH -eq 1 ] && echo '✓ Success' || echo '✗ Failed')"
echo "  create-leads: $([ $PHASE2_LEADS -eq 1 ] && echo '✓ Success' || echo '✗ Failed')"
echo "  enroll-hubspot: $([ $PHASE2_ENROLL -eq 1 ] && echo '✓ Success' || echo '✗ Failed')"
echo "  get-hubspot-sequences: $([ $PHASE2_SEQUENCES -eq 1 ] && echo '✓ Success' || echo '✗ Failed')"
echo "  generate-email-reply: $([ $PHASE2_EMAIL -eq 1 ] && echo '✓ Success' || echo '✗ Failed')"

PHASE1_SUCCESS=$((PHASE1_GMAIL + PHASE1_SF + PHASE1_DIALPAD + PHASE1_HUBSPOT + PHASE1_ER))
PHASE2_SUCCESS=$((PHASE2_EMBED + PHASE2_SCORING + PHASE2_NLP + PHASE2_SEARCH + PHASE2_LEADS + PHASE2_ENROLL + PHASE2_SEQUENCES + PHASE2_EMAIL))

echo ""
if [ $PHASE1_SUCCESS -eq 5 ] && [ $PHASE2_SUCCESS -eq 8 ]; then
    echo "[✓] All functions deployed successfully!"
    echo ""
    echo "Next Steps:"
    echo "  1. Verify functions: gcloud functions list --gen2 --region=$REGION --project=$PROJECT_ID"
    echo "  2. Test a function: gcloud functions call gmail-sync --gen2 --region=$REGION --project=$PROJECT_ID"
    echo "  3. Create Cloud Scheduler jobs (see CLIENT_DEPLOYMENT_GUIDE.md)"
    echo "  4. Deploy web application (see CLIENT_DEPLOYMENT_GUIDE.md)"
else
    echo "[⚠] Some functions failed to deploy. Review errors above."
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check logs: gcloud functions logs read FUNCTION_NAME --gen2 --region=$REGION --limit=50"
    echo "  2. Verify service account permissions"
    echo "  3. Ensure all required APIs are enabled"
    echo "  4. Check TROUBLESHOOTING.md for common issues"
fi

print_header "Deployment Complete"
