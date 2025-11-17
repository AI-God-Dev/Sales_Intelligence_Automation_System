"""
Tests for validation utilities.
"""
import pytest
from utils.validation import (
    ValidationError,
    validate_email,
    validate_sql_identifier,
    sanitize_string,
    validate_phone_number,
    validate_request_params,
    validate_sync_type,
    validate_object_type
)


def test_validate_email_valid():
    """Test validating valid emails."""
    assert validate_email("test@example.com") == "test@example.com"
    assert validate_email("  USER@DOMAIN.COM  ") == "user@domain.com"
    assert validate_email("user.name+tag@example.co.uk") == "user.name+tag@example.co.uk"


def test_validate_email_invalid():
    """Test validating invalid emails."""
    with pytest.raises(ValidationError):
        validate_email("")
    with pytest.raises(ValidationError):
        validate_email(None)
    with pytest.raises(ValidationError):
        validate_email("invalid")
    with pytest.raises(ValidationError):
        validate_email("@domain.com")


def test_validate_sql_identifier():
    """Test SQL identifier validation."""
    assert validate_sql_identifier("table_name") == "table_name"
    assert validate_sql_identifier("table-name") == "table-name"
    assert validate_sql_identifier("table123") == "table123"
    
    # With whitelist
    assert validate_sql_identifier("allowed", ["allowed", "other"]) == "allowed"
    
    # Invalid cases
    with pytest.raises(ValidationError):
        validate_sql_identifier("table name")  # Space not allowed
    with pytest.raises(ValidationError):
        validate_sql_identifier("SELECT")  # SQL keyword
    with pytest.raises(ValidationError):
        validate_sql_identifier("not_allowed", ["allowed"])


def test_sanitize_string():
    """Test string sanitization."""
    assert sanitize_string("  test  ") == "test"
    assert sanitize_string("test<script>alert('xss')</script>") == "testalert('xss')"
    assert sanitize_string("test", max_length=2) == "te"
    assert sanitize_string("test", allow_html=True) == "test"
    
    with pytest.raises(ValidationError):
        sanitize_string(123)  # Not a string


def test_validate_phone_number():
    """Test phone number validation."""
    assert validate_phone_number("+12345678901") == "+12345678901"
    assert validate_phone_number("12345678901") == "+12345678901"
    assert validate_phone_number("(123) 456-7890") == "+1234567890"
    
    assert validate_phone_number("") is None
    assert validate_phone_number("invalid") is None


def test_validate_request_params():
    """Test request parameter validation."""
    params = {"required1": "value1", "required2": "value2", "optional1": "opt1"}
    result = validate_request_params(
        params,
        required=["required1", "required2"],
        optional=["optional1"]
    )
    assert result == params
    
    # Missing required
    with pytest.raises(ValidationError):
        validate_request_params({}, required=["required1"])
    
    # With validators
    def validator(x):
        return x.upper()
    
    result = validate_request_params(
        {"param": "value"},
        required=["param"],
        validators={"param": validator}
    )
    assert result["param"] == "VALUE"


def test_validate_sync_type():
    """Test sync type validation."""
    assert validate_sync_type("full") == "full"
    assert validate_sync_type("incremental") == "incremental"
    
    with pytest.raises(ValidationError):
        validate_sync_type("invalid")


def test_validate_object_type():
    """Test object type validation."""
    allowed = ["Account", "Contact", "Lead"]
    assert validate_object_type("Account", allowed) == "Account"
    
    with pytest.raises(ValidationError):
        validate_object_type("Invalid", allowed)

