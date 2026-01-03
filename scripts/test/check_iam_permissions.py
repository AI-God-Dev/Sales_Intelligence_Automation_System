"""
IAM Permissions Checker
Checks IAM roles and permissions for the service account (sales-intel-poc-sa).
Ensures the service account has necessary access to:
- BigQuery
- Cloud Functions
- Secret Manager
- Pub/Sub
- Cloud Scheduler
"""
import os
import logging
import subprocess
import json
from typing import List, Dict, Any, Optional, Set

logger = logging.getLogger(__name__)


class IAMPermissionChecker:
    """
    Checks IAM roles and permissions for a service account.
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        service_account: str = "sales-intel-poc-sa"
    ):
        """
        Initialize IAM permission checker.
        
        Args:
            project_id: GCP project ID. If not provided, uses environment or metadata.
            service_account: Service account email (default: sales-intel-poc-sa)
        """
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        if not self.project_id:
            raise ValueError("GCP project ID is required. Set GCP_PROJECT_ID environment variable.")
        
        # Construct full service account email
        if "@" not in service_account:
            self.service_account = f"{service_account}@{self.project_id}.iam.gserviceaccount.com"
        else:
            self.service_account = service_account
        
        logger.info(f"Initialized IAM permission checker for project: {self.project_id}")
        logger.info(f"Service account: {self.service_account}")
    
    def get_service_account_iam_policy(self) -> Dict[str, Any]:
        """
        Get IAM policy for the service account.
        
        Returns:
            IAM policy as dictionary
        """
        try:
            cmd = [
                "gcloud",
                "projects",
                "get-iam-policy",
                self.project_id,
                "--flatten=bindings[].members",
                "--filter=bindings.members:serviceAccount:{}".format(self.service_account),
                "--format=json",
                "--project={}".format(self.project_id)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                bindings = json.loads(result.stdout) if result.stdout else []
                return {"bindings": bindings}
            else:
                logger.error(f"Failed to get IAM policy: {result.stderr}")
                return {"bindings": []}
                
        except Exception as e:
            logger.error(f"Error getting IAM policy: {e}", exc_info=True)
            return {"bindings": []}
    
    def get_service_account_roles(self) -> Set[str]:
        """
        Get all roles assigned to the service account.
        
        Returns:
            Set of role names
        """
        policy = self.get_service_account_iam_policy()
        roles = set()
        
        for binding in policy.get("bindings", []):
            role = binding.get("role", "")
            members = binding.get("members", [])
            
            service_account_identifier = f"serviceAccount:{self.service_account}"
            if service_account_identifier in members:
                roles.add(role)
        
        return roles
    
    def check_required_roles(self) -> Dict[str, Dict[str, Any]]:
        """
        Check if service account has all required roles.
        
        Returns:
            Dictionary mapping service names to permission status
        """
        required_roles = {
            "BigQuery": [
                "roles/bigquery.dataEditor",
                "roles/bigquery.jobUser"
            ],
            "Cloud Functions": [
                "roles/cloudfunctions.invoker",
                "roles/cloudfunctions.developer"
            ],
            "Secret Manager": [
                "roles/secretmanager.secretAccessor"
            ],
            "Pub/Sub": [
                "roles/pubsub.publisher",
                "roles/pubsub.subscriber"
            ],
            "Cloud Scheduler": [
                "roles/cloudscheduler.jobRunner",
                "roles/iam.serviceAccountTokenCreator"
            ]
        }
        
        current_roles = self.get_service_account_roles()
        
        results = {}
        
        for service_name, roles in required_roles.items():
            missing_roles = []
            present_roles = []
            
            for role in roles:
                if role in current_roles:
                    present_roles.append(role)
                else:
                    missing_roles.append(role)
            
            results[service_name] = {
                "status": "complete" if not missing_roles else "incomplete",
                "present_roles": present_roles,
                "missing_roles": missing_roles,
                "all_required": roles
            }
        
        return results
    
    def check_service_account_exists(self) -> bool:
        """
        Check if the service account exists.
        
        Returns:
            True if service account exists, False otherwise
        """
        try:
            cmd = [
                "gcloud",
                "iam",
                "service-accounts",
                "describe",
                self.service_account,
                "--project={}".format(self.project_id)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Error checking service account existence: {e}")
            return False
    
    def print_permission_report(self) -> None:
        """
        Print a comprehensive permission report.
        """
        print("=" * 60)
        print("IAM Permissions Report")
        print("=" * 60)
        print(f"\nProject ID: {self.project_id}")
        print(f"Service Account: {self.service_account}\n")
        
        # Check if service account exists
        exists = self.check_service_account_exists()
        if not exists:
            print("❌ ERROR: Service account does not exist!")
            print(f"   Please create the service account: {self.service_account}")
            return
        
        print("✓ Service account exists\n")
        
        # Get current roles
        current_roles = self.get_service_account_roles()
        print(f"Current Roles ({len(current_roles)}):")
        for role in sorted(current_roles):
            print(f"  - {role}")
        print()
        
        # Check required roles
        results = self.check_required_roles()
        
        print("=" * 60)
        print("Permission Status by Service")
        print("=" * 60)
        
        for service_name, status_info in results.items():
            status = status_info["status"]
            icon = "✓" if status == "complete" else "✗"
            
            print(f"\n{icon} {service_name}: {status.upper()}")
            
            if status_info["present_roles"]:
                print("  Present roles:")
                for role in status_info["present_roles"]:
                    print(f"    ✓ {role}")
            
            if status_info["missing_roles"]:
                print("  Missing roles:")
                for role in status_info["missing_roles"]:
                    print(f"    ✗ {role}")
        
        # Summary
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)
        
        all_complete = all(
            info["status"] == "complete"
            for info in results.values()
        )
        
        if all_complete:
            print("\n✓ All required permissions are present!")
        else:
            print("\n✗ Some permissions are missing.")
            print("\nTo grant missing permissions, run:")
            print(f"  gcloud projects add-iam-policy-binding {self.project_id} \\")
            print(f"    --member='serviceAccount:{self.service_account}' \\")
            print(f"    --role='ROLE_NAME'")


def main():
    """
    Main function to check IAM permissions.
    """
    logging.basicConfig(level=logging.INFO)
    
    checker = IAMPermissionChecker()
    checker.print_permission_report()


if __name__ == "__main__":
    main()

