# Dialpad Sync Workaround - IMPLEMENTED ✅

## Problem
Dialpad API limitation: **Cannot filter by BOTH time range AND user_id together**
- `/api/v2/call?start_time=X&end_time=Y` → ✅ Works
- `/api/v2/call?user_id=Z` → ✅ Works  
- `/api/v2/call?start_time=X&end_time=Y&user_id=Z` → ❌ 400 Bad Request

## Solution Implemented
**Workaround Method**: Fetch all calls, then filter locally

### Implementation Details

1. **Fetch All Recent Calls** (no filters)
   - Endpoint: `/api/v2/call` or `/api/v2/calls`
   - Parameter: `limit=1000` (gets up to 1000 most recent calls)
   - No time or user filters in API call

2. **Filter by Date Locally** (for incremental sync)
   - Compare `date_started` (milliseconds timestamp) with last sync time
   - Filter calls that are newer than last sync

3. **Filter by User Locally** (if user_id provided)
   - Check `target.id` where `target.type == "user"`
   - Also check `user_id` and `owner_id` fields
   - Filter calls matching the requested user

4. **Transform and Insert**
   - Transform filtered calls to BigQuery format
   - Insert into `dialpad_calls` table

## Code Changes

### File: `cloud_functions/dialpad_sync/main.py`

**New Function**: `_sync_all_calls_workaround()`
- Implements the workaround method
- Handles date filtering locally
- Handles user filtering locally
- Supports both full and incremental syncs

**Updated**: `dialpad_sync()` main function
- Now calls `_sync_all_calls_workaround()` instead of per-user sync
- Works for both specific user and all users

## Testing

### Test Command
```powershell
$token = gcloud auth print-identity-token
$body = @{sync_type="full"} | ConvertTo-Json -Compress
Invoke-RestMethod -Uri "https://us-central1-maharani-sales-hub-11-2025.cloudfunctions.net/dialpad-sync" `
    -Method Post -Headers @{Authorization="Bearer $token"; "Content-Type"="application/json"} `
    -Body $body -TimeoutSec 300
```

### Expected Results
- Should fetch up to 1000 recent calls
- Should filter and sync all calls (or filtered by user if specified)
- Should show actual call volume (thousands of calls as client mentioned)

## Next Steps

1. **Deploy Updated Function**:
   ```powershell
   cd SALES
   gcloud functions deploy dialpad-sync --gen2 --region=us-central1 --runtime=python311 --source=cloud_functions/dialpad_sync --entry-point=dialpad_sync --trigger-http --allow-unauthenticated
   ```

2. **Test After Deployment**:
   - Run test command above
   - Check Cloud Function logs for details
   - Verify calls are syncing to BigQuery

3. **Verify in BigQuery**:
   ```sql
   SELECT COUNT(*) as total_calls
   FROM `maharani-sales-hub-11-2025.sales_intelligence.dialpad_calls`
   ```

## Benefits

✅ **Works around API limitation**  
✅ **Can fetch up to 1000 calls per sync**  
✅ **Efficient for daily/hourly incremental syncs**  
✅ **Filters locally (minimal overhead)**  
✅ **Supports both full and incremental syncs**  

## Limitations

- Limited to 1000 calls per fetch (enough for daily/hourly syncs)
- For historical backfill, may need multiple runs or Stats API

## Status

✅ **Code Updated**  
⏳ **Needs Deployment**  
⏳ **Needs Testing**

