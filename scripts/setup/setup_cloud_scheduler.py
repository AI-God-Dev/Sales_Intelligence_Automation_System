"""
Cloud Scheduler Setup Script
Creates Cloud Scheduler jobs for automating ingestion pipeline execution.
Uses service account (sales-intel-poc-sa) for authentication.
"""
import os
import logging
import subprocess
import json
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class CloudSchedulerManager:
    """
    Manager for creating and managing Cloud Scheduler jobs.
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        region: str = "us-central1",
        service_account: str = "sales-intel-poc-sa"
    ):
        """
        Initialize Cloud Scheduler manager.
        
        Args:
            project_id: GCP project ID. If not provided, uses environment or metadata.
            region: GCP region for Cloud Scheduler (default: us-central1)
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
        
        logger.info(f"Initialized Cloud Scheduler manager for project: {self.project_id}")
        logger.info(f"Service account: {self.service_account}")
        logger.info(f"Region: {self.region}")
    
    def create_job(
        self,
        job_name: str,
        schedule: str,
        target_uri: str,
        http_method: str = "POST",
        body: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        timezone: str = "America/New_York"
    ) -> bool:
        """
        Create a Cloud Scheduler job.
        
        Args:
            job_name: Name of the scheduler job
            schedule: Cron schedule (e.g., "0 * * * *" for hourly)
            target_uri: Target Cloud Function URL
            http_method: HTTP method (default: POST)
            body: Optional request body as dictionary
            description: Optional job description
            timezone: Timezone for schedule (default: America/New_York)
        
        Returns:
            True if job created successfully, False otherwise
        """
        try:
            # Build gcloud command
            cmd = [
                "gcloud",
                "scheduler",
                "jobs",
                "create",
                "http",
                job_name,
                f"--location={self.region}",
                f"--schedule={schedule}",
                f"--uri={target_uri}",
                f"--http-method={http_method}",
                f"--oidc-service-account-email={self.service_account}",
                f"--time-zone={timezone}",
                f"--project={self.project_id}"
            ]
            
            # Add description
            if description:
                cmd.extend(["--description", description])
            
            # Add request body
            if body:
                body_json = json.dumps(body)
                cmd.extend(["--message-body", body_json])
                cmd.append("--headers=Content-Type=application/json")
            
            logger.info(f"Creating scheduler job: {job_name}")
            logger.debug(f"Command: {' '.join(cmd)}")
            
            # Execute command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully created scheduler job: {job_name}")
                return True
            else:
                # Check if job already exists
                if "already exists" in result.stderr.lower():
                    logger.info(f"Scheduler job {job_name} already exists")
                    return True
                logger.error(f"Failed to create scheduler job {job_name}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating scheduler job {job_name}: {e}", exc_info=True)
            return False
    
    def setup_all_jobs(self) -> Dict[str, bool]:
        """
        Set up all Cloud Scheduler jobs for ingestion pipelines.
        
        Returns:
            Dictionary mapping job names to creation success status
        """
        # Get Cloud Function URLs (assuming standard naming)
        function_base_url = f"https://{self.region}-{self.project_id}.cloudfunctions.net"
        
        jobs_config = [
            {
                "name": "gmail-incremental-sync",
                "schedule": "0 * * * *",  # Every hour
                "target_uri": f"{function_base_url}/gmail-sync",
                "body": {"sync_type": "incremental"},
                "description": "Incremental Gmail sync - runs every hour"
            },
            {
                "name": "gmail-full-sync",
                "schedule": "0 2 * * *",  # Daily at 2 AM
                "target_uri": f"{function_base_url}/gmail-sync",
                "body": {"sync_type": "full"},
                "description": "Full Gmail sync - runs daily at 2 AM"
            },
            {
                "name": "salesforce-incremental-sync",
                "schedule": "0 */6 * * *",  # Every 6 hours
                "target_uri": f"{function_base_url}/salesforce-sync",
                "body": {"sync_type": "incremental", "object_type": "Account"},
                "description": "Incremental Salesforce sync - runs every 6 hours"
            },
            {
                "name": "salesforce-full-sync",
                "schedule": "0 3 * * 0",  # Weekly on Sunday at 3 AM
                "target_uri": f"{function_base_url}/salesforce-sync",
                "body": {"sync_type": "full", "object_type": "Account"},
                "description": "Full Salesforce sync - runs weekly on Sunday at 3 AM"
            },
            {
                "name": "dialpad-sync",
                "schedule": "0 1 * * *",  # Daily at 1 AM
                "target_uri": f"{function_base_url}/dialpad-sync",
                "body": {"sync_type": "incremental"},
                "description": "Dialpad call logs sync - runs daily at 1 AM"
            },
            {
                "name": "hubspot-sync",
                "schedule": "0 4 * * *",  # Daily at 4 AM
                "target_uri": f"{function_base_url}/hubspot-sync",
                "body": {"sync_type": "incremental"},
                "description": "HubSpot sequences sync - runs daily at 4 AM"
            }
        ]
        
        job_results = {}
        
        for job_config in jobs_config:
            success = self.create_job(
                job_name=job_config["name"],
                schedule=job_config["schedule"],
                target_uri=job_config["target_uri"],
                body=job_config.get("body"),
                description=job_config.get("description")
            )
            job_results[job_config["name"]] = success
        
        return job_results


def main():
    """
    Main function to set up all Cloud Scheduler jobs.
    """
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("Setting up Cloud Scheduler Jobs for Data Ingestion")
    print("=" * 60)
    
    manager = CloudSchedulerManager()
    
    print("\nCreating scheduler jobs...")
    results = manager.setup_all_jobs()
    
    print("\nJob Creation Results:")
    for job_name, success in results.items():
        status = "✓ Success" if success else "✗ Failed"
        print(f"  {job_name}: {status}")
    
    print("\n" + "=" * 60)
    print("Cloud Scheduler setup completed!")
    print("=" * 60)
    
    if all(results.values()):
        print("\nAll scheduler jobs created successfully!")
    else:
        print("\nSome jobs failed to create. Check logs for details.")


if __name__ == "__main__":
    main()

