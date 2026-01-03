#!/bin/bash
# Check Cloud Functions deployment status and active operations

# Don't use set -e, handle errors gracefully

PROJECT_ID="${GCP_PROJECT_ID:-maharani-sales-hub-11-2025}"
REGION="${GCP_REGION:-us-central1}"

echo "Checking deployment status for project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Check active Cloud Build operations
echo "=== Active Cloud Build Operations ==="
if gcloud builds list --ongoing --project=$PROJECT_ID --region=$REGION --limit=10 --format="table(id,status,createTime,source.repoSource.branchName)" 2>/dev/null | grep -q .; then
    gcloud builds list --ongoing --project=$PROJECT_ID --region=$REGION --limit=10 --format="table(id,status,createTime,source.repoSource.branchName)" 2>/dev/null
else
    echo "No active builds found"
fi
echo ""

# Check Cloud Functions status
echo "=== Cloud Functions Status ==="
if gcloud functions list --region=$REGION --project=$PROJECT_ID --gen2 --format="table(name,state,updateTime)" 2>/dev/null | grep -q .; then
    gcloud functions list --region=$REGION --project=$PROJECT_ID --gen2 --format="table(name,state,updateTime)" 2>/dev/null
else
    echo "No functions found"
fi
echo ""

# Check Cloud Run services (Gen2 functions run as Cloud Run)
echo "=== Cloud Run Services Status ==="
if gcloud run services list --region=$REGION --project=$PROJECT_ID --format="table(metadata.name,status.conditions[0].type,status.conditions[0].status)" 2>/dev/null | grep -q .; then
    gcloud run services list --region=$REGION --project=$PROJECT_ID --format="table(metadata.name,status.conditions[0].type,status.conditions[0].status)" 2>/dev/null
else
    echo "No Cloud Run services found"
fi
echo ""

echo "If you see active builds above, wait for them to complete before deploying again."
