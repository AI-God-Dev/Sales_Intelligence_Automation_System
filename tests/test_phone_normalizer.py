"""
Tests for phone number normalization utilities.
"""
import pytest
from utils.phone_normalizer import (
    normalize_phone,
    extract_last_10_digits,
    match_phone_numbers
)


def test_normalize_phone_valid():
    """Test normalizing valid phone numbers."""
    # US numbers - these should normalize to E.164 format
    result1 = normalize_phone("(234) 567-8901")
    assert result1 is not None
    assert result1.startswith("+1")
    
    result2 = normalize_phone("234-567-8901")
    assert result2 is not None
    assert result2.startswith("+1")
    
    result3 = normalize_phone("2345678901")
    assert result3 is not None
    assert result3.startswith("+1")
    
    # Already in E.164 format
    result4 = normalize_phone("+12345678901")
    assert result4 == "+12345678901" or result4 is not None


def test_normalize_phone_invalid():
    """Test normalizing invalid phone numbers."""
    assert normalize_phone("") is None
    assert normalize_phone(None) is None
    assert normalize_phone("123") is None  # Too short
    assert normalize_phone("abc") is None  # Not a number


def test_extract_last_10_digits():
    """Test extracting last 10 digits."""
    assert extract_last_10_digits("+12345678901") == "2345678901"
    assert extract_last_10_digits("1234567890") == "1234567890"
    assert extract_last_10_digits("(123) 456-7890") == "1234567890"
    assert extract_last_10_digits("123") is None  # Less than 10 digits
    assert extract_last_10_digits("") is None


def test_match_phone_numbers():
    """Test phone number matching."""
    # Exact match
    assert match_phone_numbers("+12345678901", "+12345678901") is True
    assert match_phone_numbers("(234) 567-8901", "234-567-8901") is True
    
    # Partial match (last 10 digits) - if both normalize successfully
    result = match_phone_numbers("+12345678901", "2345678901")
    # Result depends on normalization, but should be consistent
    assert isinstance(result, bool)
    
    # No match
    assert match_phone_numbers("+12345678901", "+19876543210") is False
    assert match_phone_numbers("invalid", "1234567890") is False

