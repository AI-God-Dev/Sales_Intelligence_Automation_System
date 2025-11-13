# Production Deployment Checklist

This document outlines all the information, credentials, and configurations needed to deploy and run the Sales Intelligence & Automation System in a real-world production environment.

## 🔐 Required Credentials & API Keys

### 1. Google Cloud Platform (GCP)

#### Project Information
- [ ] **GCP Project ID**: `your-project-id`
  - Must have billing enabled
  - Must have appropriate quotas
  - Location: GCP Console → Project Settings

#### Service Account Credentials
- [ ] **Service Account JSON Key File**
  - Required for Cloud Functions execution
  - Must have roles: BigQuery Data Editor, Secret Manager Secret Accessor, Log Writer, Monitoring Metric Writer
  - Location: IAM & Admin → Service Accounts → Create/Download Key

#### OAuth 2.0 Credentials (for Gmail)
- [ ] **OAuth Client ID**: `xxxxx.apps.googleusercontent.com`
- [ ] **OAuth Client Secret**: `xxxxx`
- [ ] **Authorized Redirect URIs**: Configured in Google Cloud Console
- [ ] **OAuth Consent Screen**: Configured with required scopes
  - Required scope: `https://www.googleapis.com/auth/gmail.readonly`
  - Location: APIs & Services → Credentials → OAuth 2.0 Client IDs

#### Gmail Mailbox Access
- [ ] **Mailbox 1 Email**: `anand@maharaniweddings.com`
  - OAuth token/refresh token for this mailbox
- [ ] **Mailbox 2 Email**: `[sales-rep-1]@maharaniweddings.com`
  - OAuth token/refresh token for this mailbox
- [ ] **Mailbox 3 Email**: `[sales-rep-2]@maharaniweddings.com`
  - OAuth token/refresh token for this mailbox

**Note**: Each mailbox needs to authorize the OAuth application. The system will need refresh tokens stored securely.

### 2. Salesforce

#### API Credentials
- [ ] **Username**: Salesforce login username
- [ ] **Password**: Salesforce login password
- [ ] **Security Token**: Salesforce security token (reset password to get new token)
- [ ] **Domain**: `login` (production) or `test` (sandbox)
- [ ] **Instance URL**: `https://yourinstance.salesforce.com` (optional, auto-detected)

#### Connected App Configuration
- [ ] **Consumer Key**: OAuth Consumer Key from Connected App
- [ ] **Consumer Secret**: OAuth Consumer Secret from Connected App
- [ ] **Callback URL**: Configured in Salesforce Connected App
- [ ] **OAuth Scopes**: 
  - `api`
  - `refresh_token`
  - `offline_access`

#### Object Permissions
Verify the following Salesforce objects are accessible:
- [ ] Accounts (Read)
- [ ] Contacts (Read)
- [ ] Leads (Read, Create)
- [ ] Opportunities (Read)
- [ ] Tasks (Read, Create)
- [ ] Events (Read, Create)
- [ ] EmailMessage (Read)

#### IP Whitelisting (if required)
- [ ] **GCP Function IPs**: May need to whitelist if Salesforce has IP restrictions
  - Check with Salesforce admin

### 3. Dialpad

#### API Credentials
- [ ] **API Key**: Dialpad API key
  - Location: Dialpad Admin → Integrations → API
- [ ] **API Base URL**: `https://dialpad.com/api/v2` (default)
- [ ] **User IDs**: List of Dialpad user IDs to sync
  - User 1: `[user-id-1]` (Anand)
  - User 2: `[user-id-2]` (Sales Rep 1)
  - User 3: `[user-id-3]` (Sales Rep 2)

#### Plan Requirements
- [ ] **API Plan**: Verify plan includes:
  - Call logs API access
  - Call transcripts API access (if available)
  - AI sentiment analysis (if available)

### 4. HubSpot

#### API Credentials
- [ ] **API Key**: HubSpot Private App API Key
  - Location: HubSpot → Settings → Integrations → Private Apps
- [ ] **OAuth Access Token**: (Alternative to API key)
- [ ] **OAuth Refresh Token**: (If using OAuth)

#### Required Scopes
- [ ] **Sequences API**: Read and write access to sequences
- [ ] **Contacts API**: Read access to contacts
- [ ] **Enrollment API**: Write access to enroll contacts in sequences

### 5. LLM Provider (Choose One)

#### Option A: Anthropic Claude
- [ ] **API Key**: Anthropic API key
  - Location: Anthropic Console → API Keys
- [ ] **Model**: `claude-3-5-sonnet-20241022` (default)
- [ ] **Organization ID**: (if applicable)

#### Option B: OpenAI
- [ ] **API Key**: OpenAI API key
  - Location: OpenAI Platform → API Keys
- [ ] **Organization ID**: (optional)
- [ ] **Model**: `gpt-4` or `gpt-3.5-turbo`
- [ ] **Embedding Model**: `text-embedding-3-small`

