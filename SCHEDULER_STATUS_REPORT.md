# Cloud Scheduler Status Report
**Generated:** 2025-11-28  
**Project:** maharani-sales-hub-11-2025  
**Location:** us-central1

---

## 📊 Summary

**Total Scheduler Jobs:** 13  
**Status:** All ENABLED  
**Last Check:** 2025-11-28

---

## 🔍 Status Code Reference

- **Code 4** = `DEADLINE_EXCEEDED` - Job timed out (function took too long)
- **Code 14** = `UNAVAILABLE` - Service temporarily unavailable
- **No Code** = `OK` - Job completed successfully

---

## 📋 Scheduler Jobs Details

### ✅ **Working Schedulers** (No Error Codes)

| Job Name | Schedule | Last Run | Status |
|----------|----------|----------|--------|
| `hubspot-sync` | Daily at 4 AM | 2025-11-27 09:00:15 | ✅ OK |
| `salesforce--2hourly` | Every 2 hours | 2025-11-28 00:00:16 | ✅ OK |
| `salesforce-full-sync` | Weekly (Sun 3 AM) | 2025-11-23 08:00:15 | ✅ OK |
| `hubspot-sync-daily` | Daily at 3 AM | 2025-11-27 11:00:12 | ✅ OK |
| `salesforce--hourly` | Every hour | 2025-11-28 01:00:16 | ✅ OK |
| `salesforce-incremental-sync` | Every 6 hours | 2025-11-27 23:00:16 | ✅ OK |
| `salesforce-emailmessage-daily` | Daily at 2 AM | 2025-11-27 10:00:16 | ✅ OK |
| `dialpad-sync-2hourly` | Every 2 hours | 2025-11-28 00:00:34 | ✅ OK |

---

### ⚠️ **Schedulers with Issues**

#### 1. **dialpad-sync** (Code 4: DEADLINE_EXCEEDED)
- **Schedule:** Daily at 1 AM (America/New_York)
- **Last Attempt:** 2025-11-27 06:13:21
- **Next Run:** 2025-11-28 06:00:03
- **Issue:** Function timing out (180s deadline exceeded)
- **Status:** ⚠️ **FIXED** - Code updated with max calls limit and early stopping
- **Action Required:** Redeploy function with fixes

**Configuration:**
```yaml
URI: https://us-central1-maharani-sales-hub-11-2025.cloudfunctions.net/dialpad-sync
Method: POST
Body: {"sync_type":"incremental"}
Service Account: sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com
Attempt Deadline: 180s
Retry: 3 attempts, max 600s
```

---

#### 2. **gmail-incremental-sync** (Code 14: UNAVAILABLE)
- **Schedule:** Every hour
- **Last Attempt:** 2025-11-28 01:11:25
- **Next Run:** 2025-11-28 02:00:00
- **Issue:** Service temporarily unavailable
- **Status:** ⚠️ **Monitoring** - May be transient issue

**Configuration:**
```yaml
URI: https://us-central1-maharani-sales-hub-11-2025.cloudfunctions.net/gmail-sync
Method: POST
Body: {"sync_type":"incremental"}
Service Account: sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com
Attempt Deadline: 180s
Retry: 3 attempts, max 600s
```

---

#### 3. **gmail-full-sync** (Code 14: UNAVAILABLE)
- **Schedule:** Daily at 2 AM (America/New_York)
- **Last Attempt:** 2025-11-27 07:29:40
- **Issue:** Service temporarily unavailable
- **Status:** ⚠️ **Monitoring** - May be transient issue

**Configuration:**
```yaml
URI: https://us-central1-maharani-sales-hub-11-2025.cloudfunctions.net/gmail-sync
Method: POST
Body: {"sync_type":"full"}
Service Account: sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com
Attempt Deadline: 180s
Retry: 3 attempts, max 600s
```

---

#### 4. **entity-resolution** (Code 4: DEADLINE_EXCEEDED)
- **Schedule:** Every 4 hours
- **Last Attempt:** 2025-11-28 01:09:48
- **Issue:** Function timing out (180s deadline exceeded)
- **Status:** ⚠️ **Needs Investigation** - May need timeout increase or optimization

