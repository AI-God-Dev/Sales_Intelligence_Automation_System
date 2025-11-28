"""Test BigQuery initialization to diagnose the issue."""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment
os.environ["GCP_PROJECT_ID"] = "maharani-sales-hub-11-2025"

print("=" * 60)
print("BigQuery Initialization Test")
print("=" * 60)

try:
    print("\n1. Testing google.auth.default()...")
    from google.auth import default
    credentials, project = default()
    print(f"   ✅ ADC working! Project: {project}")
except Exception as e:
    print(f"   ❌ ADC failed: {e}")
    sys.exit(1)

try:
    print("\n2. Testing BigQueryClient import...")
    from utils.bigquery_client import BigQueryClient
    print("   ✅ Import successful")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n3. Testing BigQueryClient initialization...")
    client = BigQueryClient(project_id="maharani-sales-hub-11-2025")
    print("   ✅ Client created")
except Exception as e:
    print(f"   ❌ Initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n4. Testing BigQuery query...")
    result = client.query("SELECT 1 as test", max_results=1)
    print(f"   ✅ Query successful: {result}")
except Exception as e:
    print(f"   ❌ Query failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ All tests passed! BigQuery should work in Streamlit.")
print("=" * 60)

