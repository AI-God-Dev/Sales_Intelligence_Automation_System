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

### 1. LLM Provider - Google Vertex AI (Recommended ✅)

**Required for:** Account Scoring, Natural Language Queries, AI Email Replies

**✅ Decision: Using Google Vertex AI** - No additional API keys needed!

#### Why Vertex AI?
- ✅ Already integrated with GCP (same project, same service account)
- ✅ No additional API keys required
- ✅ Simplified credential management
- ✅ Native GCP integration with BigQuery, monitoring, and billing
- ✅ Cost-effective pricing
- ✅ Uses existing GCP authentication

#### Setup Required:
- **Enable Vertex AI API:** Enable the Vertex AI API in GCP Console
- **Service Account Role:** Ensure service account has `Vertex AI User` role (already configured)
- **Project ID:** `maharani-sales-hub-11-2025` (already have)
- **Region:** `us-central1` (already configured)
- **Model:** Vertex AI Gemini (`gemini-pro`) or PaLM (`text-bison@001`)

#### Cost:
- **Pay-per-use:** ~$2-10 per 1M tokens (competitive pricing)
- **Account Scoring:** ~$0.50-2.00 per 100 accounts (daily)
- **NLP Queries:** ~$0.10-0.50 per query
- **Email Replies:** ~$0.05-0.20 per email
- **Monthly Estimate:** $50-300 (depends on volume)

---

#### Alternative Options (Not Recommended - Only if Needed)