#### Option C: Google Vertex AI
- [ ] **Service Account**: GCP Service Account with Vertex AI permissions
- [ ] **Project ID**: Same as GCP project
- [ ] **Region**: `us-central1` (or preferred region)
- [ ] **Model**: Vertex AI model endpoint

## 📋 Configuration Information

### Environment Variables

Create a `.env` file or set in deployment environment:

```bash
# GCP Configuration
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1
BIGQUERY_DATASET=sales_intelligence

# Salesforce Configuration
SALESFORCE_DOMAIN=login  # or 'test' for sandbox

# LLM Configuration
LLM_PROVIDER=anthropic  # or 'openai' or 'vertex_ai'
LLM_MODEL=claude-3-5-sonnet-20241022
EMBEDDING_MODEL=text-embedding-3-small

# Gmail OAuth (for initial setup)
GMAIL_OAUTH_CLIENT_ID=xxxxx.apps.googleusercontent.com
GMAIL_OAUTH_CLIENT_SECRET=xxxxx

# Sync Intervals
GMAIL_SYNC_INTERVAL_MINUTES=60
SALESFORCE_SYNC_INTERVAL_HOURS=24
DIALPAD_SYNC_INTERVAL_HOURS=24

# Data Quality Targets
EMAIL_MATCH_TARGET_PERCENTAGE=90.0
CALL_MATCH_TARGET_PERCENTAGE=85.0
HUBSPOT_ENROLLMENT_SUCCESS_TARGET=98.0

# Query Configuration
MAX_QUERY_RESULTS=100
QUERY_TIMEOUT_SECONDS=30

# Data Retention
DATA_RETENTION_YEARS=3
```

### Secret Manager Setup

All sensitive credentials should be stored in Google Secret Manager:

```bash
# Required Secrets (add via gcloud CLI or Console)
gcloud secrets create salesforce-username
gcloud secrets create salesforce-password
gcloud secrets create salesforce-security-token
gcloud secrets create dialpad-api-key
gcloud secrets create hubspot-api-key
gcloud secrets create openai-api-key
gcloud secrets create anthropic-api-key
```

## 🏗️ Infrastructure Requirements

### GCP Services to Enable

- [ ] **Cloud Functions API**: `cloudfunctions.googleapis.com`
- [ ] **Cloud Run API**: `run.googleapis.com`
- [ ] **Cloud Scheduler API**: `cloudscheduler.googleapis.com`
- [ ] **BigQuery API**: `bigquery.googleapis.com`
- [ ] **Secret Manager API**: `secretmanager.googleapis.com`
- [ ] **Cloud Logging API**: `logging.googleapis.com`
- [ ] **Cloud Monitoring API**: `monitoring.googleapis.com`
- [ ] **Cloud Storage API**: `storage.googleapis.com` (for function source)

### Resource Quotas

Verify/Request the following quotas:
- [ ] **Cloud Functions**: 
  - Concurrent executions: 100+ (default: 80)
  - Function invocations per day: Sufficient for your volume
- [ ] **BigQuery**:
  - Query slots: 200+ (default: 200)
  - Daily query quota: Sufficient for your queries
  - Storage: Plan for data growth
- [ ] **Gmail API**:
  - Quota units per day: 1 billion (default)
  - Requests per 100 seconds per user: 250
- [ ] **Cloud Scheduler**:
  - Jobs per project: 500+ (default: 500)

### Network Configuration

- [ ] **VPC**: (Optional) Configure VPC connector if needed
- [ ] **Firewall Rules**: Allow outbound HTTPS (443) for API calls
- [ ] **Private IP**: (Optional) Configure if using VPC

## 👥 User Access & Permissions

### Google Workspace

- [ ] **Domain**: `maharaniweddings.com`
- [ ] **Admin Access**: For OAuth consent screen approval
- [ ] **User Consent**: Each Gmail user must authorize the application

### Salesforce Users

- [ ] **Integration User**: Dedicated Salesforce user for API access
  - Username: `integration@maharaniweddings.com`
  - Profile: System Administrator or Custom Profile with required permissions
- [ ] **Sales Rep Users**: Map to Salesforce User IDs for personalization
  - User 1: `[sf-user-id-1]` → Anand
  - User 2: `[sf-user-id-2]` → Sales Rep 1
  - User 3: `[sf-user-id-3]` → Sales Rep 2

### Application Users

- [ ] **Web App Access**: List of Google Workspace emails allowed to access the web app
  - Must be in `maharaniweddings.com` domain
  - Configured in OAuth consent screen

## 📊 Initial Data Requirements

### Historical Data Sync

- [ ] **Gmail Historical Sync**: 
  - Date range: `[start-date]` to `[end-date]`
  - Estimated message count: `[number]`
  - Expected sync time: `[hours]`

- [ ] **Salesforce Historical Sync**:
  - Full sync of all objects (Account, Contact, Lead, Opportunity, Task, Event)
  - Estimated record counts per object
  - Expected sync time: `[hours]`

