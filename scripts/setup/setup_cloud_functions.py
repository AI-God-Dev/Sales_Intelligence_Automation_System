"""
Cloud Function Deployment Script
Deploys Cloud Functions for data ingestion from Gmail, Salesforce, Dialpad, and HubSpot.
Uses service account (sales-intel-poc-sa) for authentication.
"""
import os
import logging
import subprocess
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class CloudFunctionDeployer:
    """
    Manager for deploying Cloud Functions.
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        region: str = "us-central1",
        service_account: str = "sales-intel-poc-sa"
    ):
        """
        Initialize Cloud Function deployer.
        
        Args:
            project_id: GCP project ID. If not provided, uses environment or metadata.
            region: GCP region for Cloud Functions (default: us-central1)
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
        
        self.region = region
        self.base_path = Path(__file__).parent.parent
        
        logger.info(f"Initialized Cloud Function deployer for project: {self.project_id}")
        logger.info(f"Service account: {self.service_account}")
        logger.info(f"Region: {self.region}")
    
    def deploy_function(
        self,
        function_name: str,
        source_path: str,
        entry_point: str,
        runtime: str = "python311",
        trigger: str = "http",
        environment_vars: Optional[Dict[str, str]] = None,
        timeout: int = 540,
        memory: str = "256MB"
    ) -> bool:
        """
        Deploy a Cloud Function.
        
        Args:
            function_name: Name of the Cloud Function
            source_path: Path to function source code (relative to project root)
            entry_point: Entry point function name
            runtime: Python runtime version (default: python311)
            trigger: Trigger type (http or pubsub)
            environment_vars: Optional environment variables
            timeout: Function timeout in seconds (default: 540)
            memory: Memory allocation (default: 256MB)
        
        Returns:
            True if deployment successful, False otherwise
        """
        try:
            source_full_path = self.base_path / source_path
            
            if not source_full_path.exists():
                logger.error(f"Source path does not exist: {source_full_path}")
                return False
            
            # Build gcloud command
            cmd = [
                "gcloud",
                "functions",
                "deploy",
                function_name,
                f"--gen2",
                f"--runtime={runtime}",
                f"--region={self.region}",
                f"--source={source_full_path}",
                f"--entry-point={entry_point}",
                f"--service-account={self.service_account}",
                f"--timeout={timeout}",
                f"--memory={memory}",
                f"--project={self.project_id}",
                "--allow-unauthenticated"  # Remove if authentication is required
            ]
            
            # Add trigger
            if trigger == "http":
                cmd.append("--trigger-http")
            elif trigger == "pubsub":
                # For Pub/Sub, need to specify topic
                topic_name = f"{function_name.replace('-', '-')}-topic"
                cmd.extend(["--trigger-topic", topic_name])
            
            # Add environment variables
            if environment_vars:
                env_vars_str = ",".join([f"{k}={v}" for k, v in environment_vars.items()])
                cmd.extend(["--set-env-vars", env_vars_str])
            
            logger.info(f"Deploying function: {function_name}")
            logger.debug(f"Command: {' '.join(cmd)}")
            
            # Execute deployment
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully deployed function: {function_name}")
                return True
            else:
                logger.error(f"Failed to deploy function {function_name}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error deploying function {function_name}: {e}", exc_info=True)
            return False
    
    def deploy_all_functions(self) -> Dict[str, bool]:
        """
        Deploy all ingestion Cloud Functions.
        
        Returns:
            Dictionary mapping function names to deployment success status
        """
        functions_config = [
            {
                "name": "gmail-sync",
                "source": "cloud_functions/gmail_sync",
                "entry_point": "gmail_sync",
                "trigger": "http"
            },
            {
                "name": "salesforce-sync",
                "source": "cloud_functions/salesforce_sync",
                "entry_point": "salesforce_sync",
                "trigger": "http"
            },
            {
                "name": "dialpad-sync",
                "source": "cloud_functions/dialpad_sync",
                "entry_point": "dialpad_sync",
                "trigger": "http"
            },
            {
                "name": "hubspot-sync",
                "source": "cloud_functions/hubspot_sync",
                "entry_point": "hubspot_sync",
                "trigger": "http"
            }
        ]
        
        deployment_results = {}
        
        for func_config in functions_config:
            success = self.deploy_function(
                function_name=func_config["name"],
                source_path=func_config["source"],
                entry_point=func_config["entry_point"],
                trigger=func_config["trigger"],
                environment_vars={
                    "GCP_PROJECT_ID": self.project_id
                }
            )
            deployment_results[func_config["name"]] = success
        
        return deployment_results


def main():
    """
    Main function to deploy all Cloud Functions.
    """
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("Deploying Cloud Functions for Data Ingestion")
    print("=" * 60)
    
    deployer = CloudFunctionDeployer()
    
    print("\nDeploying functions...")
    results = deployer.deploy_all_functions()
    
    print("\nDeployment Results:")
    for function_name, success in results.items():
        status = "✓ Success" if success else "✗ Failed"
        print(f"  {function_name}: {status}")
    
    print("\n" + "=" * 60)
    print("Cloud Function deployment completed!")
    print("=" * 60)
    
    if all(results.values()):
        print("\nAll functions deployed successfully!")
    else:
        print("\nSome functions failed to deploy. Check logs for details.")


if __name__ == "__main__":
    main()

