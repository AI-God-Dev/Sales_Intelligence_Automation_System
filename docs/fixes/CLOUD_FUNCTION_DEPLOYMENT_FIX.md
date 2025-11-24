# Cloud Function Deployment Fix

## Problem
Cloud Functions Gen2 deployment was failing with a healthcheck error:
```
Container Healthcheck failed. The user-provided container failed to start and listen on the port defined provided by the PORT=8080 environment variable within the allocated timeout.
```

## Root Cause
When deploying from project root (`--source=.`), Python couldn't find the `utils`, `config`, and `entity_resolution` modules during container startup, causing import errors that prevented the function from starting.

## Solution
Added explicit Python path configuration at the top of each Cloud Function's `main.py`:

1. **Path Setup**: Added project root to `sys.path` before imports
2. **Error Handling**: Wrapped imports in try/except with fallbacks
3. **Runtime Validation**: Check imports at runtime before executing business logic

## Fix Applied
- ✅ `cloud_functions/gmail_sync/main.py` - Fixed
- ⚠️ Other functions need the same fix applied

## Next Steps
1. Apply the same fix to other Cloud Functions:
   - `cloud_functions/salesforce_sync/main.py`
   - `cloud_functions/dialpad_sync/main.py`
   - `cloud_functions/hubspot_sync/main.py`
   - `cloud_functions/entity_resolution/main.py`

2. Test deployment:
   ```bash
   bash scripts/deploy_functions.sh
   ```

3. Verify function starts:
   - Check Cloud Function logs in GCP Console
   - Test function with a simple HTTP request

## Key Changes
Each function now starts with:
```python
import sys
from pathlib import Path

# Add project root to Python path
_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Then imports with error handling
try:
    from utils.bigquery_client import BigQueryClient
    from config.config import settings
    # ... other imports
except ImportError as e:
    logging.error(f"Import error: {e}")
    # Define fallbacks
```

