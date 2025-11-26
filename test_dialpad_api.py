import os
import requests
from google.cloud import secretmanager

# Get API key from Secret Manager
client = secretmanager.SecretManagerServiceClient()
project_id = "maharani-sales-hub-11-2025"
secret_id = "dialpad-api-key"
name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
response = client.access_secret_version(request={"name": name})
api_key = response.payload.data.decode("UTF-8")

# Test API
base_url = "https://dialpad.com/api/v2"
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

# Test /call endpoint
print("Testing /call endpoint...")
response = requests.get(f"{base_url}/call", headers=headers, params={"limit": 1000}, timeout=60)
print(f"Status: {response.status_code}")
print(f"URL: {response.url}")
if response.status_code == 200:
    data = response.json()
    print(f"Response type: {type(data)}")
    if isinstance(data, dict):
        print(f"Keys: {list(data.keys())}")
        for key in ["items", "calls", "data", "results"]:
            if key in data:
                items = data[key]
                print(f"{key}: {len(items)} items")
    elif isinstance(data, list):
        print(f"List with {len(data)} items")
else:
    print(f"Error: {response.text[:500]}")
