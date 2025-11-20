# Milestone 2 - Client Credentials & Information Required

**Milestone:** Phase 2 - Intelligence & Automation  
**Status:** Planning/Not Started  
**Created:** November 2025

---

## 📋 Overview

This document lists **ALL credentials, API keys, and information** required from the client to implement Milestone 2 (Phase 2) features including AI-powered account scoring, embeddings, natural language queries, automation, and AI email replies.

---

## ✅ Already Provided (From Milestone 1)

These credentials should already be available from Phase 1:

### GCP (Google Cloud Platform)
- ✅ GCP Project ID: `maharani-sales-hub-11-2025`
- ✅ GCP Region: `us-central1`
- ✅ Service Account Email: `sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com`
- ✅ Service Account Key File (if needed)

### Gmail OAuth
- ✅ OAuth Client ID
- ✅ OAuth Client Secret
- ✅ Gmail mailboxes (3 sales rep emails)

### Salesforce
- ✅ Username
- ✅ Password
- ✅ Security Token
- ✅ Client ID (Consumer Key)
- ✅ Client Secret (Consumer Secret)
- ✅ Domain (login/test)

### Dialpad
- ✅ API Key

### HubSpot
- ✅ API Key (Private App Access Token)

---

## 🆕 NEW Credentials Required for Milestone 2

### 1. LLM Provider API Keys (Choose One or Multiple)

**Required for:** Account Scoring, Natural Language Queries, AI Email Replies

#### Option A: Anthropic Claude (Recommended)
- **API Key:** `sk-ant-...` (Anthropic API Key)
- **Model:** `claude-3-5-sonnet-20241022` (default)
- **Source:** Anthropic Console → API Keys → Create Key
- **Cost:** Pay-per-use (estimate: $3-15 per 1M input tokens)
- **Usage:** LLM for account scoring, NLP queries, email replies
- **Secret Name:** `anthropic-api-key`

#### Option B: OpenAI GPT-4
- **API Key:** `sk-...` (OpenAI API Key)
- **Organization ID:** (optional)
- **Model:** `gpt-4` or `gpt-4-turbo-preview`
- **Source:** OpenAI Platform → API Keys → Create Key
- **Cost:** Pay-per-use (estimate: $30-60 per 1M tokens)
- **Usage:** LLM for account scoring, NLP queries, email replies
- **Secret Name:** `openai-api-key`

#### Option C: Google Vertex AI
- **Project ID:** (same as GCP project)
- **Region:** `us-central1`
- **Service Account:** (same as existing service account)
- **Model:** Vertex AI Gemini or PaLM models
- **Source:** GCP Vertex AI API (no additional key needed if using GCP service account)
- **Cost:** Pay-per-use (estimate: $2-10 per 1M tokens)
- **Usage:** LLM for account scoring, NLP queries, email replies
- **Note:** Requires Vertex AI API enabled in GCP project

---

### 2. Embeddings Provider API Key

**Required for:** Vector embeddings generation for semantic search

#### Option A: OpenAI Embeddings (Recommended)
- **API Key:** `sk-...` (OpenAI API Key - can be same as LLM key)
- **Model:** `text-embedding-3-small` (default)
- **Source:** OpenAI Platform → API Keys
- **Cost:** $0.020 per 1M tokens (very affordable)
- **Usage:** Generate vector embeddings for emails and call transcripts
- **Secret Name:** `openai-api-key` (reuse same key)

#### Option B: Google Vertex AI Embeddings
- **Project ID:** (same as GCP project)
- **Model:** Vertex AI text-embedding models
- **Source:** GCP Vertex AI API (no additional key needed)
- **Cost:** Pay-per-use
- **Usage:** Generate vector embeddings
- **Note:** Requires Vertex AI API enabled

**Note:** Embedding provider can be different from LLM provider (e.g., use OpenAI for embeddings, Anthropic for LLM)

---

### 3. Configuration Preferences

**Required for:** System configuration and customization

#### LLM Provider Selection
- **Question:** Which LLM provider would you like to use?
  - Anthropic Claude (recommended - best for business use cases)
  - OpenAI GPT-4 (more expensive but very capable)
  - Vertex AI (integrated with GCP, no additional cost for API key)
- **Default:** Anthropic Claude

#### LLM Model Selection
- **Question:** Which model version?
  - Anthropic: `claude-3-5-sonnet-20241022` (recommended)
  - OpenAI: `gpt-4-turbo-preview` or `gpt-4`
  - Vertex AI: `gemini-pro` or `text-bison@001`

