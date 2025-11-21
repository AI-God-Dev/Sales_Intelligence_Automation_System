# Fix Salesforce Credentials Error

## Error Message
```
INVALID_LOGIN: Invalid username, password, security token; or user locked out.
```

## Causes
1. **Wrong credentials** in Secret Manager
2. **Security token expired/changed** (Salesforce resets tokens when password changes)
3. **User locked out** (too many failed login attempts)
4. **Credentials format** (extra spaces, wrong encoding)

## Solution Steps

### Step 1: Verify Secrets Exist

```bash
# Check if secrets exist
gcloud secrets list --project=maharani-sales-hub-11-2025 | grep salesforce

# Check secret values (will show if they exist, but not the values)
gcloud secrets describe salesforce-username --project=maharani-sales-hub-11-2025
gcloud secrets describe salesforce-password --project=maharani-sales-hub-11-2025
gcloud secrets describe salesforce-security-token --project=maharani-sales-hub-11-2025
```

### Step 2: Get New Security Token (If Needed)

**If password was changed, you need a new security token:**

1. Go to Salesforce: https://login.salesforce.com
2. Login with your Salesforce account
3. Click your profile icon → **Settings** → **My Personal Information** → **Reset My Security Token**
4. Click **Reset Security Token** button
5. Check your email for the new security token

### Step 3: Update Secrets in Secret Manager

**Replace old values with correct ones:**

```bash
PROJECT_ID="maharani-sales-hub-11-2025"

# Update username (replace YOUR_USERNAME with actual username)
echo -n "YOUR_USERNAME@example.com" | gcloud secrets versions add salesforce-username \
  --data-file=- --project=$PROJECT_ID

# Update password (replace YOUR_PASSWORD with actual password)
echo -n "YOUR_PASSWORD" | gcloud secrets versions add salesforce-password \
  --data-file=- --project=$PROJECT_ID

# Update security token (replace YOUR_TOKEN with new security token from email)
echo -n "YOUR_SECURITY_TOKEN" | gcloud secrets versions add salesforce-security-token \
  --data-file=- --project=$PROJECT_ID
```

### Step 4: Verify Secrets Are Accessible

```bash
# Check if service account can access secrets
gcloud secrets get-iam-policy salesforce-username --project=$PROJECT_ID
```

### Step 5: Test Salesforce Connection Locally (Optional)

Before retrying the sync, test credentials:

```python
from simple_salesforce import Salesforce

sf = Salesforce(
    username='YOUR_USERNAME',
    password='YOUR_PASSWORD',
    security_token='YOUR_TOKEN',
    domain='login'  # or 'test' for sandbox
)

# Test query
results = sf.query("SELECT Id, Name FROM Account LIMIT 1")
print(results)
```

### Step 6: Retry Sync

After updating credentials:

```bash
TOKEN=$(gcloud auth print-identity-token)

curl -X POST \
  "https://us-central1-maharani-sales-hub-11-2025.cloudfunctions.net/salesforce-sync" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"sync_type":"full","object_type":"Account"}'
```

## Common Issues

1. **Security token resets automatically** when password changes
2. **Username must be exact** - check for typos
3. **Password must be exact** - no extra spaces
4. **Domain setting** - use `login` for production, `test` for sandbox
5. **User permissions** - ensure user has API access enabled

## Check Salesforce User Status

1. Login to Salesforce as admin
2. Go to Setup → Users → Users
3. Find the user and check:
   - Is user **Active**?
   - Is user **Locked Out**? (Unlock if yes)
   - Does user have **API Enabled** permission?

