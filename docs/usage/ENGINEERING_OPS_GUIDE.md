# Engineering & Operations Guide

Safe system interaction, monitoring, and maintenance procedures.

## System Overview

```
┌──────────────────────────────────────────────────────────┐
│                    READ-ONLY LAYER                        │
│  Web App → BigQuery (queries only) → Display             │
└──────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────────────────────────────────────┐
│                    WRITE LAYER                            │
│  Cloud Scheduler → Cloud Functions → BigQuery (writes)   │
│  Cloud Functions → External APIs (Salesforce, HubSpot)   │
└──────────────────────────────────────────────────────────┘
```

## Safe Operations

### Read-Only Queries (Always Safe)

**BigQuery Console**:
```sql
-- Check data freshness
SELECT MAX(sent_at) FROM `PROJECT.sales_intelligence.gmail_messages`;

-- Check ETL status
SELECT * FROM `PROJECT.sales_intelligence.etl_runs` 
WHERE DATE(started_at) = CURRENT_DATE() ORDER BY started_at DESC;

-- Check account scores
SELECT COUNT(*), score_date FROM `PROJECT.sales_intelligence.account_recommendations`
GROUP BY score_date ORDER BY score_date DESC LIMIT 7;
```

**Cloud Logging**:
```bash
# View errors (read-only)
gcloud logging read "severity>=ERROR" --limit=50

# View function logs
gcloud functions logs read gmail-sync --limit=50
```

### Potentially Destructive Operations

⚠️ **Require approval before executing**:

| Operation | Risk Level | Approval Needed |
|-----------|------------|-----------------|
| Redeploy function | Medium | Team lead |
| Update secrets | High | Manager + security |
| Modify BigQuery schema | High | Manager |
| Delete/truncate tables | Critical | Manager + backup |
| Modify IAM roles | Critical | Security team |

---

## Daily Monitoring

### Health Check Script

```bash
#!/bin/bash
PROJECT_ID="your-project-id"

echo "=== ETL Status ==="
bq query --use_legacy_sql=false "
SELECT source_system, status, started_at
FROM \`$PROJECT_ID.sales_intelligence.etl_runs\`
WHERE DATE(started_at) = CURRENT_DATE()
ORDER BY started_at DESC
LIMIT 10"

echo "=== Function Status ==="
gcloud functions list --gen2 --region=us-central1

echo "=== Recent Errors ==="
gcloud logging read "severity>=ERROR" --limit=10 --format="table(timestamp,textPayload)"
```

### What to Check

| Check | Expected | Alert If |
|-------|----------|----------|
| ETL runs today | 5+ successful | 0 successful |
| Error count | < 5 | > 20 |
| Account scores | Today's date | > 1 day old |
| Function count | 13 functions | Any missing |

### Monitoring Queries

```sql
-- ETL success rate (last 7 days)
SELECT 
  DATE(started_at) as date,
  COUNTIF(status = 'success') as success,
  COUNTIF(status = 'failed') as failed
FROM `PROJECT.sales_intelligence.etl_runs`
WHERE started_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY date ORDER BY date DESC;

-- Data freshness
SELECT 
  'gmail_messages' as table_name,
  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(sent_at), HOUR) as hours_stale
FROM `PROJECT.sales_intelligence.gmail_messages`
UNION ALL
SELECT 'sf_accounts', TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(last_modified_date), HOUR)
FROM `PROJECT.sales_intelligence.sf_accounts`;
```

---

## Incident Response

### Severity Levels

| Level | Description | Response Time | Example |
|-------|-------------|---------------|---------|
| P1 | System down | 15 min | All functions failing |
| P2 | Major feature broken | 1 hour | Account scoring failed |
| P3 | Minor issue | 4 hours | One sync delayed |
| P4 | Low impact | 1 day | UI cosmetic issue |

### P1 Response Playbook

1. **Identify scope**
   ```bash
   gcloud functions list --gen2  # Check function status
   gcloud logging read "severity>=ERROR" --limit=20
   ```

2. **Check dependencies**
   - BigQuery status: console.cloud.google.com
   - Vertex AI status: status.cloud.google.com
   - External APIs (Salesforce, HubSpot status pages)

3. **Quick fixes** (safe operations)
   ```bash
   # Retry failed function
   gcloud functions call gmail-sync --gen2 --region=us-central1
   ```

4. **Escalate if needed**
   - Document timeline
   - Notify stakeholders
   - Engage GCP support if infrastructure issue

### Common Issues & Fixes

