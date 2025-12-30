"""
Input validation utilities for security and data integrity.
"""
import re
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_account_id(account_id: str) -> bool:
    """
    Validate Salesforce account ID format.
    
    Args:
        account_id: Account ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not account_id or not isinstance(account_id, str):
        return False
    
    # Salesforce IDs are 15 or 18 characters alphanumeric
    return bool(re.match(r'^[a-zA-Z0-9]{15,18}$', account_id))


def sanitize_sql_input(value: str) -> str:
    """
    Sanitize input for SQL queries to prevent injection.
    
    Args:
        value: String to sanitize
        
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        value = str(value)
    
    # Remove potentially dangerous characters
    # Note: This is a basic sanitization. Always use parameterized queries!
    sanitized = re.sub(r'[;\'"\\]', '', value)
    
    if sanitized != value:
        logger.warning(f"SQL input sanitized: {len(value)} -> {len(sanitized)} chars")
    
    return sanitized


def validate_limit(limit: Optional[int], max_limit: int = 10000) -> Optional[int]:
    """
    Validate and sanitize limit parameter.
    
    Args:
        limit: Limit value to validate
        max_limit: Maximum allowed limit
        
    Returns:
        Validated limit or None if invalid
    """
    if limit is None:
        return None
    
    try:
        limit_int = int(limit)
        if limit_int <= 0:
            logger.warning(f"Invalid limit: {limit_int} (must be > 0)")
            return None
        if limit_int > max_limit:
            logger.warning(f"Limit too large: {limit_int} (max: {max_limit})")
            return max_limit
        return limit_int
    except (ValueError, TypeError):
        logger.warning(f"Invalid limit type: {type(limit)}")
        return None


def validate_project_id(project_id: str) -> bool:
    """
    Validate GCP project ID format.
    
    Args:
        project_id: Project ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not project_id or not isinstance(project_id, str):
        return False
    
    # GCP project IDs: 6-30 chars, lowercase letters, numbers, hyphens
    # Must start with lowercase letter
    pattern = r'^[a-z][a-z0-9-]{4,28}[a-z0-9]$'
    return bool(re.match(pattern, project_id))


def validate_secret_name(secret_name: str) -> bool:
    """
    Validate secret name format for Secret Manager.
    
    Args:
        secret_name: Secret name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not secret_name or not isinstance(secret_name, str):
        return False
    
    # Secret names: 1-255 chars, alphanumeric, hyphens, underscores
    pattern = r'^[a-zA-Z0-9_-]{1,255}$'
    return bool(re.match(pattern, secret_name))

