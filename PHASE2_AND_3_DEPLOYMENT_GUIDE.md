# Phase 2 & 3 Deployment Guide - Quick Start

## 🚀 Complete Deployment Steps

### Step 1: Enable Vertex AI API

```bash
gcloud services enable aiplatform.googleapis.com --project=maharani-sales-hub-11-2025
```

### Step 2: Verify Service Account Permissions

```bash
# Check if Vertex AI User role is assigned
gcloud projects get-iam-policy maharani-sales-hub-11-2025 \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com" \
  --format="table(bindings.role)"

# If not set, grant the role:
gcloud projects add-iam-policy-binding maharani-sales-hub-11-2025 \
  --member="serviceAccount:sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

### Step 3: Deploy Phase 2 Cloud Functions

**Bash (Linux/Mac)**:
```bash
cd ~/Sales_Intelligence_Automation_System
chmod +x scripts/deploy_phase2_functions.sh
./scripts/deploy_phase2_functions.sh
```

**PowerShell (Windows)**:
```powershell
cd C:\Users\Administrator\Desktop\SALES
.\scripts\deploy_phase2_functions.ps1
```

This will deploy:
- `generate-embeddings`
- `account-scoring`
- `nlp-query`
- `create-leads`
- `enroll-hubspot`
- `get-hubspot-sequences`
- `generate-email-reply`

### Step 4: Create Cloud Scheduler Jobs

**Daily Account Scoring (7 AM)**:
```bash
gcloud scheduler jobs create http account-scoring-daily \
  --location=us-central1 \
  --schedule="0 7 * * *" \
  --uri="https://us-central1-maharani-sales-hub-11-2025.cloudfunctions.net/account-scoring" \
  --http-method=POST \
  --oidc-service-account-email=sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com \
  --project=maharani-sales-hub-11-2025
```

**Daily Embeddings Generation (8 AM)**:
```bash
gcloud scheduler jobs create http generate-embeddings-daily \
  --location=us-central1 \
  --schedule="0 8 * * *" \
  --uri="https://us-central1-maharani-sales-hub-11-2025.cloudfunctions.net/generate-embeddings" \
  --http-method=POST \
  --message-body='{"type":"both","limit":1000}' \
  --oidc-service-account-email=sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com \
  --project=maharani-sales-hub-11-2025
```

### Step 5: Deploy Web Application

**Option A: Cloud Run (Recommended)**:
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

**Option B: Local Development**:
```bash
cd web_app
pip install -r requirements.txt
streamlit run app.py
```

### Step 6: Initial Data Processing

**Generate Embeddings for Historical Data**:
```bash
curl -X POST \
  "https://us-central1-maharani-sales-hub-11-2025.cloudfunctions.net/generate-embeddings" \
  -H "Content-Type: application/json" \
  -d '{"type":"both","limit":null}'
```

**Run Initial Account Scoring**:
```bash
curl -X POST \
  "https://us-central1-maharani-sales-hub-11-2025.cloudfunctions.net/account-scoring"
```

### Step 7: Verify Deployment

**Check Function Status**:
```bash
gcloud functions list --gen2 --region=us-central1 --project=maharani-sales-hub-11-2025
```

**Test NLP Query**:
```bash
curl -X POST \
  "https://us-central1-maharani-sales-hub-11-2025.cloudfunctions.net/nlp-query" \
  -H "Content-Type: application/json" \
  -d '{"query":"Show me accounts with high engagement in the last week"}'
```

**Check Web App**:
- Navigate to Cloud Run URL or `http://localhost:8501` if running locally
- Test login and navigation

---

## ✅ Verification Checklist

- [ ] Vertex AI API enabled
- [ ] Service account has Vertex AI User role
- [ ] All Phase 2 functions deployed successfully
- [ ] Cloud Scheduler jobs created
- [ ] Web application deployed
- [ ] Initial embeddings generated
- [ ] Account scoring running
- [ ] NLP queries working
- [ ] Web app accessible and functional

---

## 🔧 Troubleshooting

### Vertex AI Errors

**Error**: "Vertex AI initialization failed"
- **Solution**: Ensure Vertex AI API is enabled and service account has permissions

### Function Deployment Errors

**Error**: "Entry point not found"
- **Solution**: Verify entry points in deployment scripts match function names

### Web App Errors

**Error**: "Cannot connect to Cloud Functions"
- **Solution**: Check function URLs in `web_app/app.py` match your deployment

---

## 📞 Support

For issues or questions:
1. Check logs: `gcloud functions logs read <function-name> --gen2 --region=us-central1`
2. Review documentation: `PHASE2_AND_3_COMPLETE.md`
3. Check BigQuery `etl_runs` table for execution status

---

**Status**: Ready for Production Deployment  
**Last Updated**: Phase 2 & 3 Complete

