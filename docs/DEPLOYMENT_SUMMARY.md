# Deployment Summary - Sales Intelligence System

This document summarizes all the components created for the 10 deployment tasks.

## Task 1: Pub/Sub Topics ✅

**File**: `infrastructure/pubsub.tf`

Created Pub/Sub topics and subscriptions for each ingestion pipeline:
- `gmail-ingestion` - Gmail data ingestion topic
- `salesforce-ingestion` - Salesforce data ingestion topic
- `dialpad-ingestion` - Dialpad data ingestion topic
- `hubspot-ingestion` - HubSpot data ingestion topic
- `ingestion-errors` - Central error notification topic

Each topic includes:
- Dead letter queues (DLQ) for failed messages
- Error subscriptions with retry policies
- IAM permissions for service account

## Task 2: Cloud Scheduler Jobs ✅

**File**: `infrastructure/scheduler.tf`

Created automated Cloud Scheduler jobs:
- **Gmail Incremental Sync**: Every hour (`0 * * * *`)
- **Gmail Full Sync**: Daily at 2 AM (`0 2 * * *`)
- **Salesforce Incremental Sync**: Every 6 hours (`0 */6 * * *`)
- **Salesforce Full Sync**: Weekly on Sunday at 3 AM (`0 3 * * 0`)
- **Dialpad Sync**: Daily at 1 AM (`0 1 * * *`)
- **HubSpot Sync**: Daily at 4 AM (`0 4 * * *`)
- **Entity Resolution**: Every 4 hours (`0 */4 * * *`)

All jobs include:
- Retry configuration with exponential backoff
- OIDC token authentication using service account
- Error handling and monitoring

## Task 3: Cloud Functions Deployment ✅

**File**: `scripts/deploy_functions.sh`

Updated deployment script to use service account:
- Service account: `sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com`
- All functions deployed with service account impersonation
- IAM bindings for Cloud Scheduler to invoke functions
- Environment variables for project configuration

Functions deployed:
- `gmail-sync`
- `salesforce-sync`
- `dialpad-sync`
- `hubspot-sync`

## Task 4: BigQuery Schemas ✅

**File**: `bigquery/schemas/create_tables.sql`

Enhanced BigQuery schema with:
- All 12 core tables (Gmail, Salesforce, Dialpad, HubSpot)
- Gmail sync state table for incremental sync tracking
- Proper partitioning and clustering
- Data types optimized for ingestion and querying
- Views for unmatched emails

## Task 5: HubSpot OAuth Scopes ✅

**File**: `docs/HUBSPOT_SCOPES.md`

Documented required HubSpot OAuth scopes:
- `contacts.read` - Read contacts
- `companies.read` - Read companies
- `sequences.read` - Read sequences
- `sequences.write` - Enroll in sequences
- Optional: `timeline.read`, `timeline.write`

Includes Private App creation steps and security notes.

## Task 6: Secrets List ✅

**File**: `docs/SECRETS_LIST.md`

Comprehensive list of all secrets needed:
- Gmail: OAuth client ID/secret
- Salesforce: Client ID/secret, username/password, security token, refresh token
- Dialpad: API key
- HubSpot: API key (Private App token)
- LLM: OpenAI and Anthropic API keys

Includes:
- Secret creation commands
- IAM permission setup
- Security best practices
- Placeholder values for development

## Task 7: Gmail Domain-Wide Delegation ✅

**Files**: 
- `cloud_functions/gmail_sync/gmail_dwd.py`
- `cloud_functions/gmail_sync/main.py` (updated)

Implemented Gmail sync using domain-wide delegation:
- No user OAuth tokens required
- Service account impersonates users
- Supports multiple mailboxes
- Incremental sync using history ID tracking
- Full sync with pagination
- Automatic participant extraction

## Task 8: Entity Resolution Logic ✅

**Files**:
- `entity_resolution/matcher.py` (enhanced)
- `cloud_functions/entity_resolution/main.py` (new)

Enhanced entity resolution with:
- Email-to-contact matching (exact, fuzzy, manual)
- Phone-to-contact matching (exact, fuzzy, manual)
- Batch processing for participants and calls
- MERGE statements for efficient BigQuery updates
- Match confidence tracking (exact, fuzzy, manual)

## Task 9: Automated Tests ✅

**Files**:
- `tests/test_gmail_sync.py`
- `tests/test_salesforce_sync.py`
- `tests/test_entity_resolution.py`
- `tests/test_integration.py`

Comprehensive test suite:
- Unit tests for individual functions
- Integration tests for end-to-end flows
- Mock-based testing for external APIs
- Error handling tests
- Data transformation tests

## Task 10: Error Handling and Monitoring ✅

**Files**:
- `utils/monitoring.py` (enhanced)
- Updated all sync functions with error handling

Implemented:
- Pub/Sub error notifications
- Performance monitoring with context managers
- Health check endpoints
- Structured error logging
- Metrics collection (counters, gauges, histograms)
- Automatic error publishing on failures

## Infrastructure Updates

**Files**:
- `infrastructure/main.tf` - Updated with service account references
- `infrastructure/outputs.tf` - Updated outputs

## Deployment Steps

1. **Deploy Infrastructure**:
   ```bash
   cd infrastructure
   terraform init
   terraform plan
   terraform apply
   ```

2. **Setup Secrets**:
   ```bash
   ./scripts/setup_secrets.sh
   # Then add secret values using gcloud commands
   ```

3. **Deploy Cloud Functions**:
   ```bash
   ./scripts/deploy_functions.sh
   ```

4. **Create BigQuery Tables**:
   ```bash
   # Replace {project_id} in create_tables.sql
   bq query --use_legacy_sql=false < bigquery/schemas/create_tables.sql
   ```

5. **Enable Domain-Wide Delegation**:
   - In Google Workspace Admin Console
   - Grant the service account the required scopes
   - Authorize the OAuth client ID for domain-wide delegation

6. **Run Tests**:
   ```bash
   pytest tests/ -v
   ```

## Service Account Configuration

The service account `sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com` requires:
- BigQuery Data Editor role
- Secret Manager Secret Accessor role
- Cloud Functions Invoker role
- Pub/Sub Publisher/Subscriber roles
- Logging Writer role
- Monitoring Metric Writer role

## Next Steps

1. Configure Gmail domain-wide delegation in Google Workspace
2. Add actual secret values to Secret Manager
3. Deploy infrastructure using Terraform
4. Deploy Cloud Functions
5. Create BigQuery tables
6. Test each ingestion pipeline
7. Monitor error notifications in Pub/Sub
8. Set up Cloud Monitoring dashboards

## Monitoring

- Error notifications: `ingestion-errors` Pub/Sub topic
- ETL run tracking: `etl_runs` BigQuery table
- Cloud Monitoring: Custom metrics via MetricsCollector
- Cloud Logging: Structured logs from all functions

## Support

For issues or questions:
1. Check Cloud Logging for function errors
2. Review Pub/Sub error notifications
3. Check BigQuery `etl_runs` table for job status
4. Review test results for validation

