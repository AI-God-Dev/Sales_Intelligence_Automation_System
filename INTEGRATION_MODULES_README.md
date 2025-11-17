# Integration Modules - Implementation Summary

This document summarizes the implementation of all 10 integration requirements.

## ✅ Completed Implementations

### 1. Google Cloud Secret Manager Integration ✅

**File**: `utils/secret_manager.py`

- Securely retrieves secrets from Google Cloud Secret Manager at runtime
- No hardcoded credentials
- Supports all required secrets:
  - `hubspot_access_token`
  - `gmail_oauth_client_id_anand` (and larnie, lia)
  - `salesforce_client_id`
  - `dialpad_api_key`
- Uses environment variables or metadata service for project ID
- Includes helper functions for each secret type

**Usage**:
```python
from utils.secret_manager import get_hubspot_access_token, get_gmail_oauth_credentials

token = get_hubspot_access_token()
creds = get_gmail_oauth_credentials("anand")
```

---

### 2. Gmail API Integration ✅

**File**: `integrations/gmail_oauth.py`

- Retrieves OAuth credentials from Secret Manager for Anand, Larnie, and Lia
- Authenticates with Gmail API using OAuth 2.0
- Fetches latest emails with subject and sender
- Supports multiple users
- Follows security best practices

**Usage**:
```python
from integrations.gmail_oauth import GmailOAuthClient

client = GmailOAuthClient(user="anand")
emails = client.get_latest_emails(max_results=5)
client.print_latest_emails(max_results=5)
```

---

### 3. HubSpot API Integration ✅

**File**: `integrations/hubspot_api.py`

- Retrieves HubSpot API credentials from Secret Manager
- Uses `hubspot_access_token` for authentication
- Implements GET /marketing/v3/emails/events for email engagement data
- Implements POST /automation/v4/actions/enrollments for sequence enrollment
- Only syncs HubSpot-specific data (email engagement, sequences)
- Does NOT sync contacts/companies/deals
- Respects rate limits (150 requests/10 seconds, 500K daily)

**Usage**:
```python
from integrations.hubspot_api import HubSpotAPIClient

client = HubSpotAPIClient()
client.authenticate()
events = client.get_email_engagement_events(limit=100)
client.enroll_in_sequence(contact_id="123", sequence_id="456")
```

---

### 4. Salesforce API Integration ✅

**File**: `integrations/salesforce_oauth.py`

- Retrieves Salesforce OAuth credentials from Secret Manager (client_id, client_secret, refresh_token)
- Authenticates with Salesforce using OAuth 2.0 refresh token flow
- Syncs Accounts, Contacts, Leads, and Opportunities
- Only syncs Salesforce-specific data
- Does NOT sync HubSpot contacts

**Usage**:
```python
from integrations.salesforce_oauth import SalesforceOAuthClient

client = SalesforceOAuthClient()
client.authenticate()
accounts = client.get_accounts(limit=100)
contacts = client.get_contacts(limit=100)
leads = client.get_leads(limit=100)
opportunities = client.get_opportunities(limit=100)
```

---

### 5. Dialpad API Integration ✅

**File**: `integrations/dialpad_api.py`

- Retrieves Dialpad API key from Secret Manager
- Authenticates with Dialpad API
- Fetches call logs with duration, phone numbers, and timestamps
- Retrieves call transcriptions
- Secrets retrieved dynamically at runtime

**Usage**:
```python
from integrations.dialpad_api import DialpadAPIClient

client = DialpadAPIClient()
client.authenticate()
calls = client.get_call_logs(limit=5)
transcription = client.get_call_transcription(call_id="123")
```

---

### 6. Pub/Sub Topic Setup ✅

**File**: `scripts/setup_pubsub.py`

- Creates Pub/Sub topics for ingestion pipelines
- Uses service account (sales-intel-poc-sa) for authentication
- Sets up topics for Gmail, Salesforce, Dialpad, and HubSpot
- Creates subscriptions for event-driven processing
- Provides example of publishing messages

**Usage**:
```bash
python scripts/setup_pubsub.py
```

Or programmatically:
```python
from scripts.setup_pubsub import setup_ingestion_topics, setup_subscriptions

topics = setup_ingestion_topics()
subscriptions = setup_subscriptions()
```

---

### 7. BigQuery Schema Setup ✅

**File**: `scripts/setup_bigquery.py`

- Creates BigQuery tables in `sales_intelligence_dev` dataset
- Uses service account for authentication
- Defines schemas for all data sources:
  - `gmail_messages` - Gmail messages
  - `sf_accounts` - Salesforce accounts
  - `sf_contacts` - Salesforce contacts
  - `sf_leads` - Salesforce leads
  - `sf_opportunities` - Salesforce opportunities
  - `dialpad_calls` - Dialpad call logs
  - `hubspot_sequences` - HubSpot sequences
- Uses BigQuery client libraries for Python

**Usage**:
```bash
python scripts/setup_bigquery.py
```

Or programmatically:
```python
from scripts.setup_bigquery import setup_all_tables

tables = setup_all_tables()
```

