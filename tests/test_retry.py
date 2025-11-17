"""
Tests for retry utilities.
"""
import pytest
import time
from unittest.mock import patch, MagicMock
from utils.retry import retry_with_backoff, RateLimiter, RetryConfig


def test_retry_with_backoff_success():
    """Test retry decorator with successful call."""
    call_count = 0
    
    @retry_with_backoff(max_attempts=3, initial_wait=0.1)
    def successful_function():
        nonlocal call_count
        call_count += 1
        return "success"
    
    result = successful_function()
    assert result == "success"
    assert call_count == 1


def test_retry_with_backoff_retries():
    """Test retry decorator with retries."""
    call_count = 0
    
    @retry_with_backoff(max_attempts=3, initial_wait=0.1)
    def failing_then_success():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("Temporary error")
        return "success"
    
    result = failing_then_success()
    assert result == "success"
    assert call_count == 2


def test_retry_with_backoff_max_attempts():
    """Test retry decorator exhausts max attempts."""
    call_count = 0
    
    @retry_with_backoff(max_attempts=3, initial_wait=0.1)
    def always_fails():
        nonlocal call_count
        call_count += 1
        raise ValueError("Always fails")
    
    with pytest.raises(ValueError):
        always_fails()
    
    assert call_count == 3


def test_retry_config():
    """Test RetryConfig initialization."""
    config = RetryConfig(
        max_attempts=5,
        initial_wait=2.0,
        max_wait=120.0
    )
    assert config.max_attempts == 5
    assert config.initial_wait == 2.0
    assert config.max_wait == 120.0


def test_rate_limiter():
    """Test rate limiter functionality."""
    limiter = RateLimiter(max_calls=2, time_window=1.0)
    
    # First two calls should pass immediately
    limiter.wait_if_needed()
    limiter.wait_if_needed()
    
    # Third call should wait
    start = time.time()
    limiter.wait_if_needed()
    elapsed = time.time() - start
    
    # Should have waited at least a bit (allowing for timing variations)
    assert elapsed >= 0.5  # Should wait close to time_window


def test_rate_limiter_reset():
    """Test rate limiter resets after time window."""
    limiter = RateLimiter(max_calls=1, time_window=0.5)
    
    limiter.wait_if_needed()
    
    # Wait for time window to pass
    time.sleep(0.6)
    
    # Should not wait now
    start = time.time()
    limiter.wait_if_needed()
    elapsed = time.time() - start
    
    assert elapsed < 0.1  # Should be immediate