| Issue | Diagnosis | Fix |
|-------|-----------|-----|
| ETL stuck | Check function logs | Redeploy function |
| Auth error | Check secret versions | Update secret |
| Quota exceeded | Check API quotas | Wait or request increase |
| Memory limit | Check function logs | Increase memory |
| Timeout | Check duration | Increase timeout or optimize |

---

## Safe Deployment Procedures

### Before Deploying

1. ✅ Tested locally with `MOCK_MODE=1`
2. ✅ Code reviewed
3. ✅ No secret changes in code
4. ✅ Backup plan identified

### Deployment Checklist

```bash
# 1. Verify current state
gcloud functions describe FUNCTION_NAME --gen2 --region=us-central1

# 2. Deploy with explicit version
gcloud functions deploy FUNCTION_NAME \
  --gen2 \
  --region=us-central1 \
  --source=. \
  --runtime=python311

# 3. Verify deployment
gcloud functions describe FUNCTION_NAME --gen2 --region=us-central1

# 4. Test
gcloud functions call FUNCTION_NAME --gen2 --region=us-central1

# 5. Monitor logs
gcloud functions logs read FUNCTION_NAME --limit=20
```

### Rollback Procedure

```bash
# List revisions (Cloud Run backing)
gcloud run revisions list --service=FUNCTION_NAME --region=us-central1

# Route traffic to previous revision
gcloud run services update-traffic FUNCTION_NAME \
  --to-revisions=PREVIOUS_REVISION=100 \
  --region=us-central1
```

---

## Secret Management

### Safe Secret Operations

```bash
# View secret metadata (safe)
gcloud secrets describe salesforce-client-id

# List secret versions (safe)
gcloud secrets versions list salesforce-client-id

# Access secret value (safe, but log access)
gcloud secrets versions access latest --secret=salesforce-client-id
```

### Updating Secrets (Requires Approval)

```bash
# Add new version (doesn't delete old)
echo -n "NEW_VALUE" | gcloud secrets versions add SECRET_NAME --data-file=-

# Verify new version
gcloud secrets versions list SECRET_NAME

# Test with new version before disabling old
```

---

## BigQuery Operations

### Safe Queries

All SELECT queries are safe. Use the console or `bq query`.

### Schema Changes (Requires Approval)

```sql
-- Adding columns is safe
ALTER TABLE `PROJECT.sales_intelligence.table_name`
ADD COLUMN new_column STRING;

-- Modifying/deleting requires backup first
-- NEVER run DROP or TRUNCATE without explicit approval
```

### Data Backups

```bash
# Create table snapshot
bq cp PROJECT:sales_intelligence.table_name \
      PROJECT:sales_intelligence_backup.table_name_$(date +%Y%m%d)
```

---

## Access Control

### Required Roles for Ops

| Role | Purpose |
|------|---------|
| `roles/cloudfunctions.viewer` | View functions |
| `roles/logging.viewer` | View logs |
| `roles/bigquery.dataViewer` | Query data |
| `roles/bigquery.jobUser` | Run queries |

### Elevated Roles (Require Approval)

| Role | Purpose | When Needed |
|------|---------|-------------|
| `roles/cloudfunctions.admin` | Deploy | Releases |
| `roles/secretmanager.admin` | Update secrets | Credential rotation |
| `roles/bigquery.dataEditor` | Modify data | Schema changes |

---

## Maintenance Windows

### Preferred Times

- **ETL redeployments**: 6-7 AM (before scoring runs)
- **Schema changes**: Weekends
- **Secret rotation**: During business hours (for quick rollback)

### Pre-Maintenance Checklist

1. ☐ Notify stakeholders
2. ☐ Document current state
3. ☐ Prepare rollback plan
4. ☐ Test in non-prod if available
5. ☐ Monitor during and after

---

## Contacts

| Role | Contact | When to Reach |
|------|---------|---------------|
| On-call Ops | [Rotation] | P1/P2 incidents |
| Engineering Lead | [Name] | Technical decisions |
| Security | [Team] | Secret/IAM changes |
| GCP Support | console.cloud.google.com | Infrastructure issues |

---

## Quick Reference

```bash
# Safe commands (always okay)
gcloud functions list
gcloud functions logs read FUNC
gcloud logging read "severity>=ERROR"
bq query --use_legacy_sql=false "SELECT ..."

# Careful commands (check impact first)
gcloud functions call FUNC          # May trigger processing
gcloud functions deploy FUNC        # Changes live system
gcloud secrets versions add SECRET  # Credential change
```

---

For detailed troubleshooting, see [Troubleshooting Guide](../operations/TROUBLESHOOTING.md).

For operational procedures, see [Operations Runbook](../operations/RUNBOOK.md).

