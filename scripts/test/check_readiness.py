"""
Readiness Check Script
Verifies that all prerequisites are met before testing the integrations.
"""
import os
import sys
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from google.cloud import secretmanager
    from google.cloud import bigquery
    from google.cloud import pubsub_v1
    SECRET_MANAGER_AVAILABLE = True
except ImportError:
    SECRET_MANAGER_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReadinessChecker:
    """Checks if the system is ready for testing."""
    
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.issues = []
        self.warnings = []
        self.successes = []
    
    def check_project_id(self) -> bool:
        """Check if GCP_PROJECT_ID is set."""
        if not self.project_id:
            self.issues.append("GCP_PROJECT_ID environment variable is not set")
            return False
        self.successes.append(f"✓ GCP_PROJECT_ID is set: {self.project_id}")
        return True
    
    def check_dependencies(self) -> bool:
        """Check if required Python packages are installed."""
        required_packages = [
            "google-cloud-secret-manager",
            "google-cloud-bigquery",
            "google-cloud-pubsub",
            "google-api-python-client",
            "google-auth-oauthlib",
            "requests"
        ]
        
        missing = []
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                missing.append(package)
        
        if missing:
            self.issues.append(f"Missing Python packages: {', '.join(missing)}")
            self.issues.append(f"Install with: pip install {' '.join(missing)}")
            return False
        
        self.successes.append("✓ All required Python packages are installed")
        return True
    
    def check_secrets(self) -> bool:
        """Check if required secrets exist in Secret Manager."""
        if not SECRET_MANAGER_AVAILABLE:
            self.issues.append("google-cloud-secret-manager package not installed")
            return False
        
        if not self.project_id:
            return False
        
        required_secrets = [
            "hubspot_access_token",
            "gmail_oauth_client_id_anand",
            "gmail_oauth_client_secret_anand",
            "gmail_oauth_refresh_token_anand",
            "gmail_oauth_client_id_larnie",
            "gmail_oauth_client_secret_larnie",
            "gmail_oauth_refresh_token_larnie",
            "gmail_oauth_client_id_lia",
            "gmail_oauth_client_secret_lia",
            "gmail_oauth_refresh_token_lia",
            "salesforce_client_id",
            "salesforce_client_secret",
            "salesforce_refresh_token",
            "dialpad_api_key"
        ]
        
        try:
            client = secretmanager.SecretManagerServiceClient()
            missing_secrets = []
            
            for secret_id in required_secrets:
                try:
                    name = f"projects/{self.project_id}/secrets/{secret_id}"
                    client.get_secret(request={"name": name})
                except Exception:
                    missing_secrets.append(secret_id)
            
            if missing_secrets:
                self.issues.append(f"Missing secrets in Secret Manager: {', '.join(missing_secrets)}")
                self.issues.append("Create them using: gcloud secrets create SECRET_NAME --data-file=-")
                return False
            
            self.successes.append(f"✓ All {len(required_secrets)} required secrets exist in Secret Manager")
            return True
            
        except Exception as e:
            self.warnings.append(f"Could not verify secrets (may need authentication): {e}")
            return False
    
    def check_service_account(self) -> bool:
        """Check if service account exists and has permissions."""
        if not self.project_id:
            return False
        
        service_account = f"sales-intel-poc-sa@{self.project_id}.iam.gserviceaccount.com"
        
        try:
            import subprocess
            result = subprocess.run(
                [
                    "gcloud", "iam", "service-accounts", "describe",
                    service_account,
                    f"--project={self.project_id}"
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.successes.append(f"✓ Service account exists: {service_account}")
                return True
            else:
                self.issues.append(f"Service account does not exist: {service_account}")
                self.issues.append(f"Create it using: gcloud iam service-accounts create sales-intel-poc-sa")
                return False
                
        except FileNotFoundError:
            self.warnings.append("gcloud CLI not found - cannot verify service account")
            return False
        except Exception as e:
            self.warnings.append(f"Could not verify service account: {e}")
            return False
    
    def check_authentication(self) -> bool:
        """Check if authenticated with GCP."""
        try:
            import subprocess
            result = subprocess.run(
                ["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                account = result.stdout.strip().split('\n')[0]
                self.successes.append(f"✓ Authenticated as: {account}")
                return True
            else:
                self.issues.append("Not authenticated with gcloud CLI")
                self.issues.append("Run: gcloud auth login")
                return False
                
        except FileNotFoundError:
            self.warnings.append("gcloud CLI not found - cannot verify authentication")
            return False
        except Exception as e:
            self.warnings.append(f"Could not verify authentication: {e}")
            return False
    
    def check_bigquery_dataset(self) -> bool:
        """Check if BigQuery dataset exists (optional)."""
        if not SECRET_MANAGER_AVAILABLE or not self.project_id:
            return False
        
        try:
            client = bigquery.Client(project=self.project_id)
            dataset_id = "sales_intelligence_dev"
            dataset_ref = client.dataset(dataset_id)
            
            try:
                client.get_dataset(dataset_ref)
                self.successes.append(f"✓ BigQuery dataset exists: {dataset_id}")
                return True
            except Exception:
                self.warnings.append(f"BigQuery dataset does not exist: {dataset_id}")
                self.warnings.append("Run: python scripts/setup_bigquery.py")
                return False
                
        except Exception as e:
            self.warnings.append(f"Could not verify BigQuery dataset: {e}")
            return False
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all readiness checks."""
        print("=" * 60)
        print("Readiness Check for Integration Testing")
        print("=" * 60)
        print()
        
        checks = [
            ("Project ID", self.check_project_id),
            ("Python Dependencies", self.check_dependencies),
            ("GCP Authentication", self.check_authentication),
            ("Service Account", self.check_service_account),
            ("Secret Manager Secrets", self.check_secrets),
            ("BigQuery Dataset", self.check_bigquery_dataset),
        ]
        
        results = {}
        for check_name, check_func in checks:
            try:
                results[check_name] = check_func()
            except Exception as e:
                logger.error(f"Error in {check_name} check: {e}", exc_info=True)
                results[check_name] = False
                self.issues.append(f"Error checking {check_name}: {e}")
        
        return results
    
    def print_report(self):
        """Print readiness report."""
        results = self.run_all_checks()
        
        print("\n" + "=" * 60)
        print("Readiness Report")
        print("=" * 60)
        
        if self.successes:
            print("\n✓ Successes:")
            for success in self.successes:
                print(f"  {success}")
        
        if self.warnings:
            print("\n⚠ Warnings:")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if self.issues:
            print("\n✗ Issues (must be fixed before testing):")
            for issue in self.issues:
                print(f"  {issue}")
        
        print("\n" + "=" * 60)
        
        if not self.issues:
            print("\n✅ READY TO TEST!")
            print("\nNext steps:")
            print("1. Run integration examples:")
            print("   python examples/integration_examples.py")
            print("\n2. Or test individual integrations:")
            print("   python integrations/gmail_oauth.py")
            print("   python integrations/hubspot_api.py")
            print("   python integrations/salesforce_oauth.py")
            print("   python integrations/dialpad_api.py")
            print("\n3. Set up infrastructure (if not done):")
            print("   python scripts/setup_pubsub.py")
            print("   python scripts/setup_bigquery.py")
            print("   python scripts/setup_cloud_functions.py")
            print("   python scripts/setup_cloud_scheduler.py")
        else:
            print("\n❌ NOT READY - Please fix the issues above before testing")
            print("\nQuick fixes:")
            if "GCP_PROJECT_ID" in str(self.issues):
                print("  export GCP_PROJECT_ID=your-project-id")
            if "Missing Python packages" in str(self.issues):
                print("  pip install -r requirements.txt")
            if "Missing secrets" in str(self.issues):
                print("  Create secrets in Secret Manager (see docs/INTEGRATION_GUIDE.md)")
            if "Not authenticated" in str(self.issues):
                print("  gcloud auth login")
                print("  gcloud auth application-default login")
        
        print("=" * 60)


def main():
    """Main function."""
    checker = ReadinessChecker()
    checker.print_report()


if __name__ == "__main__":
    main()