- [ ] **Dialpad Historical Sync**:
  - Date range: `[start-date]` to `[end-date]`
  - Estimated call count: `[number]`
  - Expected sync time: `[hours]`

### Data Validation

- [ ] **Sample Data Review**: Review sample records after initial sync
- [ ] **Entity Resolution Validation**: Verify match accuracy with known contacts
- [ ] **Data Quality Check**: Verify completeness and accuracy

## 🔔 Monitoring & Alerting

### Alert Configuration

Set up alerts for:
- [ ] **ETL Job Failures**: Alert when ETL runs fail
- [ ] **High Error Rates**: Alert when error rate > 5%
- [ ] **Low Match Accuracy**: Alert when match accuracy < 85%
- [ ] **API Quota Warnings**: Alert at 80% of quota
- [ ] **Function Timeouts**: Alert on function timeouts
- [ ] **BigQuery Query Failures**: Alert on query errors
- [ ] **Cost Alerts**: Alert at $500, $750, $1000 monthly spend

### Monitoring Dashboards

- [ ] **ETL Performance Dashboard**: Track sync times and success rates
- [ ] **Data Quality Dashboard**: Track match accuracy and data completeness
- [ ] **API Usage Dashboard**: Track API calls and quota usage
- [ ] **Cost Dashboard**: Track GCP spending by service

## 🔄 Operational Procedures

### Backup & Recovery

- [ ] **BigQuery Backups**: 
  - Daily snapshots configured
  - Retention policy: 30 days
- [ ] **Terraform State**: 
  - Stored in GCS bucket
  - Versioning enabled
- [ ] **Secret Backups**: 
  - Documented secret locations
  - Recovery procedures documented

### Disaster Recovery Plan

- [ ] **Recovery Time Objective (RTO)**: `[hours]`
- [ ] **Recovery Point Objective (RPO)**: `[hours]`
- [ ] **Backup Restoration Procedures**: Documented and tested
- [ ] **Failover Procedures**: Documented

### Maintenance Windows

- [ ] **Scheduled Maintenance**: `[day/time]`
- [ ] **Update Procedures**: Documented
- [ ] **Rollback Procedures**: Documented and tested

## 📝 Legal & Compliance

### Data Privacy

- [ ] **Data Processing Agreement**: Signed with all vendors
- [ ] **Privacy Policy**: Updated to include data processing
- [ ] **User Consent**: Obtained for data processing
- [ ] **Data Retention Policy**: Documented and implemented

### Compliance Requirements

- [ ] **GDPR Compliance**: (if applicable)
  - Right to deletion implemented
  - Data export functionality
- [ ] **CCPA Compliance**: (if applicable)
  - Consumer rights implemented
- [ ] **SOC 2**: (if required)
  - Controls documented
  - Audits scheduled

## 🧪 Testing Requirements

### Pre-Production Testing

- [ ] **Unit Tests**: All tests passing
- [ ] **Integration Tests**: All tests passing
- [ ] **End-to-End Tests**: Critical paths tested
- [ ] **Load Testing**: System tested under expected load
- [ ] **Security Testing**: Security scan passed
- [ ] **UAT**: User acceptance testing completed

### Staging Environment

- [ ] **Staging GCP Project**: Created and configured
- [ ] **Staging Data**: Sample data loaded
- [ ] **Staging Tests**: All functionality verified

## 📞 Support & Escalation

### Contact Information

- [ ] **Primary Contact**: `[name]` - `[email]` - `[phone]`
- [ ] **Technical Lead**: `[name]` - `[email]` - `[phone]`
- [ ] **Salesforce Admin**: `[name]` - `[email]` - `[phone]`
- [ ] **GCP Support**: Support plan level: `[Basic/Standard/Premium]`
- [ ] **Vendor Support Contacts**:
  - Salesforce Support: `[contact]`
  - Dialpad Support: `[contact]`
  - HubSpot Support: `[contact]`

### Escalation Procedures

- [ ] **Level 1**: Documented
- [ ] **Level 2**: Documented
- [ ] **Level 3**: Documented
- [ ] **On-Call Rotation**: Established

## ✅ Pre-Launch Checklist

Before going live, verify:

- [ ] All credentials configured in Secret Manager
- [ ] All APIs enabled in GCP
- [ ] All Cloud Functions deployed and tested
- [ ] Cloud Scheduler jobs created and tested
- [ ] BigQuery tables created and schema validated
- [ ] Initial data sync completed successfully
- [ ] Entity resolution accuracy verified (>90%)
- [ ] Monitoring and alerting configured
- [ ] Documentation reviewed and updated
- [ ] Team trained on system operation
- [ ] Backup and recovery procedures tested
- [ ] Security review completed
- [ ] Performance benchmarks met
- [ ] UAT sign-off received

## 📚 Additional Resources

- [GCP Setup Guide](SETUP.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [API Documentation](API.md)
- [Architecture Documentation](ARCHITECTURE.md)

---

**Last Updated**: [Date]
**Version**: 1.0
**Maintained By**: [Team/Contact]

