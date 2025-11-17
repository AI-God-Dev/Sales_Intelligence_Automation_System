# Integration Guide

This guide provides comprehensive documentation for all integration modules and setup scripts.

## Table of Contents

1. [Secret Manager Integration](#secret-manager-integration)
2. [Gmail API Integration](#gmail-api-integration)
3. [HubSpot API Integration](#hubspot-api-integration)
4. [Salesforce API Integration](#salesforce-api-integration)
5. [Dialpad API Integration](#dialpad-api-integration)
6. [Pub/Sub Setup](#pubsub-setup)
7. [BigQuery Schema Setup](#bigquery-schema-setup)
8. [Cloud Function Deployment](#cloud-function-deployment)
9. [Cloud Scheduler Setup](#cloud-scheduler-setup)
10. [IAM Permissions Check](#iam-permissions-check)

---

## Secret Manager Integration

### Overview

The Secret Manager integration securely retrieves API credentials from Google Cloud Secret Manager at runtime. No credentials are hardcoded in the code.

### Required Secrets

The following secrets must be stored in Google Secret Manager:

- `hubspot_access_token` - HubSpot API access token
- `gmail_oauth_client_id_anand` - Gmail OAuth client ID for Anand
- `gmail_oauth_client_secret_anand` - Gmail OAuth client secret for Anand
- `gmail_oauth_refresh_token_anand` - Gmail OAuth refresh token for Anand
- `gmail_oauth_client_id_larnie` - Gmail OAuth client ID for Larnie
- `gmail_oauth_client_secret_larnie` - Gmail OAuth client secret for Larnie
- `gmail_oauth_refresh_token_larnie` - Gmail OAuth refresh token for Larnie
- `gmail_oauth_client_id_lia` - Gmail OAuth client ID for Lia
- `gmail_oauth_client_secret_lia` - Gmail OAuth client secret for Lia
- `gmail_oauth_refresh_token_lia` - Gmail OAuth refresh token for Lia
- `salesforce_client_id` - Salesforce OAuth client ID
- `salesforce_client_secret` - Salesforce OAuth client secret
- `salesforce_refresh_token` - Salesforce OAuth refresh token
- `dialpad_api_key` - Dialpad API key

### Usage

```python
from utils.secret_manager import (
    get_hubspot_access_token,
    get_gmail_oauth_credentials,
    get_salesforce_credentials,
    get_dialpad_api_key
)

# Retrieve HubSpot access token
hubspot_token = get_hubspot_access_token()

# Retrieve Gmail OAuth credentials for a user
gmail_creds = get_gmail_oauth_credentials("anand")  # or "larnie", "lia"

# Retrieve Salesforce credentials
sf_creds = get_salesforce_credentials()

# Retrieve Dialpad API key
dialpad_key = get_dialpad_api_key()
```

### Example

See `examples/integration_examples.py` for complete examples.

---

## Gmail API Integration

### Overview

Integrates with Gmail API using OAuth 2.0 credentials stored in Secret Manager. Supports multiple users: Anand, Larnie, and Lia.

### Features

- Retrieves OAuth credentials from Secret Manager
- Authenticates with Gmail API using OAuth 2.0
- Fetches latest emails with subject and sender information
- Supports multiple users

### Usage

```python
from integrations.gmail_oauth import GmailOAuthClient

# Initialize client for a user
client = GmailOAuthClient(user="anand")  # or "larnie", "lia"

# Authenticate (automatic on first API call)
client.authenticate()

# Fetch latest 5 emails
emails = client.get_latest_emails(max_results=5)

# Print emails
client.print_latest_emails(max_results=5)
```

### Example Output

```
=== Latest 5 Emails for ANAND ===

Email 1:
  Subject: Meeting Request
  From: john@example.com
  Date: Mon, 1 Jan 2024 10:00:00 -0500
  Snippet: Hi, I'd like to schedule a meeting...
```

---

## HubSpot API Integration

### Overview

Interacts with HubSpot API to retrieve email engagement data and manage sequence enrollments. Only syncs HubSpot-specific data (email engagement, sequences), not contacts/companies/deals.

### Features

- Retrieves HubSpot access token from Secret Manager
- Fetches email engagement events using GET /marketing/v3/emails/events
- Implements sequence enrollment using POST /automation/v4/actions/enrollments
- Respects rate limits (150 requests/10 seconds, 500K daily)

### Usage

```python
from integrations.hubspot_api import HubSpotAPIClient

# Initialize client
client = HubSpotAPIClient()
client.authenticate()

# Get email engagement events
events = client.get_email_engagement_events(limit=100)

# Enroll a contact in a sequence
enrollment = client.enroll_in_sequence(
    contact_id="12345",
    sequence_id="67890"
)

# Get available sequences
sequences = client.get_sequences(limit=100)
```

### Rate Limiting

The client automatically enforces HubSpot rate limits:
- 150 requests per 10 seconds
- 500,000 requests per day

---

## Salesforce API Integration

### Overview

Connects to Salesforce using OAuth 2.0 credentials from Secret Manager. Syncs only Salesforce-specific data: Accounts, Contacts, Leads, and Opportunities.

### Features

- Retrieves OAuth credentials from Secret Manager
- Authenticates with Salesforce using refresh token flow
- Syncs Accounts, Contacts, Leads, and Opportunities
- Does NOT sync HubSpot contacts

### Usage

```python
from integrations.salesforce_oauth import SalesforceOAuthClient

# Initialize client
client = SalesforceOAuthClient()
client.authenticate()

# Fetch accounts
accounts = client.get_accounts(limit=100)
for account in accounts:
    print(f"Account: {account.get('Name')}")
    print(f"Annual Revenue: ${account.get('AnnualRevenue', 0):,.2f}")

# Fetch contacts
contacts = client.get_contacts(limit=100)

# Fetch leads
leads = client.get_leads(limit=100)

# Fetch opportunities
opportunities = client.get_opportunities(limit=100)
```

### Example Output

```
Account 1:
  Account Name: Acme Corporation
  Annual Revenue: $1,000,000.00
  Industry: Technology
  Website: https://acme.com
```

---

## Dialpad API Integration

### Overview

Integrates with Dialpad API to retrieve call logs and transcriptions using API key from Secret Manager.

### Features

- Retrieves Dialpad API key from Secret Manager
- Fetches call logs with duration, phone numbers, and timestamps
- Retrieves call transcriptions

### Usage

```python
from integrations.dialpad_api import DialpadAPIClient

# Initialize client
client = DialpadAPIClient()
client.authenticate()

# Fetch call logs
calls = client.get_call_logs(limit=5)

for call in calls:
    print(f"From: {call.get('from_number')}")
    print(f"To: {call.get('to_number')}")
    print(f"Duration: {call.get('duration_seconds')} seconds")
    print(f"Call Time: {call.get('start_time')}")

# Get transcription for a specific call
transcription = client.get_call_transcription(call_id="12345")
```

### Example Output

```
Call 1:
  From: +1234567890
  To: +0987654321
  Duration: 300 seconds
  Call Time: 2024-01-01T10:00:00Z
  Transcript: Hello, this is a test call...
```

---

## Pub/Sub Setup

### Overview

Creates and manages Pub/Sub topics for event-driven data ingestion pipelines.

### Usage

```python
from scripts.setup_pubsub import setup_ingestion_topics, setup_subscriptions

# Set up topics
topics = setup_ingestion_topics()

# Set up subscriptions
subscriptions = setup_subscriptions()
```

### Command Line

```bash
python scripts/setup_pubsub.py
```

### Created Topics

- `gmail-ingestion` - Gmail data ingestion
- `salesforce-ingestion` - Salesforce data ingestion
- `dialpad-ingestion` - Dialpad data ingestion
- `hubspot-ingestion` - HubSpot data ingestion

---

## BigQuery Schema Setup

### Overview

Creates BigQuery tables for storing data from all sources in the `sales_intelligence_dev` dataset.

### Usage

```python
from scripts.setup_bigquery import setup_all_tables

# Set up all tables
tables = setup_all_tables()
```

### Command Line

```bash
python scripts/setup_bigquery.py
```

### Created Tables

- `gmail_messages` - Gmail messages
- `sf_accounts` - Salesforce accounts
- `sf_contacts` - Salesforce contacts
- `sf_leads` - Salesforce leads
- `sf_opportunities` - Salesforce opportunities
- `dialpad_calls` - Dialpad call logs
- `hubspot_sequences` - HubSpot sequences

---

## Cloud Function Deployment

### Overview

Deploys Cloud Functions for data ingestion from all sources. Uses service account `sales-intel-poc-sa` for authentication.

### Usage

```python
from scripts.setup_cloud_functions import CloudFunctionDeployer

# Initialize deployer
deployer = CloudFunctionDeployer()

# Deploy all functions
results = deployer.deploy_all_functions()
```

### Command Line

```bash
python scripts/setup_cloud_functions.py
```

### Deployed Functions

- `gmail-sync` - Gmail data sync
- `salesforce-sync` - Salesforce data sync
- `dialpad-sync` - Dialpad data sync
- `hubspot-sync` - HubSpot data sync

---

## Cloud Scheduler Setup

### Overview

Creates Cloud Scheduler jobs for automating ingestion pipeline execution.

### Usage

```python
from scripts.setup_cloud_scheduler import CloudSchedulerManager

# Initialize manager
manager = CloudSchedulerManager()

# Set up all jobs
results = manager.setup_all_jobs()
```

### Command Line

```bash
python scripts/setup_cloud_scheduler.py
```

### Created Jobs

- `gmail-incremental-sync` - Every hour
- `gmail-full-sync` - Daily at 2 AM
- `salesforce-incremental-sync` - Every 6 hours
- `salesforce-full-sync` - Weekly on Sunday at 3 AM
- `dialpad-sync` - Daily at 1 AM
- `hubspot-sync` - Daily at 4 AM

---

## IAM Permissions Check

### Overview

Checks IAM roles and permissions for the service account to ensure it has necessary access to all required services.

### Usage

```python
from scripts.check_iam_permissions import IAMPermissionChecker

# Initialize checker
checker = IAMPermissionChecker()

# Print permission report
checker.print_permission_report()
```

### Command Line

```bash
python scripts/check_iam_permissions.py
```

### Required Roles

- **BigQuery**: `roles/bigquery.dataEditor`, `roles/bigquery.jobUser`
- **Cloud Functions**: `roles/cloudfunctions.invoker`, `roles/cloudfunctions.developer`
- **Secret Manager**: `roles/secretmanager.secretAccessor`
- **Pub/Sub**: `roles/pubsub.publisher`, `roles/pubsub.subscriber`
- **Cloud Scheduler**: `roles/cloudscheduler.jobRunner`, `roles/iam.serviceAccountTokenCreator`

---

## Quick Start

1. **Set up secrets in Secret Manager** (see required secrets above)

2. **Check IAM permissions**:
   ```bash
   python scripts/check_iam_permissions.py
   ```

3. **Set up Pub/Sub topics**:
   ```bash
   python scripts/setup_pubsub.py
   ```

4. **Set up BigQuery tables**:
   ```bash
   python scripts/setup_bigquery.py
   ```

5. **Deploy Cloud Functions**:
   ```bash
   python scripts/setup_cloud_functions.py
   ```

6. **Set up Cloud Scheduler jobs**:
   ```bash
   python scripts/setup_cloud_scheduler.py
   ```

7. **Test integrations**:
   ```bash
   python examples/integration_examples.py
   ```

---

## Troubleshooting

### Common Issues

1. **Secret not found**: Ensure all secrets are created in Secret Manager with correct names
2. **Permission denied**: Run `check_iam_permissions.py` to verify service account has required roles
3. **Authentication failed**: Verify OAuth credentials are correct and refresh tokens are valid
4. **Rate limit exceeded**: HubSpot client automatically handles rate limiting, but check daily limits

### Getting Help

- Check logs in Cloud Logging
- Review error messages in Cloud Functions
- Verify service account permissions
- Test individual integrations using example scripts

