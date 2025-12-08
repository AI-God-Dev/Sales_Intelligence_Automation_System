#!/bin/bash
# Setup secrets in Google Secret Manager

set -e

PROJECT_ID="${GCP_PROJECT_ID:-maharani-sales-hub-11-2025}"
SERVICE_ACCOUNT="sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com"

echo "Setting up secrets in Secret Manager for project: $PROJECT_ID"

# Create secrets (values should be provided via environment variables or prompts)
secrets=(
  "gmail-oauth-client-id"
  "gmail-oauth-client-secret"
  "salesforce-client-id"
  "salesforce-client-secret"
  "salesforce-username"
  "salesforce-password"
  "salesforce-security-token"
  "salesforce-refresh-token"
  "dialpad-api-key"
  "hubspot-client-id"
  "hubspot-client-secret"
  "hubspot-api-key"
  # Note: OpenAI and Anthropic API keys removed - Vertex AI uses Application Default Credentials (ADC)
)

for secret in "${secrets[@]}"; do
  echo "Creating secret: $secret"
  
  # Check if secret already exists
  if gcloud secrets describe "$secret" --project="$PROJECT_ID" &>/dev/null; then
    echo "Secret $secret already exists. Skipping creation."
  else
    # Create secret (user will need to add value manually)
    echo -n "" | gcloud secrets create "$secret" \
      --data-file=- \
      --project="$PROJECT_ID" \
      --replication-policy="automatic"
    
    echo "Secret $secret created. Please add the value using:"
    echo "  echo -n 'YOUR_VALUE' | gcloud secrets versions add $secret --data-file=- --project=$PROJECT_ID"
  fi
  
  # Grant service account access to secret
  echo "Granting service account access to secret: $secret"
  gcloud secrets add-iam-policy-binding "$secret" \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor" \
    --project="$PROJECT_ID" || echo "Warning: Could not grant access to $secret (may need manual setup)"
done

echo "Secret setup complete!"

