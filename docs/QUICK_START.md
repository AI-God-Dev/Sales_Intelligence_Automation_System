# Quick Start Guide

This guide provides a quick overview of what information you need to get started with production deployment.

## 🚀 Essential Information Needed

### 1. GCP Project Setup
- **GCP Project ID**: Your Google Cloud project ID
- **Billing Account**: Must be enabled
- **Service Account**: For Cloud Functions execution
- **OAuth Credentials**: For Gmail API access

### 2. API Credentials (Store in Secret Manager)

#### Salesforce
- Username, Password, Security Token
- Connected App credentials (OAuth)

#### Gmail (3 mailboxes)
- OAuth Client ID and Secret
- Refresh tokens for each mailbox:
  - anand@maharaniweddings.com
  - [sales-rep-1]@maharaniweddings.com
  - [sales-rep-2]@maharaniweddings.com

#### Dialpad
- API Key
- User IDs for 3 users

#### HubSpot
- API Key or OAuth tokens

#### LLM Provider (Choose One)
- **Anthropic**: API Key
- **OpenAI**: API Key
- **Vertex AI**: Uses GCP service account

### 3. User Mappings

Map Salesforce User IDs to email addresses:
- Anand: `[sf-user-id]` → `anand@maharaniweddings.com`
- Sales Rep 1: `[sf-user-id]` → `[email]`
- Sales Rep 2: `[sf-user-id]` → `[email]`

### 4. Permissions & Access

- **Google Workspace Admin**: For OAuth consent screen
- **Salesforce Admin**: For API access and permissions
- **GCP Project Owner**: For infrastructure setup

## 📋 Deployment Steps

1. **Review [Deployment Checklist](DEPLOYMENT_CHECKLIST.md)**
   - Complete all required items
   - Gather all credentials

2. **Setup Infrastructure**
   ```bash
   cd infrastructure
   terraform init
   terraform plan
   terraform apply
   ```

3. **Configure Secrets**
   ```bash
   ./scripts/setup_secrets.sh
   # Then add values for each secret
   ```

4. **Deploy Functions**
   ```bash
   ./scripts/deploy_functions.sh
   ```

5. **Create BigQuery Tables**
   ```bash
   # Update project_id in SQL file first
   bq query --use_legacy_sql=false < bigquery/schemas/create_tables.sql
   ```

6. **Run Initial Sync**
   - Gmail: Full historical sync
   - Salesforce: Full sync of all objects
   - Dialpad: Historical call logs

7. **Verify & Monitor**
   - Check ETL runs in BigQuery
   - Verify entity resolution accuracy
   - Set up monitoring alerts

## ⚠️ Important Notes

- **Never commit credentials** to git
- **Use Secret Manager** for all sensitive data
- **Test in staging** before production
- **Monitor costs** and set up billing alerts
- **Review security** settings before going live

## 📚 Full Documentation

- [Deployment Checklist](DEPLOYMENT_CHECKLIST.md) - Complete requirements
- [Credentials Template](CREDENTIALS_TEMPLATE.md) - Template for documenting credentials
- [Deployment Guide](DEPLOYMENT.md) - Detailed deployment steps
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions

## 🆘 Need Help?

1. Check [Troubleshooting Guide](TROUBLESHOOTING.md)
2. Review logs: `gcloud functions logs read FUNCTION_NAME`
3. Check ETL runs: Query `etl_runs` table in BigQuery
4. Open an issue on GitHub

