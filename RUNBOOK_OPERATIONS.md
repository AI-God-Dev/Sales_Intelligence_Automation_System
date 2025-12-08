# Runbook - Operations Guide
## Sales Intelligence Automation System

## Overview

This runbook provides operational procedures for monitoring, maintaining, and troubleshooting the Sales Intelligence Automation System in production.

---

## System Health Checks

### Daily Health Check

**Time**: 8:00 AM (after account scoring completes)

**Checklist**:
1. ✅ Account scoring completed successfully
2. ✅ All ETL jobs ran successfully
3. ✅ No critical errors in Cloud Logging
4. ✅ BigQuery tables updated with recent data
5. ✅ Web application accessible

**Commands**:
```bash
# Check latest ETL runs
bq query --use_legacy_sql=false "
SELECT 
  source_system,
  status,
  started_at,
  rows_processed
FROM \`PROJECT_ID.sales_intelligence.etl_runs\`
WHERE DATE(started_at) = CURRENT_DATE()
ORDER BY started_at DESC
"

# Check account scoring
bq query --use_legacy_sql=false "
SELECT 
  COUNT(*) as accounts_scored,
  MAX(score_date) as latest_score_date
FROM \`PROJECT_ID.sales_intelligence.account_recommendations\`
WHERE score_date = CURRENT_DATE()
"
```

### Weekly Health Check

**Time**: Monday 9:00 AM

**Checklist**:
1. ✅ Data quality metrics within targets
2. ✅ Entity resolution match rates acceptable
3. ✅ Embedding generation up to date
4. ✅ No stale data in tables
5. ✅ Cost analysis (GCP billing)

**Commands**:
```bash
# Check entity resolution match rates
bq query --use_legacy_sql=false "
SELECT 
  COUNTIF(sf_contact_id IS NOT NULL) * 100.0 / COUNT(*) as email_match_rate
FROM \`PROJECT_ID.sales_intelligence.gmail_participants\`
WHERE DATE(ingested_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
"
```

---

## Monitoring

### Cloud Logging

**View Recent Errors**:
```bash
gcloud logging read "severity>=ERROR" \
  --limit=50 \
  --format=json \
  --project=PROJECT_ID
```

**View Function Logs**:
```bash
# Gmail sync
gcloud functions logs read gmail-sync --limit=50

# Account scoring
gcloud functions logs read account-scoring --limit=50
```

### BigQuery Monitoring

**Check ETL Status**:
```sql
SELECT 
  source_system,
  status,
  COUNT(*) as run_count,
  AVG(TIMESTAMP_DIFF(completed_at, started_at, SECOND)) as avg_duration_seconds
FROM `PROJECT_ID.sales_intelligence.etl_runs`
WHERE DATE(started_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY source_system, status
ORDER BY source_system, status
```

**Check Data Freshness**:
```sql
SELECT 
  'gmail_messages' as table_name,
  MAX(sent_at) as latest_record,
  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(sent_at), HOUR) as hours_old
FROM `PROJECT_ID.sales_intelligence.gmail_messages`
UNION ALL
SELECT 
  'dialpad_calls' as table_name,
  MAX(call_time) as latest_record,
  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(call_time), HOUR) as hours_old
FROM `PROJECT_ID.sales_intelligence.dialpad_calls`
```

### Cloud Functions Monitoring

**List All Functions**:
```bash
gcloud functions list --project=PROJECT_ID
```

**Check Function Status**:
```bash
gcloud functions describe FUNCTION_NAME --project=PROJECT_ID
```

**View Function Metrics**:
```bash
# In Cloud Console: Cloud Functions > FUNCTION_NAME > Metrics
```

---

## Common Operations

### 1. Manual ETL Trigger

**Gmail Sync**:
```bash
curl -X POST \
  https://REGION-PROJECT_ID.cloudfunctions.net/gmail-sync \
  -H "Authorization: bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{"mailbox": "email@example.com", "sync_type": "incremental"}'
```

**Salesforce Sync**:
```bash
curl -X POST \
  https://REGION-PROJECT_ID.cloudfunctions.net/salesforce-sync \
  -H "Authorization: bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{"object_type": "Account", "sync_type": "incremental"}'
```

**Entity Resolution**:
```bash
curl -X POST \
  https://REGION-PROJECT_ID.cloudfunctions.net/entity-resolution \
  -H "Authorization: bearer $(gcloud auth print-identity-token)"
```

### 2. Regenerate Embeddings

