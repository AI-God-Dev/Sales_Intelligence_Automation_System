# Phase 2 Deployment Status

## ⚠️ Deployment Blocked - Permission Required

### Issue
All Phase 2 function deployments are failing due to missing IAM permission:

```
ERROR: Caller is missing permission 'iam.serviceaccounts.actAs' on service account
```

### Required Permission
The current user needs the `roles/iam.serviceAccountUser` role on the service account to deploy functions.

### Solution

**Ask Anand to run this command** (replace `YOUR_EMAIL` with your actual email):

```powershell
$PROJECT_ID = "maharani-sales-hub-11-2025"
$SERVICE_ACCOUNT = "sales-intel-poc-sa@${PROJECT_ID}.iam.gserviceaccount.com"
$USER_EMAIL = "YOUR_EMAIL@example.com"  # Replace with actual email

gcloud iam service-accounts add-iam-policy-binding $SERVICE_ACCOUNT `
  --member="user:$USER_EMAIL" `
  --role="roles/iam.serviceAccountUser" `
  --project=$PROJECT_ID
```

Or grant the role via GCP Console:
1. Go to IAM & Admin > Service Accounts
2. Find `sales-intel-poc-sa`
3. Click "Grant Access"
4. Add your email with role: **Service Account User**

---

## 📋 Functions Ready to Deploy

All 8 Phase 2 functions are ready:

1. ✅ **generate-embeddings** - Code ready
2. ✅ **account-scoring** - Code ready (needs 2048MB)
3. ✅ **nlp-query** - Code ready
4. ✅ **semantic-search** - Code ready
5. ✅ **create-leads** - Code ready
6. ✅ **enroll-hubspot** - Code ready
7. ✅ **get-hubspot-sequences** - Code ready
8. ✅ **generate-email-reply** - Code ready

### Deployment Script Status
- ✅ Script fixed (path resolution)
- ✅ All entry points verified
- ✅ Memory allocations correct
- ✅ Environment variables set
- ⏳ Waiting for IAM permission

---

## 🚀 After Permission is Granted

Once Anand grants the permission, run:

```powershell
cd C:\Users\Administrator\Desktop\Projects\SALES
.\scripts\deploy_phase2_functions.ps1
```

This will deploy all 8 functions.

---

## 📊 Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| Code | ✅ Ready | All functions reviewed and refined |
| Deployment Script | ✅ Fixed | Path resolution corrected |
| Entry Points | ✅ Verified | All match correctly |
| Requirements | ✅ Complete | All dependencies present |
| IAM Permission | ❌ Blocked | Need `roles/iam.serviceAccountUser` |
| Deployment | ⏳ Pending | Waiting for permission |

---

## 🔍 Verification Steps (After Deployment)

Once deployed, verify each function:

```powershell
# List all functions
gcloud run services list --region=us-central1 --project=maharani-sales-hub-11-2025

# Check specific function
gcloud functions describe generate-embeddings --gen2 --region=us-central1 --project=maharani-sales-hub-11-2025

# Test function
gcloud functions call nlp-query --gen2 --region=us-central1 --project=maharani-sales-hub-11-2025 --data='{"query": "test"}'
```

---

**Next Action**: Contact Anand to grant `roles/iam.serviceAccountUser` permission

