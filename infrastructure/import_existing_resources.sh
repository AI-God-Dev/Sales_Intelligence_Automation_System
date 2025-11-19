#!/bin/bash
# Script to import existing GCP resources into Terraform state
# Run this if you get 409 errors saying resources already exist

set -e

PROJECT_ID="${GCP_PROJECT_ID:-maharani-sales-hub-11-2025}"
REGION="${GCP_REGION:-us-central1}"

echo "========================================"
echo "Importing Existing Resources to Terraform"
echo "========================================"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

cd "$(dirname "$0")"

# Check if terraform is initialized
if [ ! -d ".terraform" ]; then
    echo "Error: Terraform not initialized. Run 'terraform init' first."
    exit 1
fi

# Import BigQuery Dataset
echo "1. Importing BigQuery dataset..."
terraform import google_bigquery_dataset.sales_intelligence "$PROJECT_ID:sales_intelligence" 2>/dev/null || echo "  (Already imported or doesn't exist)"

# Import Cloud Scheduler Jobs
echo ""
echo "2. Importing Cloud Scheduler jobs..."
JOBS=(
    "gmail-incremental-sync"
    "gmail-full-sync"
    "salesforce-incremental-sync"
    "salesforce-full-sync"
    "dialpad-sync"
    "hubspot-sync"
    "entity-resolution"
)

for job in "${JOBS[@]}"; do
    echo "  Importing $job..."
    RESOURCE_NAME=$(echo "$job" | tr '-' '_')
    terraform import "google_cloud_scheduler_job.${RESOURCE_NAME}" "projects/$PROJECT_ID/locations/$REGION/jobs/$job" 2>/dev/null || echo "    (Already imported or doesn't exist)"
done

# Import Pub/Sub Topics (if they exist)
echo ""
echo "3. Importing Pub/Sub topics (if they exist)..."
TOPICS=(
    "gmail-ingestion"
    "salesforce-ingestion"
    "dialpad-ingestion"
    "hubspot-ingestion"
    "ingestion-errors"
)

for topic in "${TOPICS[@]}"; do
    echo "  Importing $topic..."
    RESOURCE_NAME=$(echo "$topic" | tr '-' '_')
    terraform import "google_pubsub_topic.${RESOURCE_NAME}" "projects/$PROJECT_ID/topics/$topic" 2>/dev/null || echo "    (Already imported or doesn't exist)"
done

echo ""
echo "========================================"
echo "Import complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Run 'terraform plan' to see if there are any differences"
echo "2. If needed, run 'terraform apply' to sync any differences"
echo ""

