"""Phone number normalization utilities for entity resolution."""
import phonenumbers
from phonenumbers import NumberParseException
from typing import Optional


def normalize_phone(phone: str, default_region: str = "US") -> Optional[str]:
    """
    Normalize phone number to E.164 format.
    
    Args:
        phone: Phone number string (various formats)
        default_region: Default region code (ISO 3166-1 alpha-2)
    
    Returns:
        E.164 formatted phone number (e.g., +1234567890) or None if invalid
    """
    if not phone:
        return None
    
    # Remove common formatting characters
    phone = phone.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    
    try:
        parsed = phonenumbers.parse(phone, default_region)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except NumberParseException:
        pass
    
    return None


def extract_last_10_digits(phone: str) -> Optional[str]:
    """
    Extract last 10 digits from phone number for partial matching.
    
    Args:
        phone: Phone number string
    
    Returns:
        Last 10 digits as string or None
    """
    if not phone:
        return None
    
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, phone))
    
    if len(digits) >= 10:
        return digits[-10:]
    
    return None


def match_phone_numbers(phone1: str, phone2: str) -> bool:
    """
    Check if two phone numbers match (exact or partial).
    
    Args:
        phone1: First phone number
        phone2: Second phone number
    
    Returns:
        True if numbers match
    """
    # Try exact match first
    normalized1 = normalize_phone(phone1)
    normalized2 = normalize_phone(phone2)
    
    if normalized1 and normalized2:
        if normalized1 == normalized2:
            return True
    
    # Try partial match (last 10 digits)
    digits1 = extract_last_10_digits(phone1)
    digits2 = extract_last_10_digits(phone2)
    
    if digits1 and digits2:
        return digits1 == digits2
    
    return False

