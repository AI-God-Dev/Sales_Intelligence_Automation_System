# Troubleshooting Guide

## Common Issues and Solutions

### Cloud Functions

#### Function Deployment Fails

**Symptoms**: `gcloud functions deploy` fails with permission errors

**Solutions**:
1. Verify IAM permissions:
   ```bash
   gcloud projects get-iam-policy PROJECT_ID
   ```
2. Ensure service account has required roles
3. Check Cloud Functions API is enabled:
   ```bash
   gcloud services enable cloudfunctions.googleapis.com
   ```

#### Function Timeout

**Symptoms**: Functions timeout before completing

**Solutions**:
1. Increase timeout in deployment:
   ```bash
   gcloud functions deploy FUNCTION_NAME --timeout=540s
   ```
2. Optimize code for batch processing
3. Check for infinite loops or blocking operations

#### Function Not Triggering

**Symptoms**: Scheduled functions don't run

**Solutions**:
1. Check Cloud Scheduler job status:
   ```bash
   gcloud scheduler jobs describe JOB_NAME --location=LOCATION
   ```
2. Verify OAuth service account permissions
3. Check function logs for errors

### BigQuery

#### Permission Denied Errors

**Symptoms**: `403 Forbidden` when querying BigQuery

**Solutions**:
1. Verify service account has BigQuery Data Editor role
2. Check dataset access controls
3. Ensure project has BigQuery API enabled

#### Query Timeout

**Symptoms**: Queries take too long or timeout

**Solutions**:
1. Optimize query (add WHERE clauses, use LIMIT)
2. Check table partitioning and clustering
3. Increase query timeout in configuration
4. Use query result caching

#### Table Not Found

**Symptoms**: `404 Not found` when accessing tables

**Solutions**:
1. Verify table exists:
   ```bash
   bq ls DATASET_ID
   ```
2. Check table name spelling
3. Ensure tables were created successfully

### Secret Manager

#### Secret Not Found

**Symptoms**: `404 Secret not found` errors

**Solutions**:
1. Verify secret exists:
   ```bash
   gcloud secrets list
   ```
2. Check secret name spelling
3. Ensure service account has Secret Manager Secret Accessor role

#### Permission Denied Accessing Secrets

**Symptoms**: `403 Permission denied` when accessing secrets

**Solutions**:
1. Grant Secret Manager Secret Accessor role:
   ```bash
   gcloud secrets add-iam-policy-binding SECRET_NAME \
     --member="serviceAccount:SERVICE_ACCOUNT" \
     --role="roles/secretmanager.secretAccessor"
   ```

### API Integrations

#### Gmail API Rate Limits

**Symptoms**: `429 Too Many Requests` errors

**Solutions**:
1. Implement exponential backoff (already in code)
2. Reduce batch sizes
3. Request quota increase from Google
4. Use incremental sync instead of full sync

#### Salesforce API Errors

**Symptoms**: Authentication or query failures

**Solutions**:
1. Verify credentials in Secret Manager
2. Check security token is correct
3. Ensure IP is whitelisted (if required)
4. Verify object permissions in Salesforce

#### Dialpad API Errors

**Symptoms**: Call logs not syncing

**Solutions**:
1. Verify API key is correct
2. Check API plan includes transcript access
3. Verify user IDs are correct
4. Check API rate limits

### Data Quality

#### Low Entity Resolution Accuracy

**Symptoms**: Match percentage below 90%

**Solutions**:
1. Review unmatched records in UI
2. Add manual mappings for common cases
3. Improve email/phone normalization
4. Run weekly reconciliation job

#### Missing Data

**Symptoms**: Expected data not appearing in BigQuery

**Solutions**:
1. Check ETL run logs:
   ```bash
   bq query "SELECT * FROM etl_runs ORDER BY started_at DESC LIMIT 10"
   ```
2. Verify source system connectivity
3. Check for errors in Cloud Function logs
4. Verify sync schedules are running

### Performance

#### Slow Query Performance

**Symptoms**: Queries take >10 seconds

**Solutions**:
1. Add appropriate indexes/clustering
2. Use query result caching
3. Optimize SQL queries
4. Consider materialized views for common queries

#### High Cloud Function Costs

**Symptoms**: Unexpected GCP charges

**Solutions**:
1. Review function execution times
2. Optimize batch sizes
3. Implement caching to reduce API calls
4. Set up billing alerts

## Getting Help

1. Check logs:
   ```bash
   gcloud functions logs read FUNCTION_NAME --limit=50
   ```

2. Review ETL runs:
   ```bash
   bq query "SELECT * FROM etl_runs WHERE status='failed' ORDER BY started_at DESC"
   ```

3. Check monitoring dashboards in GCP Console

4. Open an issue on GitHub with:
   - Error messages
   - Relevant logs
   - Steps to reproduce
   - Environment details

## Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or set environment variable:
```bash
export LOG_LEVEL=DEBUG
```

