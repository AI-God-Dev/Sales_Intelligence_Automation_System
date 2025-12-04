# Complete List of Cloud Functions to Deploy

## 📋 Overview

This document lists all Cloud Functions that need to be deployed, their configurations, and deployment status.

---

## Phase 1: Data Ingestion Functions (✅ Already Deployed)

| Function Name | Entry Point | Memory | Timeout | Status |
|--------------|-------------|--------|---------|--------|
| `gmail-sync` | `cloud_functions.gmail_sync.main.gmail_sync` | 512MB | 540s | ✅ Deployed |
| `salesforce-sync` | `cloud_functions.salesforce_sync.main.salesforce_sync` | 512MB | 540s | ✅ Deployed |
| `dialpad-sync` | `cloud_functions.dialpad_sync.main.dialpad_sync` | 512MB | 540s | ✅ Deployed |
| `hubspot-sync` | `cloud_functions.hubspot_sync.main.hubspot_sync` | 512MB | 540s | ✅ Deployed |
| `entity-resolution` | `cloud_functions.entity_resolution.main.entity_resolution` | 512MB | 540s | ✅ Deployed |

**Deployment Script**: `scripts/deploy_functions.ps1`

---

## Phase 2: Intelligence & Automation Functions (⏳ Need Deployment)

### 1. **generate-embeddings**
- **Entry Point**: `generate_embeddings` (from `intelligence.embeddings.main`)
- **Memory**: 1024MB
- **Timeout**: 540s
- **Max Instances**: 5
- **Environment Variables**: 
  - `GCP_PROJECT_ID=maharani-sales-hub-11-2025`
  - `GCP_REGION=us-central1`
  - `LLM_PROVIDER=vertex_ai`
  - `EMBEDDING_PROVIDER=vertex_ai`
- **Description**: Generates vector embeddings for emails and call transcripts
- **Status**: ❌ Not Deployed

### 2. **account-scoring**
- **Entry Point**: `account_scoring_job` (from `intelligence.scoring.main`)
- **Memory**: 2048MB ⚠️ (Currently 512MB - needs update)
- **Timeout**: 540s
- **Max Instances**: 3
- **Environment Variables**:
  - `GCP_PROJECT_ID=maharani-sales-hub-11-2025`
  - `GCP_REGION=us-central1`
  - `LLM_PROVIDER=vertex_ai`
- **Description**: Daily AI-powered account scoring using LLM
- **Status**: ⚠️ Deployed but needs memory increase

### 3. **nlp-query**
- **Entry Point**: `nlp_query` (from `intelligence.nlp_query.main`)
- **Memory**: 1024MB
- **Timeout**: 60s
- **Max Instances**: 10
- **Environment Variables**:
  - `GCP_PROJECT_ID=maharani-sales-hub-11-2025`
  - `GCP_REGION=us-central1`
  - `LLM_PROVIDER=vertex_ai`
- **Description**: Convert natural language questions to BigQuery SQL
- **Status**: ❌ Not Deployed

### 4. **semantic-search**
- **Entry Point**: `semantic_search` (from `intelligence.vector_search.main`)
- **Memory**: 1024MB
- **Timeout**: 60s
- **Max Instances**: 10
- **Environment Variables**:
  - `GCP_PROJECT_ID=maharani-sales-hub-11-2025`
  - `GCP_REGION=us-central1`
  - `EMBEDDING_PROVIDER=vertex_ai`
- **Description**: Semantic search using BigQuery Vector Search
- **Status**: ❌ Not Deployed

### 5. **create-leads**
- **Entry Point**: `create_leads` (from `intelligence.automation.main`)
- **Memory**: 512MB
- **Timeout**: 300s
- **Max Instances**: 5
- **Environment Variables**:
  - `GCP_PROJECT_ID=maharani-sales-hub-11-2025`
  - `GCP_REGION=us-central1`
- **Description**: Creates Salesforce leads from unmatched emails
- **Status**: ❌ Not Deployed

### 6. **enroll-hubspot**
- **Entry Point**: `enroll_hubspot` (from `intelligence.automation.main`)
- **Memory**: 512MB
- **Timeout**: 300s
- **Max Instances**: 5
- **Environment Variables**:
  - `GCP_PROJECT_ID=maharani-sales-hub-11-2025`
  - `GCP_REGION=us-central1`
- **Description**: Enrolls contacts in HubSpot sequences
- **Status**: ❌ Not Deployed

### 7. **get-hubspot-sequences**
- **Entry Point**: `get_hubspot_sequences` (from `intelligence.automation.main`)
- **Memory**: 512MB
- **Timeout**: 60s
- **Max Instances**: 10
- **Environment Variables**:
  - `GCP_PROJECT_ID=maharani-sales-hub-11-2025`
  - `GCP_REGION=us-central1`
- **Description**: Gets available HubSpot sequences
- **Status**: ❌ Not Deployed

### 8. **generate-email-reply**
- **Entry Point**: `generate_email_reply` (from `intelligence.email_replies.main`)
- **Memory**: 1024MB
- **Timeout**: 120s
- **Max Instances**: 10
- **Environment Variables**:
  - `GCP_PROJECT_ID=maharani-sales-hub-11-2025`
  - `GCP_REGION=us-central1`
  - `LLM_PROVIDER=vertex_ai`
- **Description**: Generates contextual AI email replies
- **Status**: ❌ Not Deployed

---

## 📊 Summary

### Deployment Status
- **Phase 1 (Data Ingestion)**: ✅ 5/5 Deployed
- **Phase 2 (Intelligence)**: ⚠️ 1/8 Deployed (account-scoring needs memory fix)
- **Total**: 6/13 Functions Deployed

### Functions Needing Deployment
1. ❌ generate-embeddings
2. ⚠️ account-scoring (needs memory increase to 2048MB)
3. ❌ nlp-query
4. ❌ semantic-search
5. ❌ create-leads
6. ❌ enroll-hubspot
7. ❌ get-hubspot-sequences
8. ❌ generate-email-reply

---

## 🚀 Deployment Command

Use the deployment script:

```powershell
.\scripts\deploy_phase2_functions.ps1
```

Or deploy individually using the commands in the script.

---

## ✅ Prerequisites

Before deploying, ensure:

1. **APIs Enabled**:
   ```powershell
   gcloud services enable cloudfunctions.googleapis.com --project=maharani-sales-hub-11-2025
   gcloud services enable run.googleapis.com --project=maharani-sales-hub-11-2025
   gcloud services enable aiplatform.googleapis.com --project=maharani-sales-hub-11-2025
   ```

2. **Service Account Permissions**:
   - BigQuery Data Editor
   - BigQuery Job User
   - Vertex AI User
   - Cloud Functions Invoker

3. **Secrets Configured** (in Secret Manager):
   - `hubspot-api-key`
   - `salesforce-username`
   - `salesforce-password`
   - `salesforce-security-token`
   - `dialpad-api-key`
   - `gmail-service-account-key` (JSON)

---

## 📝 Notes

- All functions use **Gen2** (Cloud Run)
- All functions use **Python 3.11** runtime
- All functions deploy from **project root** (`.`) to include shared modules
- All functions use **HTTP trigger**
- All functions require **authentication** (`--no-allow-unauthenticated`)
- Service Account: `sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com`