**Configuration:**
```yaml
URI: https://us-central1-maharani-sales-hub-11-2025.cloudfunctions.net/entity-resolution
Method: POST
Body: {}
Service Account: sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com
Attempt Deadline: 180s
Retry: 3 attempts, max 600s
```

---

#### 5. **entity-resolution-daily** (Code 4: DEADLINE_EXCEEDED)
- **Schedule:** Daily at 4 AM (America/Los_Angeles)
- **Last Attempt:** 2025-11-27 12:03:00
- **Issue:** Function timing out (180s deadline exceeded)
- **Status:** ⚠️ **Needs Investigation** - Same as entity-resolution

**Configuration:**
```yaml
URI: https://us-central1-maharani-sales-hub-11-2025.cloudfunctions.net/entity-resolution
Method: POST
Body: {}
Service Account: sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com
Attempt Deadline: 180s
Retry: 3 attempts, max 600s
```

---

## 🔧 Recommended Actions

### Immediate Actions

1. **✅ Dialpad Sync - FIXED**
   - Code has been updated with timeout fixes
   - **Action:** Redeploy function once `run.services.setIamPolicy` permission is granted
   - **Expected Result:** Should complete within 180s deadline

2. **⚠️ Gmail Syncs - Monitor**
   - Code 14 (UNAVAILABLE) may be transient
   - **Action:** Monitor next few runs
   - **If persists:** Check function logs and Cloud Run service status

3. **⚠️ Entity Resolution - Investigate**
   - Both jobs timing out
   - **Action:** 
     - Check function logs for bottlenecks
     - Consider increasing `attemptDeadline` from 180s to 540s (matching function timeout)
     - Optimize entity resolution logic if needed

### Permission Requirements

To manage schedulers, the following permissions are needed:

**Current Status:**
- ✅ Can view scheduler jobs (`gcloud scheduler jobs list`)
- ✅ Can describe scheduler jobs (`gcloud scheduler jobs describe`)
- ❌ Cannot run jobs manually (`cloudscheduler.jobs.run` - PERMISSION_DENIED)
- ❌ Cannot update jobs (`cloudscheduler.jobs.update` - not tested, likely denied)

**Required Permissions:**
- `roles/cloudscheduler.jobRunner` - To manually trigger/test jobs
- `roles/cloudscheduler.jobs.editor` - To update job configurations (timeouts, schedules)

---

## 📝 Scheduler Configuration Summary

All schedulers use:
- **OIDC Authentication** with service account: `sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com`
- **Retry Configuration:**
  - Max retries: 3
  - Max retry duration: 600s
  - Min backoff: 5s
  - Max backoff: 3600s
- **Attempt Deadline:** 180s (may need increase for some functions)

---

## 🎯 Next Steps

1. **Request Permissions from Anand:**
   - `roles/run.developer` - To redeploy Dialpad function
   - `roles/cloudscheduler.jobRunner` - To test scheduler jobs manually
   - `roles/cloudscheduler.jobs.editor` - To update job configurations if needed

2. **After Permissions Granted:**
   - Redeploy Dialpad sync function with fixes
   - Test Dialpad scheduler manually
   - Investigate entity-resolution timeouts
   - Monitor Gmail sync availability

3. **Long-term:**
   - Consider increasing `attemptDeadline` for entity-resolution jobs
   - Set up monitoring/alerting for scheduler failures
   - Document scheduler run history and success rates

---

## 📊 Quick Reference Commands

```bash
# List all schedulers
gcloud scheduler jobs list --location=us-central1 --project=maharani-sales-hub-11-2025

# Describe a specific scheduler
gcloud scheduler jobs describe JOB_NAME --location=us-central1 --project=maharani-sales-hub-11-2025

# Run a scheduler manually (requires cloudscheduler.jobs.run permission)
gcloud scheduler jobs run JOB_NAME --location=us-central1 --project=maharani-sales-hub-11-2025

# Update attempt deadline (requires cloudscheduler.jobs.update permission)
gcloud scheduler jobs update http JOB_NAME \
  --location=us-central1 \
  --attempt-deadline=540s \
  --project=maharani-sales-hub-11-2025
```

---

**Report Generated:** 2025-11-28  
**Next Review:** After Dialpad function redeployment


