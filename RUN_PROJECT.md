# 🚀 How to Run the Sales Intelligence System

## Quick Start Guide

### Option 1: Run Web Application Locally (Recommended for Testing)

1. **Setup Virtual Environment** (if not already done):
```bash
# Windows PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

2. **Install Dependencies**:
```bash
pip install -r requirements.txt
pip install -r web_app/requirements.txt
```

3. **Set Environment Variables**:
```bash
# Windows PowerShell
$env:GCP_PROJECT_ID = "maharani-sales-hub-11-2025"
$env:GCP_REGION = "us-central1"

# Linux/Mac
export GCP_PROJECT_ID="maharani-sales-hub-11-2025"
export GCP_REGION="us-central1"
```

4. **Authenticate with Google Cloud**:
```bash
gcloud auth application-default login
```

5. **Run the Web Application**:
```bash
cd web_app
streamlit run app.py
```

The web app will open at: `http://localhost:8501`

---

### Option 2: Deploy to Cloud Run (Production)

1. **Deploy Web Application**:
```bash
cd web_app
gcloud run deploy sales-intelligence-web \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=maharani-sales-hub-11-2025,GCP_REGION=us-central1 \
  --project=maharani-sales-hub-11-2025
```

---

### Option 3: Run Cloud Functions Locally

For testing individual functions:

1. **Run Gmail Sync Function**:
```bash
functions-framework --target=gmail_sync --source=cloud_functions/gmail_sync
```

2. **Run NLP Query Function**:
```bash
functions-framework --target=nlp_query --source=intelligence/nlp_query
```

---

## Prerequisites

### Required Setup

1. **Google Cloud SDK**: Must be installed and authenticated
2. **Python 3.11+**: Required for Cloud Functions
3. **GCP Project Access**: Service account credentials configured
4. **BigQuery Dataset**: Must exist (`sales_intelligence`)

### Environment Variables

Create a `.env` file or set environment variables:
```env
GCP_PROJECT_ID=maharani-sales-hub-11-2025
GCP_REGION=us-central1
BIGQUERY_DATASET=sales_intelligence
```

### Secrets Configuration

Ensure these secrets exist in Secret Manager:
- `salesforce-username`
- `salesforce-password`
- `salesforce-security-token`
- `dialpad-api-key`
- `hubspot-api-key`
- (Optional) `anthropic-api-key` or `openai-api-key` if not using Vertex AI

---

## Testing the System

### 1. Test Web Application Locally

```bash
cd web_app
streamlit run app.py
```

**Login**: Use any email address (e.g., `anand@maharaniweddings.com`)

**Test Features**:
- Dashboard: View metrics (if BigQuery has data)
- Account Scoring: Trigger scoring job
- NLP Query: Try "Show me accounts with high engagement"
- Semantic Search: Try "budget discussions for 2026"
- Unmatched Emails: View and create leads

### 2. Test Cloud Functions

**Test NLP Query**:
```bash
curl -X POST "http://localhost:8080" \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me accounts with high engagement"}'
```

**Test Semantic Search**:
```bash
curl -X POST "http://localhost:8080" \
  -H "Content-Type: application/json" \
  -d '{"query": "budget discussions", "type": "accounts"}'
```

---

## Troubleshooting

### Web App Won't Start

**Error**: `ModuleNotFoundError`
- **Solution**: Install dependencies: `pip install -r web_app/requirements.txt`

**Error**: `BigQuery client error`
- **Solution**: Run `gcloud auth application-default login`

### Cloud Functions Not Working

**Error**: `Secret not found`
- **Solution**: Create secrets in Secret Manager (see `docs/SECRETS_LIST.md`)

**Error**: `Vertex AI not enabled`
- **Solution**: `gcloud services enable aiplatform.googleapis.com --project=maharani-sales-hub-11-2025`

### BigQuery Errors

**Error**: `Dataset not found`
- **Solution**: Create dataset: `bq mk sales_intelligence`

**Error**: `Table not found`
- **Solution**: Run `scripts/setup_bigquery.sh` or create tables manually

---

## Next Steps

1. **Run the web app locally** to test
2. **Deploy Cloud Functions** if not already deployed
3. **Deploy web app to Cloud Run** for production
4. **Test all features** and verify data flow
5. **Run UAT** with sales team

---

## Quick Commands Reference

```bash
# Activate virtual environment
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate    # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run web app
cd web_app && streamlit run app.py

# Deploy functions
./scripts/deploy_phase2_functions.sh

# Test functions
pytest tests/

# View logs
gcloud functions logs read <function-name> --gen2 --region=us-central1
```

---

**Ready to run!** Start with Option 1 to test locally, then deploy to production.

