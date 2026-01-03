#!/bin/bash
# Check if Salesforce secrets exist in Secret Manager

PROJECT_ID="${GCP_PROJECT_ID:-maharani-sales-hub-11-2025}"

echo "Checking Salesforce secrets in Secret Manager..."
echo "Project: $PROJECT_ID"
echo ""

REQUIRED_SECRETS=(
    "salesforce-username"
    "salesforce-password"
    "salesforce-security-token"
)

MISSING_SECRETS=()

for secret in "${REQUIRED_SECRETS[@]}"; do
    echo "Checking: $secret"
    if gcloud secrets describe "$secret" --project=$PROJECT_ID &>/dev/null; then
        echo "  ✅ Secret exists: $secret"
    else
        echo "  ❌ Secret missing: $secret"
        MISSING_SECRETS+=("$secret")
    fi
done

echo ""
echo "----------------------------------------"

if [ ${#MISSING_SECRETS[@]} -eq 0 ]; then
    echo "✅ All Salesforce secrets exist!"
    echo ""
    echo "If you're still getting errors, check the logs:"
    echo "bash scripts/check_salesforce_sync_errors.sh"
else
    echo "❌ Missing secrets: ${MISSING_SECRETS[*]}"
    echo ""
    echo "To add missing secrets, run:"
    echo ""
    for secret in "${MISSING_SECRETS[@]}"; do
        echo "echo -n 'YOUR_VALUE' | gcloud secrets create $secret --data-file=- --project=$PROJECT_ID"
    done
    echo ""
    echo "Or grant access if secrets exist but service account can't access:"
    echo "gcloud secrets add-iam-policy-binding SECRET_NAME \\"
    echo "  --member=\"serviceAccount:sales-intel-poc-sa@${PROJECT_ID}.iam.gserviceaccount.com\" \\"
    echo "  --role=\"roles/secretmanager.secretAccessor\" \\"
    echo "  --project=$PROJECT_ID"
fi

