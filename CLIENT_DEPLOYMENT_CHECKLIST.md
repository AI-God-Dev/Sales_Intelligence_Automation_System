# Client Deployment Checklist
## Quick Reference for Deployment

Use this checklist to track your deployment progress. Check off each item as you complete it.

---

## 📋 Pre-Deployment

### Account Access
- [ ] GCP account with billing enabled
- [ ] Google Workspace Admin access (for Gmail)
- [ ] Salesforce Admin access
- [ ] Dialpad Admin access
- [ ] HubSpot Admin access

### Software Installation
- [ ] Google Cloud SDK (`gcloud`) installed
- [ ] Python 3.11+ installed
- [ ] Git installed

### Credentials Gathered
- [ ] GCP Project ID: `_________________`
- [ ] Salesforce credentials (username, password, security token)
- [ ] Salesforce Connected App (client ID, client secret)
- [ ] Dialpad API key
- [ ] HubSpot Private App access token
- [ ] Gmail OAuth credentials (client ID, client secret)
- [ ] LLM API key (if not using Vertex AI)

---

## 🚀 Step 1: GCP Project Setup

- [ ] GCP project created or selected
- [ ] Project ID set: `gcloud config set project YOUR_PROJECT_ID`
- [ ] Billing enabled
- [ ] Environment variables set:
  - [ ] `GCP_PROJECT_ID`
  - [ ] `GCP_REGION`
  - [ ] `BIGQUERY_DATASET`

---

## 👤 Step 2: Service Account

- [ ] Service account created: `sales-intelligence-sa`
- [ ] Roles granted:
  - [ ] BigQuery Data Editor
  - [ ] BigQuery Job User
  - [ ] Vertex AI User
  - [ ] Secret Manager Secret Accessor
  - [ ] Cloud Functions Invoker
  - [ ] Cloud Run Invoker
  - [ ] Logging Log Writer
  - [ ] Pub/Sub Publisher
- [ ] Your user account granted:
  - [ ] Service Account User
  - [ ] Cloud Functions Admin
  - [ ] Cloud Run Admin
  - [ ] Secret Manager Admin

---

## 🔌 Step 3: Enable APIs

- [ ] Cloud Functions API
- [ ] Cloud Run API
- [ ] Cloud Build API
- [ ] Cloud Scheduler API
- [ ] BigQuery API
- [ ] Secret Manager API
- [ ] Cloud Storage API
- [ ] Vertex AI API
- [ ] Pub/Sub API
- [ ] Gmail API
- [ ] IAM API
- [ ] Logging API
- [ ] Monitoring API

---

## 💾 Step 4: BigQuery Setup

- [ ] Dataset created: `sales_intelligence`
- [ ] Tables created (13 tables):
  - [ ] gmail_messages
  - [ ] gmail_participants
  - [ ] sf_accounts
  - [ ] sf_contacts
  - [ ] sf_opportunities
  - [ ] sf_activities
  - [ ] dialpad_calls
  - [ ] email_matches
  - [ ] phone_matches
  - [ ] account_recommendations
  - [ ] hubspot_sequences
  - [ ] etl_runs
  - [ ] unmatched_emails_view

---

## 🔐 Step 5: Secret Manager

- [ ] Secrets created (run `.\scripts\setup_secrets.ps1`):
  - [ ] salesforce-client-id
  - [ ] salesforce-client-secret
  - [ ] salesforce-username
  - [ ] salesforce-password
  - [ ] salesforce-security-token
  - [ ] salesforce-refresh-token
  - [ ] salesforce-instance-url
  - [ ] dialpad-api-key
  - [ ] hubspot-api-key
  - [ ] openai-api-key (optional)
  - [ ] anthropic-api-key (optional)
- [ ] Secret values added
- [ ] Service account access granted to all secrets

---

## 📧 Step 6: Gmail OAuth Setup