#### Embedding Model Selection
- **Question:** Which embedding model?
  - OpenAI: `text-embedding-3-small` (recommended) or `text-embedding-3-large`
  - Vertex AI: `textembedding-gecko@001`

#### Business Rules & Preferences
- **Account Scoring Criteria:** What factors should influence account scoring?
  - Email engagement levels
  - Call frequency and recency
  - Opportunity values
  - Custom business rules
- **Lead Creation Rules:** When should leads be auto-created from unmatched emails?
  - Email domain patterns (exclude certain domains?)
  - Email content patterns (only certain keywords?)
  - Manual review required before creation?
- **HubSpot Enrollment Criteria:** What triggers automatic HubSpot sequence enrollment?
  - Score thresholds
  - Engagement levels
  - Specific account statuses

---

### 4. Additional Access Permissions

**Required for:** Automation features

#### Salesforce Permissions
- **Permission:** Create Leads (if not already granted)
- **Permission:** Create Opportunities (optional)
- **Permission:** Create Tasks/Events (optional)
- **Verification:** Confirm integration user has these permissions

#### HubSpot Permissions
- **Permission:** Create Contacts (if not already granted)
- **Permission:** Enroll Contacts in Sequences
- **Permission:** Update Contact Properties
- **Verification:** Confirm Private App has these scopes

#### Gmail Permissions (If Not Already Set)
- **Permission:** Send emails on behalf of users (for AI email replies)
- **Note:** May need additional OAuth scopes or domain-wide delegation

---

### 5. Business Logic & Configuration

**Required for:** Customization and business rules

#### Account Scoring Weights
- **Email Engagement Weight:** (0-100) - How important is email engagement?
- **Call Engagement Weight:** (0-100) - How important is call activity?
- **Opportunity Value Weight:** (0-100) - How important is deal size?
- **Time Decay Factor:** How quickly should engagement decay over time?

#### Lead Creation Rules
- **Auto-create Leads:** Yes/No
- **Domain Exclusions:** List of email domains to ignore (e.g., `@competitor.com`)
- **Required Keywords:** Keywords that must appear in email to create lead
- **Excluded Keywords:** Keywords that prevent lead creation

#### HubSpot Sequence Configuration
- **Sequence IDs:** List of HubSpot sequence IDs for enrollment
- **Enrollment Criteria:** Score thresholds or other criteria
- **Sequence Mapping:** Which sequence for which account type/score?

#### Email Reply Preferences
- **Tone:** Professional, Friendly, Casual?
- **Length:** Brief, Medium, Detailed?
- **Auto-send:** Yes/No (manual review required?)
- **Reply Templates:** Custom templates for common scenarios?

---

## 📝 Complete Credential Checklist

### From Client (New Requirements)

#### LLM Provider (Choose One)
- [ ] **Anthropic API Key** (`anthropic-api-key`)
  - OR
- [ ] **OpenAI API Key** (`openai-api-key`)
  - OR
- [ ] **Vertex AI enabled** (no key needed if using GCP service account)

#### Embeddings Provider
- [ ] **OpenAI API Key** (`openai-api-key` - can reuse LLM key)
  - OR
- [ ] **Vertex AI enabled** (no key needed)

#### Configuration Decisions
- [ ] **LLM Provider Selection:** Anthropic / OpenAI / Vertex AI
- [ ] **LLM Model:** [model name]
- [ ] **Embedding Model:** [model name]
- [ ] **Account Scoring Criteria:** [preferences]
- [ ] **Lead Creation Rules:** [yes/no + rules]
- [ ] **HubSpot Enrollment Rules:** [criteria]
- [ ] **Email Reply Preferences:** [tone, length, auto-send]

#### Permissions Verification
- [ ] **Salesforce:** Confirm create leads permission
- [ ] **HubSpot:** Confirm sequence enrollment permission
- [ ] **Gmail:** Confirm send email permission (for AI replies)

---

## 🔐 Secret Manager Setup Commands

Once you receive the credentials, add them to Secret Manager:

