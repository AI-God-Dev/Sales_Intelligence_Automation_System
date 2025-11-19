# Fix Terraform "Resource Already Exists" Errors

## Problem
When running `terraform apply`, you get 409 errors saying resources already exist:
- BigQuery dataset already exists
- Cloud Scheduler jobs already exist  
- Pub/Sub topics/subscriptions already exist

## Solution: Import Existing Resources

You need to import existing resources into Terraform state BEFORE running `terraform apply`.

### Step 1: Navigate to Infrastructure Directory

```powershell
cd infrastructure
```

### Step 2: Run Import Script

**On Windows (PowerShell):**
```powershell
.\import_existing_resources.ps1
```

**On Linux/Mac (Bash):**
```bash
chmod +x import_existing_resources.sh
./import_existing_resources.sh
```

### Step 3: Verify Imports

```bash
terraform state list
```

You should see imported resources like:
- `google_bigquery_dataset.sales_intelligence`
- `google_cloud_scheduler_job.gmail_incremental_sync`
- etc.

### Step 4: Run Terraform Plan

```bash
terraform plan
```

This should now show NO errors about resources already existing. It will only show differences (if any).

### Step 5: Apply (if needed)

```bash
terraform apply
```

---

## Alternative: Manual Import

If the import script doesn't work, import resources manually:

### Import BigQuery Dataset
```bash
terraform import google_bigquery_dataset.sales_intelligence maharani-sales-hub-11-2025:sales_intelligence
```

### Import Cloud Scheduler Jobs
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

## Troubleshooting

### If Import Fails

1. **Check if resource exists in GCP:**
   ```bash
   # For BigQuery
   bq ls -d --project_id=maharani-sales-hub-11-2025 sales_intelligence
   
   # For Scheduler Jobs
   gcloud scheduler jobs list --location=us-central1 --project=maharani-sales-hub-11-2025
   ```

2. **If resource doesn't exist, remove from Terraform config temporarily:**
   - Comment out the resource in the `.tf` file
   - Run `terraform plan` to verify
   - Re-enable after creating the resource manually

3. **If import succeeds but plan still shows issues:**
   ```bash
   terraform refresh
   terraform plan
   ```

---

## Quick Fix Script (All-in-One)

Run this PowerShell script from the infrastructure directory:

```powershell
$projectId = "maharani-sales-hub-11-2025"
$region = "us-central1"

# Import BigQuery dataset
Write-Host "Importing BigQuery dataset..." -ForegroundColor Yellow
terraform import google_bigquery_dataset.sales_intelligence "$projectId`:sales_intelligence" 2>$null
if ($LASTEXITCODE -eq 0) { Write-Host "  ✓ Imported" -ForegroundColor Green }

# Import all scheduler jobs
$jobs = @("gmail-incremental-sync", "gmail-full-sync", "salesforce-incremental-sync", "salesforce-full-sync", "dialpad-sync", "hubspot-sync", "entity-resolution")
foreach ($job in $jobs) {
    $resource = $job -replace '-', '_'
    Write-Host "Importing $job..." -ForegroundColor Yellow
    terraform import "google_cloud_scheduler_job.$resource" "projects/$projectId/locations/$region/jobs/$job" 2>$null
    if ($LASTEXITCODE -eq 0) { Write-Host "  ✓ Imported" -ForegroundColor Green }
}

Write-Host "`nDone! Now run: terraform plan" -ForegroundColor Cyan
```

---

## Next Steps After Import

1. **Verify state:**
   ```bash
   terraform state list
   ```

2. **Check for differences:**
   ```bash
   terraform plan
   ```

3. **Apply changes (if any):**
   ```bash
   terraform apply
   ```

---

## Prevention for Future

To avoid this issue in the future:
1. Always use Terraform from the start for new resources
2. Import existing resources before managing them with Terraform
3. Use `terraform plan` to verify before `terraform apply`

