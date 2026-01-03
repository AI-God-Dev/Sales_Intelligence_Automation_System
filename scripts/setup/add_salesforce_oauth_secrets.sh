#!/bin/bash
# Add Salesforce OAuth secrets to Secret Manager
# Interactive script to add Client ID, Client Secret, and Refresh Token

PROJECT_ID="${GCP_PROJECT_ID:-maharani-sales-hub-11-2025}"

echo "=========================================="
echo "Add Salesforce OAuth Secrets"
echo "Project: $PROJECT_ID"
echo "=========================================="
echo ""
echo "You need:"
echo "  1. Salesforce Client ID (Consumer Key from Connected App)"
echo "  2. Salesforce Client Secret (Consumer Secret from Connected App)"
echo "  3. Salesforce Refresh Token (from OAuth flow)"
echo "  4. Salesforce Domain: 'test' for sandbox, 'login' for production"
echo ""

# Check if secrets exist
for secret in salesforce-client-id salesforce-client-secret salesforce-refresh-token; do
    if gcloud secrets describe "$secret" --project=$PROJECT_ID &>/dev/null; then
        echo "  ✅ Secret exists: $secret"
    else
        echo "  ❌ Secret missing: $secret (will create)"
        gcloud secrets create "$secret" --project=$PROJECT_ID 2>/dev/null || true
    fi
done

echo ""
echo "=========================================="
echo "Enter Salesforce OAuth Credentials"
echo "=========================================="

# Get Client ID
read -p "Salesforce Client ID (Consumer Key): " SF_CLIENT_ID
echo -n "$SF_CLIENT_ID" | gcloud secrets versions add salesforce-client-id \
  --data-file=- --project=$PROJECT_ID

# Get Client Secret
read -sp "Salesforce Client Secret (Consumer Secret): " SF_CLIENT_SECRET
echo ""
echo -n "$SF_CLIENT_SECRET" | gcloud secrets versions add salesforce-client-secret \
  --data-file=- --project=$PROJECT_ID

# Get Refresh Token
read -sp "Salesforce Refresh Token: " SF_REFRESH_TOKEN
echo ""
echo -n "$SF_REFRESH_TOKEN" | gcloud secrets versions add salesforce-refresh-token \
  --data-file=- --project=$PROJECT_ID

# Get Domain
read -p "Salesforce Domain (test for sandbox, login for production) [default: test]: " SF_DOMAIN
SF_DOMAIN=${SF_DOMAIN:-test}
echo "Using domain: $SF_DOMAIN"

echo ""
echo "=========================================="
echo "✅ OAuth secrets added successfully!"
echo ""
echo "Note: Set SALESFORCE_DOMAIN=$SF_DOMAIN when deploying the function"
echo "=========================================="

