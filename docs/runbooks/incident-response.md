# Incident Response Runbook

## Overview
This runbook provides step-by-step procedures for responding to common incidents in the Sales Intelligence Automation System.

## Incident Severity Levels

- **P0 - Critical**: System down, data loss, security breach
- **P1 - High**: Major functionality broken, affecting all users
- **P2 - Medium**: Partial functionality broken, affecting some users
- **P3 - Low**: Minor issues, workarounds available

## Common Incidents

### Account Scoring Failing (504 Timeout)

**Symptoms:**
- Cloud Scheduler shows 504 Gateway Timeout
- Cloud Function logs show timeouts
- No new rows in `account_recommendations` table

**Investigation Steps:**
1. Check Cloud Function logs:
   ```bash
   gcloud functions logs read account-scoring --gen2 --region=us-central1 --limit=100
   ```

2. Verify function is deployed:
   ```bash
   gcloud functions describe account-scoring --gen2 --region=us-central1
   ```

3. Check environment variables:
   ```bash
   gcloud functions describe account-scoring --gen2 --region=us-central1 \
     --format="yaml(serviceConfig.environmentVariables)"
   ```

4. Verify Vertex AI model:
   - Check `LLM_MODEL` env var is set correctly
   - Verify model name is accessible in project

**Resolution:**
1. If model not found (404):
   - Update `LLM_MODEL` to valid model (e.g., `gemini-2.5-pro`)
   - Redeploy function

2. If timeout:
   - Increase function timeout (max 540s for Gen2)
   - Increase scheduler `max_retry_duration`
   - Check if processing too many accounts (use `limit` parameter)

3. If memory issues:
   - Increase function memory allocation
   - Check for memory leaks in code

**Prevention:**
- Monitor function execution times
- Set up alerts for high error rates
- Test with limit parameter before full runs

---

### Vertex AI Model Not Found (404)

**Symptoms:**
- Error: "404 Publisher Model .../models/gemini-1.5-pro was not found"
- Function fails immediately on startup

**Investigation:**
1. Check function environment variables:
   ```bash
   gcloud functions describe account-scoring --gen2 --format="yaml(serviceConfig.environmentVariables)"
   ```

2. Verify model availability:
   ```bash
   gcloud ai models list --region=us-central1
   ```

3. Check IAM permissions:
   ```bash
   gcloud projects get-iam-policy PROJECT_ID \
     --flatten="bindings[].members" \
     --filter="bindings.members:serviceAccount:SERVICE_ACCOUNT"
   ```

**Resolution:**
1. Update model name in deployment:
   ```bash
   gcloud functions deploy account-scoring \
     --set-env-vars="LLM_MODEL=gemini-2.5-pro,..."
   ```

2. Grant Vertex AI permissions:
   ```bash
   gcloud projects add-iam-policy-binding PROJECT_ID \
     --member="serviceAccount:SERVICE_ACCOUNT" \
     --role="roles/aiplatform.user"
   ```

3. Enable Vertex AI API:
   ```bash
   gcloud services enable aiplatform.googleapis.com
   ```

---

### Date Serialization Errors

**Symptoms:**
- Error: "TypeError: Object of type date is not JSON serializable"
- Intermittent failures on certain accounts

**Investigation:**
1. Check which accounts are failing:
   ```bash
   gcloud functions logs read account-scoring --gen2 --limit=100 | grep "date"
   ```

2. Verify BigQuery query returns date objects

**Resolution:**
1. Ensure `ai/scoring.py` uses custom serializer:
   ```python
   json.dumps(account_data, default=_json_serializer, ensure_ascii=False)
   ```

2. Redeploy function with fix

---

### BigQuery Query Failures

**Symptoms:**
- Queries timing out
- "Quota exceeded" errors
- Slow query performance

**Investigation:**
1. Check BigQuery job history:
   ```bash
   bq ls -j --max_results=10
   ```

2. Review query performance:
   ```sql
   SELECT * FROM `region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
   WHERE creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
   ORDER BY creation_time DESC
   ```

**Resolution:**
1. Add partition filters to queries
2. Add LIMIT clauses to prevent runaway queries
3. Optimize query structure
4. Use query caching where possible

---

## Escalation Path

1. **Level 1**: On-call engineer (check logs, basic troubleshooting)
2. **Level 2**: Senior engineer (complex issues, code changes)
3. **Level 3**: Engineering lead (critical issues, architecture decisions)

## Post-Incident

After resolving an incident:
1. Document root cause
2. Create follow-up tasks for prevention
3. Update this runbook if needed
4. Review monitoring/alerting gaps

