# HubSpot Private App Setup Guide

Complete step-by-step guide for setting up HubSpot integration with the Sales Intelligence System using a Private App.

## Prerequisites

- HubSpot account (Free, Starter, Professional, or Enterprise)
- Account Owner or Super Admin permissions
- Access to Google Cloud Console and Secret Manager
- GCP project: `maharani-sales-hub-11-2025`

## Step 1: Access HubSpot Settings

1. Log in to your HubSpot account
2. Click the **Settings** icon (gear icon) in the top navigation bar
3. In the left sidebar, navigate to **Integrations** → **Private Apps**

## Step 2: Create Private App

1. **Click "Create a private app"** button (top right)

2. **Basic Information Tab**:
   - **App name**: `Sales Intelligence System`
   - **Description**: `Integration app for syncing sequences and contact data`
   - Click **"Create app"**

## Step 3: Configure Scopes (Permissions)

In the **Scopes** tab, select the following scopes:

### Required Scopes (Minimum)

1. **Contacts**:
   - ✅ `contacts.read` - Read access to contacts
   - Used for: Reading contact information, email addresses, phone numbers for entity resolution

2. **Companies**:
   - ✅ `companies.read` - Read access to companies
   - Used for: Reading company information, account data for matching

3. **Sequences**:
   - ✅ `sequences.read` - Read access to sequences
   - Used for: Reading sequence metadata, enrollment information
   - ✅ `sequences.write` - Write access to sequences
   - Used for: Enrolling contacts in sequences from the web app

### Recommended Additional Scopes

4. **Timeline** (Optional but recommended):
   - ✅ `timeline.read` - Read access to timeline events
   - Used for: Tracking engagement history, activity tracking
   - ✅ `timeline.write` - Write access to timeline events
   - Used for: Creating timeline events, activity logging

### Scope Summary

**Minimum Required**:
```
contacts.read
companies.read
sequences.read
sequences.write
```

**Full Recommended**:
```
contacts.read
companies.read
sequences.read
sequences.write
timeline.read
timeline.write
```

3. After selecting scopes, click **"Save"** at the bottom

## Step 4: Get Access Token

1. After saving, you'll be taken to the app details page
2. Click the **"Show token"** button next to "Access token"
3. **Copy the access token** - it will look like: `pat-na1-xxxxx-xxxxx-xxxxx`
   - **Important**: This token is only shown once. Save it immediately!
   - Format: `pat-[region]-[random-string]`
   - Example: `pat-na1-12345678-90ab-cdef-1234-567890abcdef`

4. **Store this token securely** - you'll need it for Secret Manager

## Step 5: Verify App Configuration

1. **Review App Settings**:
   - Go back to the Private Apps list
   - Click on "Sales Intelligence System"
   - Verify all required scopes are selected
   - Note the App ID (may be useful for troubleshooting)

2. **Test Token** (Optional):
   - You can test the token using curl:
   ```bash
   curl https://api.hubapi.com/contacts/v1/lists/all/contacts/all?count=1 \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```
   - If successful, you'll receive contact data

## Step 6: Store Access Token in Google Secret Manager

Store the HubSpot access token in Google Secret Manager:

```bash
# Set project ID
export PROJECT_ID="maharani-sales-hub-11-2025"

# Store HubSpot access token
echo -n "pat-na1-YOUR_ACCESS_TOKEN" | gcloud secrets versions add hubspot-api-key --data-file=- --project="$PROJECT_ID"
```

**Important Notes**:
- Replace `pat-na1-YOUR_ACCESS_TOKEN` with your actual access token
- The token includes the `pat-na1-` prefix
- Never commit the token to version control

## Step 7: Grant Service Account Access

Ensure the service account can access the secret:

```bash
export PROJECT_ID="maharani-sales-hub-11-2025"
export SERVICE_ACCOUNT="sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com"

gcloud secrets add-iam-policy-binding hubspot-api-key \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor" \
  --project="$PROJECT_ID"
```

## Step 8: Verify HubSpot Data Access

Before deploying, verify the Private App can access required data:

1. **Test Sequences API**:
   ```bash
   curl https://api.hubapi.com/sequences/v3/sequences \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```
   - Should return list of sequences

2. **Test Contacts API**:
   ```bash
   curl https://api.hubapi.com/contacts/v1/lists/all/contacts/all?count=1 \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```
   - Should return contact data

3. **Test Companies API**:
   ```bash
   curl https://api.hubapi.com/companies/v2/companies/paged?limit=1 \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```
   - Should return company data

## Step 9: Test the Integration

1. **Deploy the HubSpot sync function** (if not already deployed):
   ```bash
   gcloud functions deploy hubspot-sync \
     --runtime python311 \
     --trigger-http \
     --region us-central1
   ```

2. **Trigger a test sync**:
   ```bash
   gcloud scheduler jobs run hubspot-sync --location=us-central1
   ```

