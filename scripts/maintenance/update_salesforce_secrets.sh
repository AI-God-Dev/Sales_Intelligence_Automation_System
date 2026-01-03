#!/bin/bash
# Update Salesforce secrets in Secret Manager
# Interactive script to update credentials

PROJECT_ID="${GCP_PROJECT_ID:-maharani-sales-hub-11-2025}"

echo "=========================================="
echo "Update Salesforce Secrets in Secret Manager"
echo "Project: $PROJECT_ID"
echo "=========================================="
echo ""
echo "This script will update Salesforce credentials."
echo "You need:"
echo "  1. Salesforce username"
echo "  2. Salesforce password"
echo "  3. Salesforce security token (get from email if reset)"
echo ""
read -p "Continue? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Check if secrets exist
echo ""
echo "Checking existing secrets..."
for secret in salesforce-username salesforce-password salesforce-security-token; do
    if gcloud secrets describe "$secret" --project=$PROJECT_ID &>/dev/null; then
        echo "  ✅ Secret exists: $secret"
    else
        echo "  ❌ Secret missing: $secret (will create)"
        # Create secret if it doesn't exist
        gcloud secrets create "$secret" --project=$PROJECT_ID 2>/dev/null || true
    fi
done

echo ""
echo "=========================================="
echo "Enter Salesforce Credentials"
echo "=========================================="

# Get username
read -p "Salesforce Username (email): " SF_USERNAME
echo -n "$SF_USERNAME" | gcloud secrets versions add salesforce-username \
  --data-file=- --project=$PROJECT_ID

# Get password
read -sp "Salesforce Password: " SF_PASSWORD
echo ""
echo -n "$SF_PASSWORD" | gcloud secrets versions add salesforce-password \
  --data-file=- --project=$PROJECT_ID

# Get security token
read -sp "Salesforce Security Token (or press Enter to skip if not reset): " SF_TOKEN
echo ""
if [ ! -z "$SF_TOKEN" ]; then
    echo -n "$SF_TOKEN" | gcloud secrets versions add salesforce-security-token \
      --data-file=- --project=$PROJECT_ID
    echo "✅ Security token updated"
else
    echo "⚠️  Security token not updated (using existing)"
fi

echo ""
echo "=========================================="
echo "✅ Secrets updated successfully!"
echo ""
echo "Next steps:"
echo "  1. Verify credentials are correct"
echo "  2. Retry Salesforce sync"
echo "  3. Check logs if still failing"
echo "=========================================="

