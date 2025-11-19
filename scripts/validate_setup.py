#!/usr/bin/env python3
"""
Setup validation script for Sales Intelligence System.
Checks all prerequisites and configuration before deployment.
"""
import os
import sys
import subprocess
from pathlib import Path


def check_command(cmd: str, version_flag: str = "--version") -> bool:
    """Check if a command exists and works."""
    try:
        result = subprocess.run(
            [cmd, version_flag],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_python_packages() -> tuple[bool, list[str]]:
    """Check if required Python packages are installed."""
    required_packages = [
        "functions_framework",
        "google.cloud.bigquery",
        "google.cloud.secretmanager",
        "google.cloud.pubsub",
        "pydantic",
        "pydantic_settings",
    ]
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace(".", "_") if "." in package else package)
        except ImportError:
            missing.append(package)
    return len(missing) == 0, missing


def check_env_variables() -> tuple[bool, list[str]]:
    """Check if required environment variables are set."""
    required = ["GCP_PROJECT_ID"]
    optional = ["GCP_REGION", "BIGQUERY_DATASET", "GCP_SERVICE_ACCOUNT"]
    missing_required = []
    missing_optional = []
    
    for var in required:
        if not os.getenv(var):
            missing_required.append(var)
    
    for var in optional:
        if not os.getenv(var):
            missing_optional.append(var)
    
    return len(missing_required) == 0, missing_required, missing_optional


def check_file_structure() -> tuple[bool, list[str]]:
    """Check if required files and directories exist."""
    required_files = [
        "config/config.py",
        "config/__init__.py",
        "utils/__init__.py",
        "cloud_functions/__init__.py",
        "requirements.txt",
        ".env.example",
    ]
    required_dirs = [
        "cloud_functions/gmail_sync",
        "cloud_functions/salesforce_sync",
        "cloud_functions/dialpad_sync",
        "cloud_functions/hubspot_sync",
        "cloud_functions/entity_resolution",
        "utils",
        "config",
    ]
    missing = []
    
    project_root = Path(__file__).parent.parent
    
    for file_path in required_files:
        if not (project_root / file_path).exists():
            missing.append(f"File: {file_path}")
    
    for dir_path in required_dirs:
        if not (project_root / dir_path).is_dir():
            missing.append(f"Directory: {dir_path}")
    
    return len(missing) == 0, missing


def check_gcp_auth() -> bool:
    """Check if GCP authentication is configured."""
    try:
        result = subprocess.run(
            ["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0 and result.stdout.strip() != ""
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def main():
    """Run all validation checks."""
    print("=" * 60)
    print("Sales Intelligence System - Setup Validation")
    print("=" * 60)
    print()
    
    all_checks_passed = True
    
    # Check commands
    print("1. Checking required commands...")
    commands = {
        "gcloud": "GCP SDK (gcloud)",
        "python": "Python",
        "terraform": "Terraform (optional)",
    }
    for cmd, name in commands.items():
        exists = check_command(cmd)
        status = "✓" if exists else "✗"
        print(f"   {status} {name}: {'Found' if exists else 'NOT FOUND'}")
        if not exists and cmd in ["gcloud", "python"]:
            all_checks_passed = False
    
    print()
    
    # Check Python packages
    print("2. Checking Python packages...")
    packages_ok, missing = check_python_packages()
    status = "✓" if packages_ok else "✗"
    print(f"   {status} Required packages: {'All installed' if packages_ok else f'Missing: {", ".join(missing)}'}")
    if not packages_ok:
        print(f"      Run: pip install -r requirements.txt")
        all_checks_passed = False
    print()
    
    # Check environment variables
    print("3. Checking environment variables...")
    env_ok, missing_required, missing_optional = check_env_variables()
    status = "✓" if env_ok else "✗"
    print(f"   {status} Required environment variables: {'All set' if env_ok else f'Missing: {", ".join(missing_required)}'}")
    if missing_optional:
        print(f"      Optional (not set): {", ".join(missing_optional)}")
    if not env_ok:
        print(f"      Set with: export GCP_PROJECT_ID='your-project-id'")
        print(f"      Or create .env file from .env.example")
        all_checks_passed = False
    print()
    
    # Check file structure
    print("4. Checking file structure...")
    structure_ok, missing = check_file_structure()
    status = "✓" if structure_ok else "✗"
    print(f"   {status} File structure: {'OK' if structure_ok else f'Missing: {len(missing)} items'}")
    if not structure_ok:
        for item in missing[:5]:  # Show first 5
            print(f"      - {item}")
        if len(missing) > 5:
            print(f"      ... and {len(missing) - 5} more")
        all_checks_passed = False
    print()
    
    # Check GCP authentication
    print("5. Checking GCP authentication...")
    gcp_auth_ok = check_gcp_auth()
    status = "✓" if gcp_auth_ok else "✗"
    print(f"   {status} GCP Authentication: {'Authenticated' if gcp_auth_ok else 'NOT AUTHENTICATED'}")
    if not gcp_auth_ok:
        print(f"      Run: gcloud auth login")
        print(f"      And: gcloud auth application-default login")
        all_checks_passed = False
    print()
    
    # Summary
    print("=" * 60)
    if all_checks_passed:
        print("✓ All checks passed! System is ready for deployment.")
        return 0
    else:
        print("✗ Some checks failed. Please fix the issues above before deployment.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