- [ ] OAuth credentials created in GCP Console
- [ ] Client ID obtained: `_________________`
- [ ] Client Secret obtained: `_________________`
- [ ] Environment variables set:
  - [ ] `GMAIL_OAUTH_CLIENT_ID`
  - [ ] `GMAIL_OAUTH_CLIENT_SECRET`
- [ ] Domain-Wide Delegation configured
- [ ] OAuth scopes granted

---

## 🔧 Step 7: Update Configuration

- [ ] `config/config.py` updated with your project ID
- [ ] Gmail mailboxes updated in config
- [ ] Deployment scripts updated:
  - [ ] `scripts/deploy_functions.ps1`
  - [ ] `scripts/deploy_phase2_functions.ps1`
- [ ] BigQuery SQL files updated (replace project ID)

---

## 📦 Step 8: Deploy Phase 1 Functions

- [ ] gmail-sync deployed
- [ ] salesforce-sync deployed
- [ ] dialpad-sync deployed
- [ ] hubspot-sync deployed
- [ ] entity-resolution deployed
- [ ] All functions tested

---

## 🧠 Step 9: Deploy Phase 2 Functions

- [ ] generate-embeddings deployed
- [ ] account-scoring deployed (2048MB memory)
- [ ] nlp-query deployed
- [ ] semantic-search deployed
- [ ] create-leads deployed
- [ ] enroll-hubspot deployed
- [ ] get-hubspot-sequences deployed
- [ ] generate-email-reply deployed
- [ ] All functions tested

---

## 🌐 Step 10: Deploy Web Application

- [ ] Web app deployed to Cloud Run OR
- [ ] Web app running locally
- [ ] Web app accessible
- [ ] Authentication working
- [ ] All pages loading correctly

---

## ⏰ Step 11: Cloud Scheduler

- [ ] account-scoring-daily (7 AM)
- [ ] generate-embeddings-daily (8 AM)
- [ ] gmail-sync-hourly
- [ ] salesforce-sync-daily (2 AM)
- [ ] dialpad-sync-daily
- [ ] All jobs tested manually

---

## ✅ Step 12: Testing & Verification

### Data Ingestion
- [ ] Gmail sync tested and working
- [ ] Salesforce sync tested and working
- [ ] Dialpad sync tested and working
- [ ] HubSpot sync tested and working
- [ ] Data visible in BigQuery

### Intelligence Functions
- [ ] Account scoring tested (with limit)
- [ ] Embeddings generation tested
- [ ] NLP query tested
- [ ] Semantic search tested
- [ ] Results visible in BigQuery

### Web Application
- [ ] Dashboard loads
- [ ] Account Scoring page works
- [ ] Natural Language Query works
- [ ] Semantic Search works
- [ ] All features functional

---

## 📊 Step 13: Data Verification

- [ ] Accounts in `sf_accounts` table
- [ ] Contacts in `sf_contacts` table
- [ ] Emails in `gmail_messages` table
- [ ] Calls in `dialpad_calls` table
- [ ] Account scores in `account_recommendations` table
- [ ] ETL runs logged in `etl_runs` table

---

## 🔍 Step 14: Monitoring Setup

- [ ] Cloud Functions logs accessible
- [ ] BigQuery usage monitoring enabled
- [ ] Cost alerts configured
- [ ] Error notifications set up (Pub/Sub)

---

## 📝 Notes

**Project ID**: `_________________`
**Region**: `_________________`
**Service Account**: `_________________`
**Web App URL**: `_________________`

**Deployment Date**: `_________________`
**Deployed By**: `_________________`

---

## ⚠️ Issues Encountered

1. _________________________________________________
2. _________________________________________________
3. _________________________________________________

---

## ✅ Final Sign-Off

- [ ] All functions deployed and tested
- [ ] Data syncing correctly
- [ ] Web application working
- [ ] Documentation reviewed
- [ ] Team trained on system

**Deployment Complete**: ☐ Yes  ☐ No

**Date Completed**: `_________________`

