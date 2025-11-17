"""
Tests for email normalization utilities.
"""
import pytest
from utils.email_normalizer import normalize_email, extract_domain


def test_normalize_email_valid():
    """Test normalizing valid email addresses."""
    assert normalize_email("Test@Example.COM") == "test@example.com"
    assert normalize_email("  user@domain.com  ") == "user@domain.com"
    assert normalize_email("user.name+tag@example.co.uk") == "user.name+tag@example.co.uk"


def test_normalize_email_invalid():
    """Test normalizing invalid email addresses."""
    assert normalize_email("") is None
    assert normalize_email(None) is None
    assert normalize_email("invalid") is None
    assert normalize_email("invalid@") is None
    assert normalize_email("@domain.com") is None
    assert normalize_email("user@") is None


def test_extract_domain():
    """Test domain extraction from email."""
    assert extract_domain("user@example.com") == "example.com"
    assert extract_domain("test@sub.domain.co.uk") == "sub.domain.co.uk"
    assert extract_domain("invalid") is None
    assert extract_domain("") is None