**Trigger Embedding Generation**:
```bash
curl -X POST \
  https://REGION-PROJECT_ID.cloudfunctions.net/generate-embeddings \
  -H "Authorization: bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{"type": "both", "limit": 1000}'
```

**Check Embedding Status**:
```sql
SELECT 
  COUNT(*) as total_emails,
  COUNTIF(embedding IS NOT NULL) as emails_with_embeddings,
  COUNTIF(embedding IS NULL) as emails_without_embeddings
FROM `PROJECT_ID.sales_intelligence.gmail_messages`
```

### 3. Re-run Account Scoring

**Trigger Scoring**:
```bash
curl -X POST \
  https://REGION-PROJECT_ID.cloudfunctions.net/account-scoring \
  -H "Authorization: bearer $(gcloud auth print-identity-token)"
```

**Check Scoring Results**:
```sql
SELECT 
  account_id,
  priority_score,
  budget_likelihood,
  engagement_score,
  recommended_action
FROM `PROJECT_ID.sales_intelligence.account_recommendations`
WHERE score_date = CURRENT_DATE()
ORDER BY priority_score DESC
LIMIT 10
```

### 4. Update Secrets

**Update Salesforce Refresh Token**:
```bash
echo -n "NEW_REFRESH_TOKEN" | gcloud secrets versions add salesforce-refresh-token \
  --data-file=- \
  --project=PROJECT_ID
```

**Update API Key**:
```bash
echo -n "NEW_API_KEY" | gcloud secrets versions add dialpad-api-key \
  --data-file=- \
  --project=PROJECT_ID
```

---

## Troubleshooting

### Issue 1: ETL Job Failed

**Symptoms**:
- `etl_runs` table shows `status='failed'`
- Error message in `error_message` column

**Diagnosis**:
```sql
SELECT 
  source_system,
  status,
  error_message,
  started_at
FROM `PROJECT_ID.sales_intelligence.etl_runs`
WHERE status = 'failed'
ORDER BY started_at DESC
LIMIT 10
```

**Common Causes**:
1. **API Authentication Failed**
   - Check Secret Manager for valid credentials
   - Verify service account has Secret Manager access

2. **API Rate Limit Exceeded**
   - Wait and retry
   - Check API quota limits

3. **Network Timeout**
   - Check Cloud Function timeout settings
   - Increase timeout if needed

**Resolution**:
1. Check Cloud Logging for detailed error
2. Verify credentials in Secret Manager
3. Retry the job manually
4. If persistent, check API status pages

### Issue 2: Account Scoring Not Running

**Symptoms**:
- No records in `account_recommendations` for today
- Cloud Scheduler job not triggering

**Diagnosis**:
```bash
# Check Cloud Scheduler jobs
gcloud scheduler jobs list --project=PROJECT_ID

# Check job history
gcloud scheduler jobs describe account-scoring-daily --project=PROJECT_ID
```

**Resolution**:
1. Check Cloud Scheduler job status
2. Verify function exists and is accessible
3. Check IAM permissions for Cloud Scheduler
4. Manually trigger function to test

### Issue 3: Embeddings Not Generated

**Symptoms**:
- `embedding` column is NULL for many records
- Semantic search returns no results

**Diagnosis**:
```sql
SELECT 
  COUNT(*) as total,
  COUNTIF(embedding IS NULL) as without_embeddings
FROM `PROJECT_ID.sales_intelligence.gmail_messages`
WHERE sent_at >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
```

**Resolution**:
1. Trigger embedding generation manually
2. Check Vertex AI API is enabled
3. Verify service account has AI Platform User role
4. Check Cloud Function logs for errors

### Issue 4: Entity Resolution Low Match Rate

**Symptoms**:
- Low percentage of emails matched to contacts
- Many unmatched emails in view

**Diagnosis**:
```sql
SELECT 
  COUNT(*) as total_participants,
  COUNTIF(sf_contact_id IS NOT NULL) as matched,
  COUNTIF(sf_contact_id IS NULL) as unmatched,
  COUNTIF(sf_contact_id IS NOT NULL) * 100.0 / COUNT(*) as match_rate
FROM `PROJECT_ID.sales_intelligence.gmail_participants`
WHERE DATE(ingested_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
```

**Resolution**:
1. Re-run entity resolution job
2. Check for email normalization issues
3. Review manual mappings table
4. Verify Salesforce contact data is up to date

### Issue 5: Web Application Not Accessible

**Symptoms**:
- 502/503 errors
- Timeout errors
- Application not loading

