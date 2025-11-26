# Quick Start - Real-World Data Sync

## 🚀 One Command to Get Started

```powershell
cd SALES\scripts
.\MASTER_SYNC.ps1 full
```

This single command will:
1. ✅ Check prerequisites
2. ✅ Trigger all syncs (Salesforce, Dialpad, HubSpot)
3. ✅ Verify data in BigQuery
4. ✅ Check entity resolution
5. ✅ Provide comprehensive report

## 📋 Three Simple Commands

### 1. Check Status (No Syncs)
```powershell
cd SALES\scripts
.\MASTER_SYNC.ps1 validate
```
Quick health check - shows recent sync activity and data counts.

### 2. Run Syncs
```powershell
cd SALES\scripts
.\MASTER_SYNC.ps1 sync
```
Runs all syncs in proper order with retry logic.

### 3. Full Validation
```powershell
cd SALES\scripts
.\MASTER_SYNC.ps1 full
```
Complete validation + sync + verification.

## 🎯 What Gets Synced

### Salesforce (7 Objects)
- Account, Contact, Lead, Opportunity
- Task, Event, EmailMessage

### Dialpad
- Call logs from all users
- Call transcripts (when available)
- Phone numbers (normalized)

### HubSpot
- Marketing sequences
- Enrollment counts
- Sequence status

### Entity Resolution
- Email → Contact matching
- Phone → Contact matching

## 📊 Verify Results

After running syncs, check:

```powershell
# Quick status
.\MASTER_SYNC.ps1 validate

# Or query BigQuery
bq query --use_legacy_sql=false "
SELECT 
  source_system,
  status,
  rows_processed,
  started_at
FROM \`maharani-sales-hub-11-2025.sales_intelligence.etl_runs\`
ORDER BY started_at DESC
LIMIT 10
"
```

## 🔧 Troubleshooting

### Sync Failed?
1. Check logs: `gcloud functions logs read FUNCTION_NAME --gen2 --region=us-central1`
2. Verify secrets: `gcloud secrets list`
3. Check authentication: `gcloud auth list`

### No Data?
1. Verify secrets are set correctly
2. Check Cloud Function status
3. Review ETL runs table for errors

### Need Help?
- See `docs/REAL_WORLD_SYNC_GUIDE.md` for detailed guide
- See `REAL_WORLD_SYNC_COMPLETE.md` for technical details

## ✅ Success Indicators

After running syncs, you should see:
- ✅ All sync functions return success
- ✅ Data counts > 0 in BigQuery tables
- ✅ ETL runs show "success" status
- ✅ Entity resolution match rates > 0%

## 🎉 You're Ready!

Everything is set up. Just run:

```powershell
cd SALES\scripts
.\MASTER_SYNC.ps1 full
```

And you're done! 🚀

