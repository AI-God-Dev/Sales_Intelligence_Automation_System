# Salesforce Sandbox Setup Guide

Complete step-by-step guide for setting up Salesforce sandbox integration with the Sales Intelligence System.

## Prerequisites

- Access to Salesforce sandbox org
- System Administrator permissions in Salesforce
- Access to Google Cloud Console and Secret Manager
- GCP project: `maharani-sales-hub-11-2025`

## Step 1: Access Your Salesforce Sandbox

1. Log in to your Salesforce sandbox org
   - URL format: `https://test.salesforce.com` or `https://[your-instance].sandbox.my.salesforce.com`
   - Note: Sandbox uses `test` domain, not `login` domain

2. Verify you have System Administrator access
   - Go to Setup (gear icon → Setup)
   - Check your profile/permission set

## Step 2: Create Integration User (Recommended)

For security best practices, create a dedicated integration user:

1. **Create User**:
   - Go to Setup → Users → Users
   - Click "New User"
   - Fill in required fields:
     - First Name: `Integration`
     - Last Name: `API User`
     - Email: `integration@maharaniweddings.com` (or your domain)
     - Username: `integration@maharaniweddings.com.sandbox` (note the `.sandbox` suffix)
     - Profile: System Administrator (or create custom profile with API access)
   - Uncheck "Generate new password and notify user via email"
   - Set a secure password (you'll need this for Secret Manager)
   - Click "Save"

2. **Reset Security Token**:
   - Log in as the integration user (or use "Login As" feature)
   - Go to Setup → My Personal Information → Reset My Security Token
   - Click "Reset Security Token"
   - Check the email for the security token (or it will be displayed)
   - **Save this token** - you'll need it for Secret Manager

3. **Note User ID**:
   - From the user record, note the User ID (18-character ID)
   - This may be useful for troubleshooting

## Step 3: Create Connected App

The Connected App provides OAuth credentials for API access:

1. **Navigate to Connected Apps**:
   - Go to Setup → App Manager
   - Click "New Connected App" (top right)

2. **Basic Information**:
   - Connected App Name: `Sales Intelligence System`
   - API Name: `Sales_Intelligence_System` (auto-generated)
   - Contact Email: Your email address
   - Description: `Integration app for Sales Intelligence System data sync`

3. **API (Enable OAuth Settings)**:
   - Check "Enable OAuth Settings"
   - Callback URL: `https://oauth.pstmn.io/v1/callback` (for testing) or `https://localhost:8080/oauth/callback`
   - Selected OAuth Scopes: Add the following:
     - `Access and manage your data (api)`
     - `Perform requests on your behalf at any time (refresh_token, offline_access)`
     - `Access the identity URL service (id, profile, email, address, phone)`
   - Click "Save"

4. **Get Credentials**:
   - After saving, you'll see the Connected App details
   - **Consumer Key** (Client ID): Copy this value
   - **Consumer Secret** (Client Secret): Click "Click to reveal" and copy
   - **Important**: Save both values securely - you'll need them for Secret Manager

5. **Manage Connected App**:
   - Click "Manage" next to the Connected App
   - Under "OAuth Policies":
     - Permitted Users: `Admin approved users are pre-authorized`
     - IP Relaxation: `Relax IP restrictions` (or configure specific IPs if needed)
   - Under "Manage Policies":
     - Session timeout: `2 hours` (or as needed)
   - Click "Save"

6. **Pre-authorize Integration User**:
   - Still in the Connected App management page
   - Go to "Manage Profiles" or "Manage Permission Sets"
   - Add the integration user's profile (or create a permission set and assign it)
   - This allows the user to use the Connected App without manual approval

## Step 4: Verify API Access

1. **Enable API Access for User**:
   - Go to Setup → Users → Users
   - Click on the integration user
   - Verify the profile has "API Enabled" permission
   - If not, either:
     - Use System Administrator profile, OR
     - Create a custom profile with "API Enabled" permission

2. **Test API Connection** (Optional):
   - You can test the connection using Postman or curl:
   ```bash
   curl https://test.salesforce.com/services/oauth2/token \
     -d "grant_type=password" \
     -d "client_id=YOUR_CONSUMER_KEY" \
     -d "client_secret=YOUR_CONSUMER_SECRET" \
     -d "username=YOUR_USERNAME" \
     -d "password=YOUR_PASSWORD+SECURITY_TOKEN"
   ```
   - If successful, you'll receive an access token

## Step 5: Store Credentials in Google Secret Manager

Store all Salesforce credentials in Google Secret Manager:

```bash
# Set project ID
export PROJECT_ID="maharani-sales-hub-11-2025"

# Store Salesforce credentials
echo -n "YOUR_CONSUMER_KEY" | gcloud secrets versions add salesforce-client-id --data-file=- --project="$PROJECT_ID"
echo -n "YOUR_CONSUMER_SECRET" | gcloud secrets versions add salesforce-client-secret --data-file=- --project="$PROJECT_ID"
echo -n "integration@maharaniweddings.com.sandbox" | gcloud secrets versions add salesforce-username --data-file=- --project="$PROJECT_ID"
echo -n "YOUR_PASSWORD" | gcloud secrets versions add salesforce-password --data-file=- --project="$PROJECT_ID"
echo -n "YOUR_SECURITY_TOKEN" | gcloud secrets versions add salesforce-security-token --data-file=- --project="$PROJECT_ID"

# Note: Refresh token is optional if using username/password authentication
# If you complete OAuth flow, store the refresh token:
# echo -n "YOUR_REFRESH_TOKEN" | gcloud secrets versions add salesforce-refresh-token --data-file=- --project="$PROJECT_ID"
```

**Important Notes**:
- Replace `YOUR_CONSUMER_KEY`, `YOUR_CONSUMER_SECRET`, etc. with actual values
- For sandbox, username typically ends with `.sandbox`
- Security token is required when IP restrictions are enabled
- Password + Security Token are concatenated for authentication

## Step 6: Configure Environment Variable

Set the Salesforce domain to `test` for sandbox:

1. **In Cloud Functions** (if deploying):
   - Set environment variable: `SALESFORCE_DOMAIN=test`
   - Or update `config/config.py` default to `test` for sandbox

2. **In Local Development**:
   - Create/update `.env` file:
   ```bash
   SALESFORCE_DOMAIN=test
   ```

## Step 7: Verify Required Objects and Fields

Ensure the following objects are accessible and have required fields:

1. **Account**:
   - Name, Id, Email, Phone, Website, CreatedDate, LastModifiedDate

2. **Contact**:
   - FirstName, LastName, Email, Phone, AccountId, CreatedDate, LastModifiedDate

3. **Lead**:
   - FirstName, LastName, Email, Phone, Company, Status, CreatedDate, LastModifiedDate

4. **Opportunity**:
   - Name, AccountId, StageName, Amount, CloseDate, CreatedDate, LastModifiedDate

5. **Task**:
   - Subject, WhoId, WhatId, ActivityDate, Status, CreatedDate, LastModifiedDate

6. **Event**:
   - Subject, WhoId, WhatId, StartDateTime, EndDateTime, CreatedDate, LastModifiedDate

7. **EmailMessage**:
   - FromAddress, ToAddress, Subject, TextBody, HtmlBody, CreatedDate

**Note**: Some objects may require field-level security adjustments. Verify the integration user can read these fields.

## Step 8: Test the Integration

1. **Deploy the Salesforce sync function** (if not already deployed):
   ```bash
   gcloud functions deploy salesforce-sync \
     --runtime python311 \
     --trigger-http \
     --region us-central1 \
     --set-env-vars SALESFORCE_DOMAIN=test
   ```

2. **Trigger a test sync**:
   ```bash
   gcloud scheduler jobs run salesforce-incremental-sync --location=us-central1
   ```

3. **Check logs**:
   ```bash
   gcloud functions logs read salesforce-sync --limit=50 --region=us-central1
   ```

4. **Verify data in BigQuery**:
   ```bash
   bq query --use_legacy_sql=false \
     "SELECT COUNT(*) as count FROM \`maharani-sales-hub-11-2025.sales_intelligence.sf_accounts\`"
   ```

## Troubleshooting

### Common Issues

1. **"INVALID_LOGIN: Invalid username, password, security token"**:
   - Verify username includes `.sandbox` suffix
   - Check password is correct
   - Verify security token is correct (reset if needed)
   - Ensure password + security token are concatenated correctly

2. **"INVALID_CLIENT: Invalid client credentials"**:
   - Verify Consumer Key and Consumer Secret are correct
   - Check Connected App is active
   - Verify OAuth settings are enabled

3. **"INSUFFICIENT_ACCESS: Insufficient access rights"**:
   - Verify integration user has API Enabled permission
   - Check profile/permission set has access to required objects
   - Verify Connected App is pre-authorized for the user

4. **"API_DISABLED_FOR_ORG"**:
   - API access may be disabled for the org
   - Contact Salesforce support to enable API access

5. **"REQUEST_LIMIT_EXCEEDED"**:
   - You've exceeded API request limits
   - Wait before retrying
   - Consider implementing rate limiting in sync function

### Getting Help

- Check Cloud Functions logs for detailed error messages
- Review Salesforce API documentation: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/
- Verify credentials in Secret Manager are correct
- Test API connection manually using curl or Postman

## Security Best Practices

1. **Use Integration User**: Never use a real user account for API access
2. **Least Privilege**: Grant only necessary permissions to integration user
3. **IP Restrictions**: Consider restricting Connected App to specific IPs in production
4. **Rotate Credentials**: Regularly rotate passwords and security tokens
5. **Monitor Access**: Review login history and API usage regularly
6. **Secure Storage**: Never commit credentials to version control

## Next Steps

After completing this setup:
1. Verify all secrets are stored in Secret Manager
2. Test the sync function
3. Verify data appears in BigQuery
4. Proceed with HubSpot setup (see [HUBSPOT_SETUP.md](HUBSPOT_SETUP.md))
5. Complete the deployment checklist

## Checklist

- [ ] Integration user created
- [ ] Security token obtained for integration user
- [ ] Connected App created with OAuth settings
- [ ] Consumer Key and Consumer Secret copied
- [ ] Integration user pre-authorized for Connected App
- [ ] API access enabled for integration user
- [ ] All credentials stored in Secret Manager
- [ ] Environment variable `SALESFORCE_DOMAIN=test` configured
- [ ] Test sync completed successfully
- [ ] Data verified in BigQuery

