"""
Circuit breaker pattern for external service calls.
"""
from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, Optional
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker for external service calls.
    
    Prevents cascading failures by stopping requests to failing services
    and allowing them time to recover.
    
    Usage:
        breaker = CircuitBreaker(failure_threshold=5, timeout_seconds=60)
        result = breaker.call(api_function, arg1, arg2)
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        success_threshold: int = 2
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout_seconds: Time to wait before attempting half-open
            success_threshold: Successes needed to close from half-open
        """
        self.failure_threshold = failure_threshold
        self.timeout = timedelta(seconds=timeout_seconds)
        self.success_threshold = success_threshold
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.logger = logger
    
    def call(self, func: Callable, *args, **kwargs):
        """
        Execute function through circuit breaker.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == CircuitState.OPEN:
            if self.last_failure_time and datetime.now() - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                self.logger.info(f"Circuit breaker entering half-open state for {func.__name__}")
            else:
                raise Exception(
                    f"Circuit breaker is OPEN for {func.__name__}. "
                    f"Service unavailable. Last failure: {self.last_failure_time}"
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success(func.__name__)
            return result
        except Exception as e:
            self._on_failure(func.__name__, e)
            raise
    
    def _on_success(self, func_name: str):
        """Handle successful call."""
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.success_count = 0
                self.logger.info(f"Circuit breaker closed for {func_name}")
    
    def _on_failure(self, func_name: str, error: Exception):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.logger.warning(
                f"Circuit breaker opened for {func_name} "
                f"after {self.failure_count} failures. Last error: {error}"
            )
    
    def reset(self):
        """Manually reset circuit breaker to closed state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.logger.info("Circuit breaker manually reset")


# Global circuit breakers for common services
_vertex_ai_breaker = CircuitBreaker(failure_threshold=5, timeout_seconds=60)
_bigquery_breaker = CircuitBreaker(failure_threshold=3, timeout_seconds=30)
_salesforce_breaker = CircuitBreaker(failure_threshold=5, timeout_seconds=60)


def get_vertex_ai_breaker() -> CircuitBreaker:
    """Get circuit breaker for Vertex AI calls."""
    return _vertex_ai_breaker


def get_bigquery_breaker() -> CircuitBreaker:
    """Get circuit breaker for BigQuery calls."""
    return _bigquery_breaker


def get_salesforce_breaker() -> CircuitBreaker:
    """Get circuit breaker for Salesforce calls."""
    return _salesforce_breaker

