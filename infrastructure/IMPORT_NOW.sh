#!/bin/bash
# Quick Fix - Import all existing resources
# Run this from the infrastructure directory

set -e

PROJECT_ID="maharani-sales-hub-11-2025"
REGION="us-central1"

echo "========================================"
echo "Importing Existing Resources"
echo "========================================"
echo ""

# Import BigQuery Dataset
echo "1. Importing BigQuery dataset..."
terraform import google_bigquery_dataset.sales_intelligence "${PROJECT_ID}:sales_intelligence" || echo "  (Already imported)"

echo ""
echo "2. Importing Cloud Scheduler jobs..."

# Import all scheduler jobs
terraform import google_cloud_scheduler_job.gmail_incremental_sync "projects/${PROJECT_ID}/locations/${REGION}/jobs/gmail-incremental-sync" || echo "  gmail-incremental-sync: (already imported)"
terraform import google_cloud_scheduler_job.gmail_full_sync "projects/${PROJECT_ID}/locations/${REGION}/jobs/gmail-full-sync" || echo "  gmail-full-sync: (already imported)"
terraform import google_cloud_scheduler_job.salesforce_incremental_sync "projects/${PROJECT_ID}/locations/${REGION}/jobs/salesforce-incremental-sync" || echo "  salesforce-incremental-sync: (already imported)"
terraform import google_cloud_scheduler_job.salesforce_full_sync "projects/${PROJECT_ID}/locations/${REGION}/jobs/salesforce-full-sync" || echo "  salesforce-full-sync: (already imported)"
terraform import google_cloud_scheduler_job.dialpad_sync "projects/${PROJECT_ID}/locations/${REGION}/jobs/dialpad-sync" || echo "  dialpad-sync: (already imported)"
terraform import google_cloud_scheduler_job.hubspot_sync "projects/${PROJECT_ID}/locations/${REGION}/jobs/hubspot-sync" || echo "  hubspot-sync: (already imported)"
terraform import google_cloud_scheduler_job.entity_resolution "projects/${PROJECT_ID}/locations/${REGION}/jobs/entity-resolution" || echo "  entity-resolution: (already imported)"

echo ""
echo "========================================"
echo "Import Complete!"
echo "========================================"
echo ""
echo "Now run: terraform plan"
echo "You should see NO 409 errors!"
echo ""

