# Deploy Account Scoring Function

> **📖 For complete setup guide, see [ACCOUNT_SCORING_COMPLETE_GUIDE.md](./ACCOUNT_SCORING_COMPLETE_GUIDE.md)**

## Issue
The function deployment is blocked by IAM permission: `run.services.setIamPolicy`

## Correct Deployment Command

```bash
gcloud functions deploy account-scoring \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=account_scoring_job \
  --trigger-http \
  --no-allow-unauthenticated \
  --service-account=sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com \
  --memory=2048MB \
  --timeout=540s \
  --max-instances=3 \
  --min-instances=0 \
  --set-env-vars="GCP_PROJECT_ID=maharani-sales-hub-11-2025,GCP_REGION=us-central1,LLM_PROVIDER=vertex_ai" \
  --project=maharani-sales-hub-11-2025
```

## Key Differences from Previous Attempt

1. **Source Path**: `--source=.` (project root) instead of `--source=./intelligence/scoring`
   - This allows access to `utils`, `config`, and other shared modules
   - Uses the root-level `main.py` that exports all functions

2. **Entry Point**: `--entry-point=account_scoring_job` instead of `account_scoring`
   - Matches the function name in `intelligence/scoring/main.py`

3. **Authentication**: `--no-allow-unauthenticated` (requires IAM permission)

## IAM Permission Required

**Error**: `Permission 'run.services.setIamPolicy' denied`

**Solution**: Ask Anand to grant one of:
- `roles/run.developer` on the project, OR
- `run.services.setIamPolicy` permission on the specific Cloud Run service

## Alternative: Deploy Without Authentication First

If Anand can't grant the permission immediately, you can:

1. Deploy with `--allow-unauthenticated` (temporarily):
```bash
gcloud functions deploy account-scoring \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=account_scoring_job \
  --trigger-http \
  --allow-unauthenticated \
  --service-account=sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com \
  --memory=2048MB \
  --timeout=540s \
  --max-instances=3 \
  --min-instances=0 \
  --set-env-vars="GCP_PROJECT_ID=maharani-sales-hub-11-2025,GCP_REGION=us-central1,LLM_PROVIDER=vertex_ai" \
  --project=maharani-sales-hub-11-2025
```

2. Then have Anand set the IAM policy to restrict access later.

## Status

✅ **Container Healthcheck Issue**: FIXED (was using wrong source path)
❌ **IAM Permission**: BLOCKED (needs Anand's help)

## Next Steps

1. Contact Anand with the IAM permission request
2. Once permission is granted, run the deployment command above
3. Or use the alternative deployment method if needed

