#!/bin/bash
# Grant Cloud Functions Invoker role to current user for manual testing

PROJECT_ID="${GCP_PROJECT_ID:-maharani-sales-hub-11-2025}"
REGION="${GCP_REGION:-us-central1}"

# Get current user email
USER_EMAIL=$(gcloud config get-value account)
if [ -z "$USER_EMAIL" ]; then
    echo "Error: No user logged in. Please run: gcloud auth login"
    exit 1
fi

echo "Granting Cloud Functions Invoker role to: $USER_EMAIL"
echo "Project: $PROJECT_ID"
echo ""

# List of functions
FUNCTIONS=("gmail-sync" "salesforce-sync" "dialpad-sync" "hubspot-sync" "entity-resolution")

for FUNCTION_NAME in "${FUNCTIONS[@]}"; do
    echo "Granting permission to invoke: $FUNCTION_NAME..."
    gcloud functions add-iam-policy-binding $FUNCTION_NAME \
        --region=$REGION \
        --member="user:$USER_EMAIL" \
        --role="roles/cloudfunctions.invoker" \
        --project=$PROJECT_ID
    
    if [ $? -eq 0 ]; then
        echo "  ✓ Successfully granted permission to $FUNCTION_NAME"
    else
        echo "  ✗ Failed to grant permission to $FUNCTION_NAME"
    fi
    echo ""
done

echo "Done! You can now invoke the functions using your user account."

