# Client Deployment Guide (Gen2, Vertex-only)

Use these exact patterns for every Cloud Function deployment in Anand's environment.

## Prereqs
- ADC configured (`gcloud auth application-default login`)
- Env vars: `GCP_PROJECT_ID`, `GCP_REGION`, `BQ_DATASET_NAME`, `SA_EMAIL`
- Run from repo root containing `main.py`.

## Required entry points (root `main.py`)
- `gmail_sync`, `salesforce_sync`, `dialpad_sync`, `hubspot_sync`, `entity_resolution`
- `account_scoring_job`, `semantic_search`, `generate_email_reply`, `enroll_hubspot`
- `get_hubspot_sequences`, `generate_embeddings`, `nlp_query`, `create_leads`

## Deploy command template (copy/paste)
```bash
gcloud functions deploy <service-name> \
  --gen2 \
  --runtime=python311 \
  --region="$GCP_REGION" \
  --source=. \
  --entry-point=<FUNCTION_NAME> \
  --trigger-http \
  --no-allow-unauthenticated \
  --service-account="$SA_EMAIL" \
  --memory=512MB \
  --timeout=540s \
  --max-instances=10 \
  --min-instances=0 \
  --set-env-vars="GCP_PROJECT_ID=$GCP_PROJECT_ID,GCP_REGION=$GCP_REGION,BQ_DATASET_NAME=$BQ_DATASET_NAME"
```

## Notes
- Do **not** use module paths (e.g., `cloud_functions.gmail_sync.main.gmail_sync`) on Gen2.
- BigQuery dataset must come from `BQ_DATASET_NAME` (`sales_intelligence` or `sales_intelligence_dev`).
- AI: Vertex-only (`gemini-1.5-pro/flash`, `textembedding-gecko@001`) via ADC; no OpenAI/Anthropic keys.
- Health checks: ensure `main.py` exists at repo root; functions-framework local run uses `--target=gmail_sync`.