**Diagnosis**:
```bash
# Check Cloud Run service
gcloud run services describe sales-intelligence-web --project=PROJECT_ID

# Check logs
gcloud logging read "resource.type=cloud_run_revision" \
  --limit=50 \
  --project=PROJECT_ID
```

**Resolution**:
1. Check Cloud Run service status
2. Verify service is deployed
3. Check IAM permissions
4. Review application logs
5. Restart service if needed

---

## Maintenance Tasks

### Weekly Tasks

1. **Review ETL Job Performance**
   - Check average execution times
   - Identify slow jobs
   - Optimize queries if needed

2. **Data Quality Review**
   - Check match rates
   - Review error logs
   - Verify data freshness

3. **Cost Review**
   - Review GCP billing
   - Check BigQuery usage
   - Optimize if needed

### Monthly Tasks

1. **Schema Updates**
   - Review table schemas
   - Add new fields if needed
   - Update documentation

2. **Performance Optimization**
   - Review query performance
   - Optimize slow queries
   - Update clustering/partitioning

3. **Security Review**
   - Rotate API keys
   - Review IAM permissions
   - Audit access logs

### Quarterly Tasks

1. **Data Retention**
   - Archive old data
   - Update retention policies
   - Clean up unused tables

2. **Capacity Planning**
   - Review growth trends
   - Plan for scaling
   - Update resource limits

---

## Emergency Procedures

### System Down

1. **Check Status**:
   ```bash
   # Check all Cloud Functions
   gcloud functions list --project=PROJECT_ID
   
   # Check BigQuery
   bq ls PROJECT_ID:sales_intelligence
   ```

2. **Restart Services**:
   ```bash
   # Redeploy function
   gcloud functions deploy FUNCTION_NAME --project=PROJECT_ID
   ```

3. **Rollback**:
   - Revert to previous deployment
   - Check git history for last known good state

### Data Corruption

1. **Identify Issue**:
   ```sql
   -- Check for duplicate records
   SELECT message_id, COUNT(*) as count
   FROM `PROJECT_ID.sales_intelligence.gmail_messages`
   GROUP BY message_id
   HAVING count > 1
   ```

2. **Restore from Backup**:
   - Use BigQuery table snapshots
   - Restore from previous day's data

3. **Re-run ETL**:
   - Re-sync affected data sources
   - Verify data integrity

### Security Incident

1. **Immediate Actions**:
   - Rotate all API keys
   - Revoke compromised credentials
   - Review access logs

2. **Investigation**:
   - Check Cloud Logging for suspicious activity
   - Review IAM permissions
   - Audit Secret Manager access

3. **Recovery**:
   - Update all secrets
   - Verify system integrity
   - Document incident

---

## Escalation

### When to Escalate

- System down for > 1 hour
- Data loss or corruption
- Security breach
- Cost overrun (> 50% of budget)

### Escalation Contacts

- **Technical Lead**: [Contact]
- **DevOps Team**: [Contact]
- **Security Team**: [Contact]
- **GCP Support**: [Contact]

---

## Appendix

### Useful Queries

**Top Accounts by Score**:
```sql
SELECT 
  a.account_name,
  r.priority_score,
  r.budget_likelihood,
  r.engagement_score,
  r.recommended_action
FROM `PROJECT_ID.sales_intelligence.account_recommendations` r
JOIN `PROJECT_ID.sales_intelligence.sf_accounts` a ON r.account_id = a.account_id
WHERE r.score_date = CURRENT_DATE()
ORDER BY r.priority_score DESC
LIMIT 20
```

**Unmatched Emails**:
```sql
SELECT 
  email_address,
  COUNT(*) as message_count,
  MAX(sent_at) as latest_message
FROM `PROJECT_ID.sales_intelligence.v_unmatched_emails`
GROUP BY email_address
ORDER BY message_count DESC
LIMIT 50
```

**ETL Performance**:
```sql
SELECT 
  source_system,
  DATE(started_at) as run_date,
  AVG(TIMESTAMP_DIFF(completed_at, started_at, SECOND)) as avg_seconds,
  MAX(TIMESTAMP_DIFF(completed_at, started_at, SECOND)) as max_seconds,
  AVG(rows_processed) as avg_rows
FROM `PROJECT_ID.sales_intelligence.etl_runs`
WHERE status = 'success'
  AND DATE(started_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY source_system, run_date
ORDER BY run_date DESC, source_system
```

---

## Conclusion

This runbook provides comprehensive operational procedures for the Sales Intelligence Automation System. Regular monitoring, proactive maintenance, and quick response to issues ensure system reliability and performance. Update this runbook as the system evolves and new procedures are established.
