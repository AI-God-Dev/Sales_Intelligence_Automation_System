# Alternative Ways to Test Account Scoring Function

## Option 1: Test via gcloud Command (Works Now)
Test the function directly using gcloud, which handles authentication automatically:

```bash
# Test account-scoring function
gcloud functions call account-scoring \
  --gen2 \
  --region=us-central1 \
  --project=maharani-sales-hub-11-2025 \
  --data='{}'
```

Or using Cloud Run service directly:
```bash
# Get the service URL
SERVICE_URL=$(gcloud functions describe account-scoring --gen2 --region=us-central1 --project=maharani-sales-hub-11-2025 --format="value(serviceConfig.uri)")

# Call it using gcloud run services call
gcloud run services call account-scoring \
  --region=us-central1 \
  --project=maharani-sales-hub-11-2025 \
  --data='{}'
```

## Option 2: Create a Test Script Using gcloud Subprocess
Create a Python script that calls the function via gcloud command:

```python
import subprocess
import json

def test_account_scoring():
    result = subprocess.run(
        [
            "gcloud", "functions", "call", "account-scoring",
            "--gen2",
            "--region=us-central1",
            "--project=maharani-sales-hub-11-2025",
            "--data", "{}"
        ],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    return result.returncode == 0
```

## Option 3: Temporarily Modify Web App to Use gcloud Command
We can modify the `call_function` in `web_app/app.py` to use gcloud command as a fallback when authentication fails. This would work immediately.

## Option 4: Test Function Logic Locally
Run the account scoring logic locally against BigQuery to verify it works, then we know the function will work once authentication is fixed.

## Option 5: Use Cloud Run Proxy (Advanced)
Use `gcloud run services proxy` to create a local proxy that handles authentication:

```bash
gcloud run services proxy account-scoring \
  --region=us-central1 \
  --project=maharani-sales-hub-11-2025 \
  --port=8080
```

Then the web app can call `http://localhost:8080` without authentication issues.

## Recommended: Option 3 (Modify Web App to Use gcloud Fallback)
This is the quickest solution that doesn't require waiting for Anand. We can update the web app to use `gcloud functions call` as a fallback when direct HTTP authentication fails.

