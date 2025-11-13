"""Email address normalization utilities for entity resolution."""
import re
from typing import Optional


def normalize_email(email: str) -> Optional[str]:
    """
    Normalize email address for matching.
    
    Args:
        email: Email address string
    
    Returns:
        Normalized lowercase email or None if invalid
    """
    if not email:
        return None
    
    email = email.strip().lower()
    
    # Basic email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return None
    
    return email


def extract_domain(email: str) -> Optional[str]:
    """
    Extract domain from email address.
    
    Args:
        email: Email address string
    
    Returns:
        Domain portion of email or None
    """
    normalized = normalize_email(email)
    if normalized and "@" in normalized:
        return normalized.split("@")[1]
    return None

