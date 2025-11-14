"""
Input validation and sanitization utilities for production safety.
"""
import re
import logging
from typing import Any, Optional, List, Dict
from email.utils import parseaddr

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_email(email: str) -> str:
    """
    Validate and normalize email address.
    
    Args:
        email: Email address to validate
        
    Returns:
        Normalized email address (lowercase)
        
    Raises:
        ValidationError: If email is invalid
    """
    if not email or not isinstance(email, str):
        raise ValidationError("Email must be a non-empty string")
    
    email = email.strip().lower()
    
    # Basic email regex validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValidationError(f"Invalid email format: {email}")
    
    # Additional validation using email.utils
    name, addr = parseaddr(email)
    if not addr or '@' not in addr:
        raise ValidationError(f"Invalid email address: {email}")
    
    return email


def validate_sql_identifier(identifier: str, allowed_identifiers: Optional[List[str]] = None) -> str:
    """
    Validate SQL identifier to prevent injection.
    
    Args:
        identifier: SQL identifier to validate
        allowed_identifiers: Optional whitelist of allowed identifiers
        
    Returns:
        Validated identifier
        
    Raises:
        ValidationError: If identifier is invalid or not in whitelist
    """
    if not identifier or not isinstance(identifier, str):
        raise ValidationError("SQL identifier must be a non-empty string")
    
    identifier = identifier.strip()
    
    # Check against whitelist if provided
    if allowed_identifiers and identifier not in allowed_identifiers:
        raise ValidationError(f"Identifier '{identifier}' not in allowed list")
    
    # Validate format (alphanumeric, underscore, hyphen only)
    if not re.match(r'^[a-zA-Z0-9_-]+$', identifier):
        raise ValidationError(f"Invalid SQL identifier format: {identifier}")
    
    # Prevent SQL keywords
    sql_keywords = ['SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE']
    if identifier.upper() in sql_keywords:
        raise ValidationError(f"Identifier cannot be a SQL keyword: {identifier}")
    
    return identifier


def sanitize_string(value: str, max_length: Optional[int] = None, allow_html: bool = False) -> str:
    """
    Sanitize string input to prevent injection attacks.
    
    Args:
        value: String to sanitize
        max_length: Optional maximum length
        allow_html: Whether to allow HTML (default: False)
        
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        raise ValidationError("Value must be a string")
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # Strip whitespace
    value = value.strip()
    
    # Remove HTML if not allowed
    if not allow_html:
        # Basic HTML tag removal
        value = re.sub(r'<[^>]+>', '', value)
    
    # Enforce max length
    if max_length and len(value) > max_length:
        logger.warning(f"String truncated from {len(value)} to {max_length} characters")
        value = value[:max_length]
    
    return value


def validate_phone_number(phone: str) -> Optional[str]:
    """
    Validate phone number format.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        Normalized phone number or None if invalid
    """
    if not phone or not isinstance(phone, str):
        return None
    
    # Remove common formatting characters
    phone = re.sub(r'[\s\-\(\)\.]', '', phone)
    
    # Basic validation (E.164 format: + followed by 1-15 digits)
    if re.match(r'^\+?[1-9]\d{1,14}$', phone):
        # Ensure + prefix
        if not phone.startswith('+'):
            phone = '+' + phone
        return phone
    
    return None


def validate_request_params(
    params: Dict[str, Any],
    required: List[str],
    optional: Optional[List[str]] = None,
    validators: Optional[Dict[str, callable]] = None
) -> Dict[str, Any]:
    """
    Validate request parameters.
    
    Args:
        params: Request parameters dictionary
        required: List of required parameter names
        optional: List of optional parameter names
        validators: Dictionary mapping parameter names to validation functions
        
    Returns:
        Validated parameters dictionary
        
    Raises:
        ValidationError: If validation fails
    """
    validated = {}
    
    # Check required parameters
    for param in required:
        if param not in params:
            raise ValidationError(f"Required parameter '{param}' is missing")
        validated[param] = params[param]
    
    # Add optional parameters if present
    if optional:
        for param in optional:
            if param in params:
                validated[param] = params[param]
    
    # Run validators
    if validators:
        for param, validator in validators.items():
            if param in validated:
                try:
                    validated[param] = validator(validated[param])
                except Exception as e:
                    raise ValidationError(f"Validation failed for '{param}': {str(e)}")
    
    return validated


def validate_sync_type(sync_type: str) -> str:
    """
    Validate sync type parameter.
    
    Args:
        sync_type: Sync type to validate
        
    Returns:
        Validated sync type
        
    Raises:
        ValidationError: If sync type is invalid
    """
    valid_types = ['full', 'incremental']
    if sync_type not in valid_types:
        raise ValidationError(f"Invalid sync_type '{sync_type}'. Must be one of: {', '.join(valid_types)}")
    return sync_type


def validate_object_type(object_type: str, allowed_types: List[str]) -> str:
    """
    Validate Salesforce object type.
    
    Args:
        object_type: Object type to validate
        allowed_types: List of allowed object types
        
    Returns:
        Validated object type
        
    Raises:
        ValidationError: If object type is invalid
    """
    if object_type not in allowed_types:
        raise ValidationError(
            f"Invalid object_type '{object_type}'. Must be one of: {', '.join(allowed_types)}"
        )
    return object_type