---

### 8. Cloud Function Deployment ✅

**File**: `scripts/setup_cloud_functions.py`

- Deploys Cloud Functions for data ingestion
- Uses service account (sales-intel-poc-sa) for authentication
- Deploys functions for Gmail, Salesforce, Dialpad, and HubSpot
- Each function triggered by Pub/Sub events
- No hardcoded sensitive information
- Follows best practices

**Usage**:
```bash
python scripts/setup_cloud_functions.py
```

Or programmatically:
```python
from scripts.setup_cloud_functions import CloudFunctionDeployer

deployer = CloudFunctionDeployer()
results = deployer.deploy_all_functions()
```

---

### 9. Cloud Scheduler Setup ✅

**File**: `scripts/setup_cloud_scheduler.py`

- Creates Cloud Scheduler jobs for automation
- Uses service account for authentication
- Sets up scheduled jobs for all data sources:
  - Gmail: Incremental (hourly) and Full (daily at 2 AM)
  - Salesforce: Incremental (every 6 hours) and Full (weekly)
  - Dialpad: Daily at 1 AM
  - HubSpot: Daily at 4 AM
- Triggers Cloud Functions based on schedule

**Usage**:
```bash
python scripts/setup_cloud_scheduler.py
```

Or programmatically:
```python
from scripts.setup_cloud_scheduler import CloudSchedulerManager

manager = CloudSchedulerManager()
results = manager.setup_all_jobs()
```

---

### 10. IAM Permissions Check ✅

**File**: `scripts/check_iam_permissions.py`

- Checks IAM roles and permissions for service account
- Verifies access to:
  - BigQuery
  - Cloud Functions
  - Secret Manager
  - Pub/Sub
  - Cloud Scheduler
- Provides detailed permission report
- Shows missing roles with instructions to grant them

**Usage**:
```bash
python scripts/check_iam_permissions.py
```

Or programmatically:
```python
from scripts.check_iam_permissions import IAMPermissionChecker

checker = IAMPermissionChecker()
checker.print_permission_report()
```

---

## Project Structure

```
.
├── utils/
│   └── secret_manager.py          # Secret Manager integration
├── integrations/
│   ├── __init__.py
│   ├── gmail_oauth.py             # Gmail API integration
│   ├── hubspot_api.py             # HubSpot API integration
│   ├── salesforce_oauth.py        # Salesforce API integration
│   └── dialpad_api.py             # Dialpad API integration
├── scripts/
│   ├── setup_pubsub.py            # Pub/Sub topic setup
│   ├── setup_bigquery.py          # BigQuery schema setup
│   ├── setup_cloud_functions.py   # Cloud Function deployment
│   ├── setup_cloud_scheduler.py   # Cloud Scheduler setup
│   └── check_iam_permissions.py   # IAM permissions check
├── examples/
│   └── integration_examples.py    # Comprehensive examples
└── docs/
    └── INTEGRATION_GUIDE.md       # Detailed documentation
```

---

## Quick Start

1. **Set up secrets in Google Secret Manager** (see required secrets in Secret Manager section)

2. **Check IAM permissions**:
   ```bash
   python scripts/check_iam_permissions.py
   ```

3. **Set up infrastructure**:
   ```bash
   python scripts/setup_pubsub.py
   python scripts/setup_bigquery.py
   python scripts/setup_cloud_functions.py
   python scripts/setup_cloud_scheduler.py
   ```

4. **Test integrations**:
   ```bash
   python examples/integration_examples.py
   ```

---

## Required Secrets in Secret Manager

Ensure these secrets are created in Google Cloud Secret Manager:

### HubSpot
- `hubspot_access_token`

### Gmail (for each user: anand, larnie, lia)
- `gmail_oauth_client_id_{user}`
- `gmail_oauth_client_secret_{user}`
- `gmail_oauth_refresh_token_{user}`

### Salesforce
- `salesforce_client_id`
- `salesforce_client_secret`
- `salesforce_refresh_token`

### Dialpad
- `dialpad_api_key`

---

## Service Account

All scripts use the service account: `sales-intel-poc-sa@{project_id}.iam.gserviceaccount.com`

Required roles:
- `roles/bigquery.dataEditor`
- `roles/bigquery.jobUser`
- `roles/cloudfunctions.invoker`
- `roles/cloudfunctions.developer`
- `roles/secretmanager.secretAccessor`
- `roles/pubsub.publisher`
- `roles/pubsub.subscriber`
- `roles/cloudscheduler.jobRunner`
- `roles/iam.serviceAccountTokenCreator`

---

## Documentation

For detailed documentation, see:
- `docs/INTEGRATION_GUIDE.md` - Comprehensive integration guide
- `examples/integration_examples.py` - Working code examples

---

## Notes

- All credentials are retrieved dynamically at runtime from Secret Manager
- No hardcoded secrets in any code
- All modules follow security best practices
- Error handling and logging included throughout
- Rate limiting implemented for HubSpot API
- OAuth 2.0 refresh token flow used for Salesforce and Gmail