3. **Check logs**:
   ```bash
   gcloud functions logs read hubspot-sync --limit=50 --region=us-central1
   ```

4. **Verify data in BigQuery**:
   ```bash
   bq query --use_legacy_sql=false \
     "SELECT COUNT(*) as count FROM \`maharani-sales-hub-11-2025.sales_intelligence.hubspot_sequences\`"
   ```

## Step 10: Test Sequence Enrollment (Optional)

If you want to test the sequence enrollment feature:

1. **Get available sequences**:
   ```bash
   curl https://YOUR_CLOUD_FUNCTION_URL/get-hubspot-sequences
   ```

2. **Enroll a contact** (via web app or API):
   - The enrollment function uses the same access token
   - Verify the contact exists in HubSpot
   - Verify the sequence exists and is active

## Troubleshooting

### Common Issues

1. **"401 Unauthorized"**:
   - Verify access token is correct (includes `pat-na1-` prefix)
   - Check token hasn't been revoked
   - Verify token is stored correctly in Secret Manager

2. **"403 Forbidden"**:
   - Check required scopes are selected in Private App
   - Verify the account has access to the requested resources
   - Some features may require specific HubSpot subscription tiers

3. **"429 Too Many Requests"**:
   - HubSpot API rate limits:
     - Free/Starter: 100 requests per 10 seconds
     - Professional: 100 requests per 10 seconds
     - Enterprise: 100 requests per 10 seconds
   - The sync functions implement retry logic with exponential backoff
   - Wait before retrying if you hit rate limits

4. **"404 Not Found"**:
   - Verify the API endpoint is correct
   - Check if the resource (sequence, contact, etc.) exists
   - Some endpoints may require specific HubSpot subscription tiers

5. **"No sequences found"**:
   - Verify sequences exist in HubSpot
   - Check sequences are active
   - Verify `sequences.read` scope is enabled

### Getting Help

- Check Cloud Functions logs for detailed error messages
- Review HubSpot API documentation: https://developers.hubspot.com/docs/api/overview
- Verify token in Secret Manager is correct
- Test API calls manually using curl or Postman
- Check HubSpot API status: https://status.hubspot.com/

## API Rate Limits

HubSpot enforces rate limits on API requests:

- **Rate Limit**: 100 requests per 10 seconds (all tiers)
- **Daily Limit**: Varies by subscription tier
- **Best Practice**: Implement exponential backoff and retry logic

The sync functions in this system implement:
- Exponential backoff on rate limit errors
- Request queuing for large syncs
- Batch processing where possible

## Security Best Practices

1. **Private App vs OAuth**: Private Apps are simpler for server-to-server integration
2. **Least Privilege**: Only grant scopes that are actually needed
3. **Token Security**: Never commit tokens to version control
4. **Token Rotation**: Rotate access tokens periodically (recommended: every 90 days)
5. **Monitor Usage**: Review API usage in HubSpot to detect anomalies
6. **Secure Storage**: Store tokens in Google Secret Manager, not in code

## Token Management

### Rotating Access Tokens

1. Create a new Private App (or regenerate token if supported)
2. Update the token in Secret Manager:
   ```bash
   echo -n "NEW_TOKEN" | gcloud secrets versions add hubspot-api-key --data-file=- --project="$PROJECT_ID"
   ```
3. Test the new token
4. Delete old token/version if needed

### Revoking Access

If you need to revoke access:
1. Go to Settings → Integrations → Private Apps
2. Click on "Sales Intelligence System"
3. Click "Delete app" or "Revoke token"
4. Update Secret Manager with new token

## Next Steps

After completing this setup:
1. Verify all secrets are stored in Secret Manager
2. Test the sync function
3. Verify sequences appear in BigQuery
4. Test sequence enrollment (if needed)
5. Complete the deployment checklist

## Checklist

- [ ] Private App created in HubSpot
- [ ] Required scopes selected (contacts.read, companies.read, sequences.read, sequences.write)
- [ ] Optional scopes selected (timeline.read, timeline.write) if needed
- [ ] Access token copied and saved securely
- [ ] Access token stored in Secret Manager as `hubspot-api-key`
- [ ] Service account granted access to secret
- [ ] API access tested manually (optional)
- [ ] HubSpot sync function deployed
- [ ] Test sync completed successfully
- [ ] Sequences verified in BigQuery
- [ ] Sequence enrollment tested (optional)

## Additional Resources

- [HubSpot Private Apps Documentation](https://developers.hubspot.com/docs/api/working-with-oauth)
- [HubSpot API Reference](https://developers.hubspot.com/docs/api/overview)
- [HubSpot Scopes Documentation](https://developers.hubspot.com/scopes)
- [HUBSPOT_SCOPES.md](HUBSPOT_SCOPES.md) - Detailed scope information

