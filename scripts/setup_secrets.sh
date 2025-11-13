#!/bin/bash
# Setup secrets in Google Secret Manager

set -e

PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"

echo "Setting up secrets in Secret Manager for project: $PROJECT_ID"

# Create secrets (values should be provided via environment variables or prompts)
secrets=(
  "salesforce-username"
  "salesforce-password"
  "salesforce-security-token"
  "dialpad-api-key"
  "hubspot-api-key"
  "openai-api-key"
  "anthropic-api-key"
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
done

echo "Secret setup complete!"

