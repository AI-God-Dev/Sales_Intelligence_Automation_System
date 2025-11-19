# 🔧 Fix "Resource Already Exists" (409) Errors

## ⚠️ Problem
You're getting 409 errors when running `terraform apply` because resources already exist in GCP but aren't in Terraform state.

## ✅ Solution: Import Existing Resources FIRST

**IMPORTANT:** You MUST import existing resources BEFORE running `terraform apply`!

---

## 📋 Step-by-Step Fix

### Step 1: Go to Infrastructure Directory

```powershell
cd infrastructure
```

### Step 2: Import Existing Resources

**On Windows (PowerShell):**
```powershell
.\import_existing_resources.ps1
```

**On Linux/Mac:**
```bash
chmod +x import_existing_resources.sh
./import_existing_resources.sh
```

### Step 3: Verify Import Worked

```bash
terraform state list
```

You should see resources like:
- `google_bigquery_dataset.sales_intelligence`
- `google_cloud_scheduler_job.gmail_incremental_sync`
- etc.

### Step 4: Now Run Terraform Plan (NOT apply yet!)

```bash
terraform plan
```

This should show NO errors about resources already existing.

### Step 5: If Plan Looks Good, Apply

```bash
terraform apply
```

---

## 🚨 If Import Script Fails

Run these commands manually:

### Import BigQuery Dataset
```bash
terraform import google_bigquery_dataset.sales_intelligence maharani-sales-hub-11-2025:sales_intelligence
```

### Import All Scheduler Jobs
```bash
terraform import google_cloud_scheduler_job.gmail_incremental_sync projects/maharani-sales-hub-11-2025/locations/us-central1/jobs/gmail-incremental-sync

terraform import google_cloud_scheduler_job.gmail_full_sync projects/maharani-sales-hub-11-2025/locations/us-central1/jobs/gmail-full-sync

terraform import google_cloud_scheduler_job.salesforce_incremental_sync projects/maharani-sales-hub-11-2025/locations/us-central1/jobs/salesforce-incremental-sync

terraform import google_cloud_scheduler_job.salesforce_full_sync projects/maharani-sales-hub-11-2025/locations/us-central1/jobs/salesforce-full-sync

terraform import google_cloud_scheduler_job.dialpad_sync projects/maharani-sales-hub-11-2025/locations/us-central1/jobs/dialpad-sync

terraform import google_cloud_scheduler_job.hubspot_sync projects/maharani-sales-hub-11-2025/locations/us-central1/jobs/hubspot-sync

terraform import google_cloud_scheduler_job.entity_resolution projects/maharani-sales-hub-11-2025/locations/us-central1/jobs/entity-resolution
```

---

## ⚡ Quick Fix (Copy & Paste)

If you're in PowerShell in the `infrastructure` directory, run this:

```powershell
$projectId = "maharani-sales-hub-11-2025"
$region = "us-central1"

# Import BigQuery
terraform import google_bigquery_dataset.sales_intelligence "$projectId`:sales_intelligence"

# Import Scheduler Jobs
terraform import google_cloud_scheduler_job.gmail_incremental_sync "projects/$projectId/locations/$region/jobs/gmail-incremental-sync"
terraform import google_cloud_scheduler_job.gmail_full_sync "projects/$projectId/locations/$region/jobs/gmail-full-sync"
terraform import google_cloud_scheduler_job.salesforce_incremental_sync "projects/$projectId/locations/$region/jobs/salesforce-incremental-sync"
terraform import google_cloud_scheduler_job.salesforce_full_sync "projects/$projectId/locations/$region/jobs/salesforce-full-sync"
terraform import google_cloud_scheduler_job.dialpad_sync "projects/$projectId/locations/$region/jobs/dialpad-sync"
terraform import google_cloud_scheduler_job.hubspot_sync "projects/$projectId/locations/$region/jobs/hubspot-sync"
terraform import google_cloud_scheduler_job.entity_resolution "projects/$projectId/locations/$region/jobs/entity-resolution"
```

Then run:
```bash
terraform plan
terraform apply
```

---

## ✅ Success Criteria

After importing, when you run `terraform plan`, you should:
- ✅ See NO "already exists" errors
- ✅ See only resource differences (if any)
- ✅ Be able to run `terraform apply` successfully

---

## 📞 Still Having Issues?

If import fails, check:
1. Are you in the `infrastructure` directory?
2. Is Terraform initialized? (`terraform init`)
3. Are you authenticated with GCP? (`gcloud auth list`)
4. Does the resource actually exist in GCP?

