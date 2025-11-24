# HubSpot API Key Fix - Summary

## Issues Fixed

### 1. Secret Value Whitespace Handling
**Problem**: Secret values from Secret Manager contained trailing newlines (`\r\n\r\n`), causing HTTP header validation errors.

**Error**: 
```
Invalid leading whitespace, reserved character(s), or return character(s) in header value: 'Bearer PLACEHOLDER\r\n\r\n'
```

**Solution**: 
- Updated `config/config.py` `get_secret()` method to strip whitespace from secret values
- Added validation to detect placeholder values and provide clear error messages

### 2. Placeholder Value Detection
**Problem**: Secret was set to "PLACEHOLDER" instead of a real HubSpot API key.

**Solution**: 
- Added validation in `hubspot_api_key` property to check for placeholder values
- Provides clear error message: "HubSpot API key is set to PLACEHOLDER. Please update 'hubspot-api-key' secret with a valid HubSpot Private App access token (format: pat-[region]-[token])."

## Code Changes

### `config/config.py`
```python
def get_secret(self, secret_id: str, version: str = "latest") -> str:
    # ... existing code ...
    secret_value = response.payload.data.decode("UTF-8").strip()
    return secret_value

@property
def hubspot_api_key(self) -> str:
    try:
        api_key = self.get_secret("hubspot-api-key")
        # Check if API key is a placeholder
        if not api_key or api_key.upper() in ["PLACEHOLDER", ""]:
            raise Exception("HubSpot API key is set to PLACEHOLDER. Please update 'hubspot-api-key' secret with a valid HubSpot Private App access token (format: pat-[region]-[token]).")
        return api_key
    except Exception as e:
        if "PLACEHOLDER" in str(e):
            raise
        raise Exception("HubSpot API key not found in Secret Manager. Please set 'hubspot-api-key' secret.")
```

### `scripts/add_hubspot_api_key.ps1`
- Updated to strip whitespace from user input before storing in Secret Manager

## Next Steps

### To Complete HubSpot Ingestion:

1. **Get HubSpot Private App Access Token**:
   - Log in to HubSpot
   - Go to Settings → Integrations → Private Apps
   - Create or open "Sales Intelligence System" app
   - Copy the access token (format: `pat-[region]-[token]`)
   - ⚠️ **Important**: Token is only shown once!

2. **Update Secret in Secret Manager**:
   ```powershell
   .\scripts\add_hubspot_api_key.ps1
   ```
   
   Or manually:
   ```powershell
   $apiKey = Read-Host "Enter HubSpot API key (pat-...)"
   $apiKey = $apiKey.Trim()  # Strip whitespace
   $tempFile = New-TemporaryFile
   $apiKey | Out-File -FilePath $tempFile -Encoding utf8 -NoNewline
   gcloud secrets versions add hubspot-api-key --data-file=$tempFile --project=maharani-sales-hub-11-2025
   Remove-Item $tempFile
   ```

3. **Test Ingestion**:
   ```powershell
   $token = gcloud auth print-access-token
   $url = "https://us-central1-maharani-sales-hub-11-2025.cloudfunctions.net/hubspot-sync"
   Invoke-RestMethod -Uri $url -Method Post -Headers @{"Authorization"="Bearer $token"; "Content-Type"="application/json"} -Body '{"sync_type":"full"}'
   ```

## Status

✅ **Code fixes deployed:**
- Secret whitespace stripping implemented
- Placeholder detection and error messages added
- Function redeployed with fixes (revision: hubspot-sync-00005-dur)

⚠️ **Action required:**
- Update `hubspot-api-key` secret with a valid HubSpot Private App access token

Once the API key is updated, HubSpot ingestion will work correctly!




