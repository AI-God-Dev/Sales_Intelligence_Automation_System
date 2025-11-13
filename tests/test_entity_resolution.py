"""Unit tests for entity resolution."""
import pytest
from utils.email_normalizer import normalize_email, extract_domain
from utils.phone_normalizer import normalize_phone, match_phone_numbers


class TestEmailNormalizer:
    """Test email normalization functions."""
    
    def test_normalize_email_valid(self):
        assert normalize_email("Test@Example.COM") == "test@example.com"
        assert normalize_email("  user@domain.com  ") == "user@domain.com"
    
    def test_normalize_email_invalid(self):
        assert normalize_email("") is None
        assert normalize_email("invalid-email") is None
        assert normalize_email("@domain.com") is None
    
    def test_extract_domain(self):
        assert extract_domain("user@example.com") == "example.com"
        assert extract_domain("test@domain.co.uk") == "domain.co.uk"
        assert extract_domain("invalid") is None


class TestPhoneNormalizer:
    """Test phone number normalization functions."""
    
    def test_normalize_phone_us(self):
        assert normalize_phone("(123) 456-7890") == "+11234567890"
        assert normalize_phone("123-456-7890") == "+11234567890"
        assert normalize_phone("+1 123 456 7890") == "+11234567890"
    
    def test_normalize_phone_invalid(self):
        assert normalize_phone("") is None
        assert normalize_phone("123") is None
    
    def test_match_phone_numbers(self):
        assert match_phone_numbers("(123) 456-7890", "123-456-7890") is True
        assert match_phone_numbers("+11234567890", "1234567890") is True
        assert match_phone_numbers("1234567890", "9876543210") is False

