"""
Retry utilities with exponential backoff for API calls and external services.
"""
import time
import logging
from typing import Callable, TypeVar, Optional, List, Type
from functools import wraps
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryCallState
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_wait: float = 1.0,
        max_wait: float = 60.0,
        exponential_base: float = 2.0,
        retryable_exceptions: Optional[List[Type[Exception]]] = None
    ):
        self.max_attempts = max_attempts
        self.initial_wait = initial_wait
        self.max_wait = max_wait
        self.exponential_base = exponential_base
        self.retryable_exceptions = retryable_exceptions or [Exception]


def retry_with_backoff(
    max_attempts: int = 3,
    initial_wait: float = 1.0,
    max_wait: float = 60.0,
    exponential_base: float = 2.0,
    retryable_exceptions: Optional[List[Type[Exception]]] = None
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        initial_wait: Initial wait time in seconds
        max_wait: Maximum wait time in seconds
        exponential_base: Base for exponential backoff calculation
        retryable_exceptions: List of exception types to retry on
    
    Example:
        @retry_with_backoff(max_attempts=5, initial_wait=2.0)
        def api_call():
            return requests.get("https://api.example.com")
    """
    if retryable_exceptions is None:
        retryable_exceptions = [Exception]
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(
                multiplier=initial_wait,
                max=max_wait,
                exp_base=exponential_base
            ),
            retry=retry_if_exception_type(tuple(retryable_exceptions)),
            reraise=True,
            before_sleep=_log_retry_attempt
        )
        def wrapper(*args, **kwargs) -> T:
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def _log_retry_attempt(retry_state: RetryCallState) -> None:
    """Log retry attempts for observability."""
    logger.warning(
        f"Retrying {retry_state.fn.__name__} after {retry_state.outcome.exception()}. "
        f"Attempt {retry_state.attempt_number}/{retry_state.retry_object.stop.max_attempt_number}"
    )


class RateLimiter:
    """Simple rate limiter to prevent API quota exhaustion."""
    
    def __init__(self, max_calls: int, time_window: float):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls: List[float] = []
    
    def wait_if_needed(self) -> None:
        """Wait if rate limit would be exceeded."""
        now = time.time()
        
        # Remove calls outside the time window
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        if len(self.calls) >= self.max_calls:
            sleep_time = self.time_window - (now - self.calls[0])
            if sleep_time > 0:
                logger.info(f"Rate limit reached. Waiting {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                # Clean up again after sleep
                now = time.time()
                self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        self.calls.append(now)