### PowerShell
```powershell
$projectId = "maharani-sales-hub-11-2025"

# Anthropic API Key
echo -n "YOUR_ANTHROPIC_API_KEY" | gcloud secrets versions add anthropic-api-key --data-file=- --project=$projectId

# OpenAI API Key (if using)
echo -n "YOUR_OPENAI_API_KEY" | gcloud secrets versions add openai-api-key --data-file=- --project=$projectId

# Grant service account access
gcloud secrets add-iam-policy-binding anthropic-api-key `
  --member="serviceAccount:sales-intel-poc-sa@$projectId.iam.gserviceaccount.com" `
  --role="roles/secretmanager.secretAccessor" `
  --project=$projectId

gcloud secrets add-iam-policy-binding openai-api-key `
  --member="serviceAccount:sales-intel-poc-sa@$projectId.iam.gserviceaccount.com" `
  --role="roles/secretmanager.secretAccessor" `
  --project=$projectId
```

### Bash
```bash
PROJECT_ID="maharani-sales-hub-11-2025"

# Anthropic API Key
echo -n "YOUR_ANTHROPIC_API_KEY" | gcloud secrets versions add anthropic-api-key --data-file=- --project=$PROJECT_ID

# OpenAI API Key (if using)
echo -n "YOUR_OPENAI_API_KEY" | gcloud secrets versions add openai-api-key --data-file=- --project=$PROJECT_ID

# Grant service account access
gcloud secrets add-iam-policy-binding anthropic-api-key \
  --member="serviceAccount:sales-intel-poc-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=$PROJECT_ID

gcloud secrets add-iam-policy-binding openai-api-key \
  --member="serviceAccount:sales-intel-poc-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=$PROJECT_ID
```

---

## 💰 Cost Estimates

### Anthropic Claude
- **Account Scoring:** ~$0.50-2.00 per 100 accounts (daily)
- **NLP Queries:** ~$0.10-0.50 per query
- **Email Replies:** ~$0.05-0.20 per email
- **Monthly Estimate:** $50-300 (depends on volume)

### OpenAI GPT-4
- **Account Scoring:** ~$2-8 per 100 accounts (daily)
- **NLP Queries:** ~$0.30-1.50 per query
- **Email Replies:** ~$0.15-0.60 per email
- **Monthly Estimate:** $200-800 (depends on volume)

### OpenAI Embeddings
- **Embedding Generation:** ~$0.10-0.50 per 1,000 emails/calls
- **One-time Historical Data:** $10-50 (depending on volume)
- **Incremental Updates:** Minimal cost

### Vertex AI
- **Similar pricing to Anthropic**
- **No additional API key costs** (uses GCP service account)

**Note:** Actual costs depend on usage volume. Start with test runs to estimate.

---

## 📧 How to Obtain Credentials

### Anthropic API Key
1. Go to: https://console.anthropic.com/
2. Sign up or log in
3. Navigate to: API Keys
4. Click: "Create Key"
5. Copy the key (starts with `sk-ant-`)
6. **Note:** Key is shown only once, save it immediately

### OpenAI API Key
1. Go to: https://platform.openai.com/
2. Sign up or log in
3. Navigate to: API Keys
4. Click: "Create new secret key"
5. Copy the key (starts with `sk-`)
6. **Note:** Key is shown only once, save it immediately

### Vertex AI Setup
1. Go to: GCP Console → Vertex AI
2. Enable Vertex AI API (if not already enabled)
3. Ensure service account has Vertex AI User role
4. No API key needed (uses GCP authentication)

---

## ⚠️ Security Notes

1. **Never share API keys via email** - Use secure channels
2. **Store keys only in Secret Manager** - Never in code or config files
3. **Rotate keys regularly** - Every 90-180 days
4. **Monitor API usage** - Set up billing alerts
5. **Use least privilege** - Only grant necessary permissions

---

## ✅ Ready to Start Checklist

- [ ] LLM provider selected (Anthropic/OpenAI/Vertex AI)
- [ ] LLM API key obtained and added to Secret Manager
- [ ] Embedding provider selected (OpenAI/Vertex AI)
- [ ] Embedding API key obtained (if using OpenAI)
- [ ] Business rules and preferences documented
- [ ] Permissions verified (Salesforce, HubSpot, Gmail)
- [ ] Configuration decisions made
- [ ] Cost estimates reviewed and approved

---

## 📞 Next Steps

1. **Share this document with client**
2. **Client provides credentials and preferences**
3. **Add credentials to Secret Manager**
4. **Configure system with business rules**
5. **Begin Milestone 2 development**

---

**Last Updated:** November 2025  
**Document Version:** 1.0  
**Status:** Ready for Client Review