**Option B: Anthropic Claude** (if Vertex AI doesn't meet requirements)
- **API Key:** `sk-ant-...` (Anthropic API Key)
- **Model:** `claude-3-5-sonnet-20241022`
- **Source:** Anthropic Console → API Keys
- **Cost:** ~$3-15 per 1M tokens
- **Secret Name:** `anthropic-api-key`

**Option C: OpenAI GPT-4** (if Vertex AI doesn't meet requirements)
- **API Key:** `sk-...` (OpenAI API Key)
- **Model:** `gpt-4-turbo-preview` or `gpt-4`
- **Source:** OpenAI Platform → API Keys
- **Cost:** ~$30-60 per 1M tokens
- **Secret Name:** `openai-api-key`

---

### 2. Embeddings Provider - Google Vertex AI (Recommended ✅)

**Required for:** Vector embeddings generation for semantic search

**✅ Decision: Using Google Vertex AI Embeddings** - No additional API keys needed!

#### Setup Required:
- **Vertex AI API:** Already enabled (same as LLM)
- **Model:** Vertex AI `textembedding-gecko@001` or similar
- **Service Account:** Same as existing (no additional setup)
- **No API Key:** Uses GCP service account authentication

#### Cost:
- **Pay-per-use:** Competitive pricing
- **Embedding Generation:** ~$0.10-0.50 per 1,000 emails/calls
- **One-time Historical Data:** $10-50 (depending on volume)
- **Incremental Updates:** Minimal cost

---

#### Alternative Option (Not Recommended)

**Option B: OpenAI Embeddings** (if Vertex AI embeddings don't meet requirements)
- **API Key:** `sk-...` (OpenAI API Key)
- **Model:** `text-embedding-3-small`
- **Source:** OpenAI Platform → API Keys
- **Cost:** $0.020 per 1M tokens
- **Secret Name:** `openai-api-key`

---

### 3. Configuration Preferences

**Required for:** System configuration and customization

#### LLM Provider Selection
- **✅ Decision:** Google Vertex AI (Selected)
- **Rationale:** Integrated with GCP, no additional API keys, simplified management
- **Alternative Options:** Available if needed (Anthropic, OpenAI)

#### LLM Model Selection
- **✅ Default:** Vertex AI `gemini-pro` (recommended)
- **Alternative:** `text-bison@001` (if Gemini not available in region)
- **Note:** Model will be configured during implementation

#### Embedding Model Selection
- **✅ Default:** Vertex AI `textembedding-gecko@001` (recommended)
- **Alternative:** Other Vertex AI embedding models as available
- **Note:** Model will be configured during implementation

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

#### ✅ Vertex AI Setup (Selected - Primary)
- [ ] **Enable Vertex AI API** in GCP Console
- [ ] **Verify service account** has Vertex AI User role (already configured)
- [ ] **Confirm region** supports Vertex AI models (`us-central1`)
- [ ] **No API keys needed** - uses existing GCP service account

#### Alternative Options (Not Required - Only if Needed)
- [ ] **Anthropic API Key** (`anthropic-api-key`) - Only if Vertex AI doesn't work
- [ ] **OpenAI API Key** (`openai-api-key`) - Only if Vertex AI doesn't work

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

## 🔐 Vertex AI Setup Commands

Since we're using Vertex AI, no API keys need to be added to Secret Manager. Just enable the API:

### PowerShell
```powershell
$projectId = "maharani-sales-hub-11-2025"

# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com --project=$projectId

# Verify service account has Vertex AI User role (should already be set)
gcloud projects get-iam-policy $projectId `
  --flatten="bindings[].members" `
  --filter="bindings.members:serviceAccount:sales-intel-poc-sa@$projectId.iam.gserviceaccount.com" `
  --format="table(bindings.role)"

# If not set, grant Vertex AI User role
gcloud projects add-iam-policy-binding $projectId `
  --member="serviceAccount:sales-intel-poc-sa@$projectId.iam.gserviceaccount.com" `
  --role="roles/aiplatform.user"
```

### Bash
```bash
PROJECT_ID="maharani-sales-hub-11-2025"

# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com --project=$PROJECT_ID

# Verify service account has Vertex AI User role (should already be set)
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:sales-intel-poc-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --format="table(bindings.role)"

# If not set, grant Vertex AI User role
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:sales-intel-poc-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

---

### Alternative: Secret Manager Setup (Only if Using Anthropic/OpenAI)

If for any reason Vertex AI doesn't meet requirements, use these commands:

```powershell
# Anthropic API Key (if needed)
echo -n "YOUR_ANTHROPIC_API_KEY" | gcloud secrets versions add anthropic-api-key --data-file=- --project=$projectId

# OpenAI API Key (if needed)
echo -n "YOUR_OPENAI_API_KEY" | gcloud secrets versions add openai-api-key --data-file=- --project=$projectId

# Grant service account access
gcloud secrets add-iam-policy-binding anthropic-api-key `
  --member="serviceAccount:sales-intel-poc-sa@$projectId.iam.gserviceaccount.com" `
  --role="roles/secretmanager.secretAccessor" `
  --project=$projectId
```

---

## 💰 Cost Estimates - Vertex AI

### Vertex AI LLM (Gemini/PaLM)
- **Account Scoring:** ~$0.50-2.00 per 100 accounts (daily)
- **NLP Queries:** ~$0.10-0.50 per query
- **Email Replies:** ~$0.05-0.20 per email
- **Monthly Estimate:** $50-300 (depends on volume)
- **API Key Cost:** $0 (uses existing GCP service account)

### Vertex AI Embeddings
- **Embedding Generation:** ~$0.10-0.50 per 1,000 emails/calls
- **One-time Historical Data:** $10-50 (depending on volume)
- **Incremental Updates:** Minimal cost
- **API Key Cost:** $0 (uses existing GCP service account)

### Total Monthly Estimate
- **Minimum:** $50-100/month (light usage)
- **Typical:** $100-200/month (moderate usage)
- **Maximum:** $200-400/month (heavy usage)

**Note:** Actual costs depend on usage volume. All costs appear on GCP bill. Start with test runs to estimate.

---

## 📧 How to Set Up Vertex AI

### ✅ Vertex AI Setup (Primary Method)

1. **Enable Vertex AI API:**
   - Go to: [GCP Console → APIs & Services → Library](https://console.cloud.google.com/apis/library)
   - Search for: "Vertex AI API"
   - Click: "Enable"
   - **OR** use command: `gcloud services enable aiplatform.googleapis.com --project=maharani-sales-hub-11-2025`

2. **Verify Service Account Permissions:**
   - Service account should already have `Vertex AI User` role
   - If not, grant it via IAM or run the setup commands above

3. **Verify Region Support:**
   - Confirm `us-central1` supports Vertex AI models (it does)
   - Models available: Gemini Pro, PaLM, text-bison

4. **No API Key Needed:**
   - Uses existing GCP service account authentication
   - All requests authenticated via service account

**That's it!** No external accounts or API keys needed.

---

### Alternative: External Providers (Only if Needed)

If Vertex AI doesn't meet requirements, these alternatives are available:

#### Anthropic API Key
1. Go to: https://console.anthropic.com/
2. Sign up or log in
3. Navigate to: API Keys → Create Key
4. Copy the key (starts with `sk-ant-`)
5. Add to Secret Manager (see commands above)

#### OpenAI API Key
1. Go to: https://platform.openai.com/
2. Sign up or log in
3. Navigate to: API Keys → Create new secret key
4. Copy the key (starts with `sk-`)
5. Add to Secret Manager (see commands above)

---

## ⚠️ Security Notes

1. **Never share API keys via email** - Use secure channels
2. **Store keys only in Secret Manager** - Never in code or config files
3. **Rotate keys regularly** - Every 90-180 days
4. **Monitor API usage** - Set up billing alerts
5. **Use least privilege** - Only grant necessary permissions

---

## ✅ Ready to Start Checklist

### Vertex AI Setup (Primary - Required)
- [ ] **Vertex AI API enabled** in GCP Console
- [ ] **Service account verified** has Vertex AI User role
- [ ] **Region confirmed** supports Vertex AI (`us-central1` ✅)
- [ ] **No API keys needed** - using existing GCP authentication

### Configuration & Preferences (Required)
- [ ] **Business rules documented** (account scoring criteria, lead creation rules)
- [ ] **HubSpot enrollment rules** defined
- [ ] **Email reply preferences** specified (tone, length, auto-send)
- [ ] **Permissions verified** (Salesforce create leads, HubSpot enroll, Gmail send)

### Optional (Only if Not Using Vertex AI)
- [ ] Alternative LLM provider selected (Anthropic/OpenAI)
- [ ] Alternative API key obtained and added to Secret Manager

**Note:** With Vertex AI, the setup is much simpler - just enable the API and verify permissions!

---

## 📞 Next Steps

1. **Share this document with client**
2. **Client provides credentials and preferences**
3. **Add credentials to Secret Manager**
4. **Configure system with business rules**
5. **Begin Milestone 2 development**

---

**Last Updated:** November 2025  
**Document Version:** 2.0  
**Changes:** Updated to use Vertex AI as primary/recommended provider  
**Status:** Ready for Client Review

