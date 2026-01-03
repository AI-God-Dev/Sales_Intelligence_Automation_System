# Operations Runbook

Day-to-day operational procedures for the Sales Intelligence Automation System.

## Daily Health Check

**Time**: 8:00 AM (after account scoring completes)

### Checklist
- [ ] Account scoring completed
- [ ] All ETL jobs succeeded
- [ ] No critical errors in logs
- [ ] Web application accessible

### Commands

```bash
# Check ETL status
bq query --use_legacy_sql=false "
SELECT source_system, status, started_at, rows_processed
FROM \`PROJECT_ID.sales_intelligence.etl_runs\`
WHERE DATE(started_at) = CURRENT_DATE()
ORDER BY started_at DESC
"

# Check account scoring
bq query --use_legacy_sql=false "
SELECT COUNT(*) as accounts_scored
FROM \`PROJECT_ID.sales_intelligence.account_recommendations\`
WHERE score_date = CURRENT_DATE()
"

# Check for errors
gcloud logging read "severity>=ERROR" --limit=20
```

---

## Common Operations

### Manual ETL Trigger

```bash
# Gmail sync
gcloud functions call gmail-sync --gen2 --region=us-central1

# Salesforce sync
gcloud functions call salesforce-sync --gen2 --region=us-central1 \
  --data='{"object_type": "Account"}'

# Entity resolution
gcloud functions call entity-resolution --gen2 --region=us-central1

# Account scoring
gcloud functions call account-scoring --gen2 --region=us-central1

# Generate embeddings
gcloud functions call generate-embeddings --gen2 --region=us-central1
```

### Update Secrets

```bash
# Update Salesforce refresh token
echo -n "NEW_TOKEN" | gcloud secrets versions add salesforce-refresh-token --data-file=-

# Update API key
echo -n "NEW_KEY" | gcloud secrets versions add dialpad-api-key --data-file=-
```

### View Logs

```bash
# Function logs
gcloud functions logs read gmail-sync --gen2 --region=us-central1 --limit=50

# All errors
gcloud logging read "severity>=ERROR" --limit=50

# Specific function
gcloud logging read 'resource.labels.function_name="account-scoring"' --limit=50
```

---

## Monitoring Queries

### ETL Performance

```sql
SELECT 
  source_system,
  DATE(started_at) as run_date,
  AVG(TIMESTAMP_DIFF(completed_at, started_at, SECOND)) as avg_seconds,
  AVG(rows_processed) as avg_rows
FROM `PROJECT_ID.sales_intelligence.etl_runs`
WHERE status = 'success'
  AND DATE(started_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY source_system, run_date
ORDER BY run_date DESC
```

### Data Freshness

```sql
SELECT 
  'gmail_messages' as table_name,
  MAX(sent_at) as latest_record,
  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(sent_at), HOUR) as hours_old
FROM `PROJECT_ID.sales_intelligence.gmail_messages`
UNION ALL
SELECT 
  'sf_accounts',
  MAX(last_modified_date),
  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(last_modified_date), HOUR)
FROM `PROJECT_ID.sales_intelligence.sf_accounts`
```

### Entity Resolution Rate

```sql
SELECT 
  COUNTIF(sf_contact_id IS NOT NULL) * 100.0 / COUNT(*) as match_rate
FROM `PROJECT_ID.sales_intelligence.gmail_participants`
WHERE DATE(ingested_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
```

### Top Priority Accounts

```sql
SELECT 
  a.account_name,
  r.priority_score,
  r.budget_likelihood,
  r.recommended_action
FROM `PROJECT_ID.sales_intelligence.account_recommendations` r
JOIN `PROJECT_ID.sales_intelligence.sf_accounts` a ON r.account_id = a.account_id
WHERE r.score_date = CURRENT_DATE()
ORDER BY r.priority_score DESC
LIMIT 20
```

---

## Weekly Tasks

1. **Review ETL Performance**
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

---

## Monthly Tasks

1. **Security Review**
   - Rotate API keys
   - Review IAM permissions
   - Audit access logs

2. **Performance Optimization**
   - Review query performance
   - Update clustering/partitioning

3. **Schema Updates**
   - Review table schemas
   - Add new fields if needed

---

## Emergency Procedures

### System Down

```bash
# Check function status
gcloud functions list --gen2 --region=us-central1

# Check Cloud Run
gcloud run services describe sales-intelligence-web --region=us-central1

# Redeploy if needed
gcloud functions deploy FUNCTION_NAME --gen2 --region=us-central1 --source=.
```

### Data Issues

```bash
# Check for duplicates
bq query --use_legacy_sql=false "
SELECT message_id, COUNT(*) as count
FROM \`PROJECT_ID.sales_intelligence.gmail_messages\`
GROUP BY message_id
HAVING count > 1
"

# Re-sync data
gcloud functions call gmail-sync --gen2 --region=us-central1 \
  --data='{"sync_type": "full"}'
```

### Security Incident

1. Rotate all API keys immediately
2. Revoke compromised credentials
3. Review access logs
4. Update all secrets
5. Document incident

---

## Scheduled Jobs

| Job | Schedule | Function | Purpose |
|-----|----------|----------|---------|
| Gmail Sync | Hourly | `gmail-sync` | Email ingestion |
| Salesforce Sync | 2 AM | `salesforce-sync` | CRM sync |
| Dialpad Sync | 3 AM | `dialpad-sync` | Call sync |
| HubSpot Sync | 4 AM | `hubspot-sync` | Sequence sync |
| Account Scoring | 7 AM | `account-scoring` | Daily scores |
| Embeddings | 8 AM | `generate-embeddings` | Vector generation |

### Manage Jobs

```bash
# List jobs
gcloud scheduler jobs list --location=us-central1

# Run job manually
gcloud scheduler jobs run account-scoring-daily --location=us-central1

# Pause job
gcloud scheduler jobs pause account-scoring-daily --location=us-central1

# Resume job
gcloud scheduler jobs resume account-scoring-daily --location=us-central1
```

---

## Escalation

### When to Escalate
- System down > 1 hour
- Data loss or corruption
- Security breach
- Cost overrun > 50%

### Contacts
- Technical Lead: [Contact]
- DevOps Team: [Contact]
- GCP Support: [Link]

---

See [Troubleshooting](TROUBLESHOOTING.md) for issue resolution.

