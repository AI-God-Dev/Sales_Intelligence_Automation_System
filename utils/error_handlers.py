"""
Centralized error handling with categorization and reporting.
"""
import logging
from typing import Callable, TypeVar, Optional, Dict, Any
from functools import wraps
from enum import Enum

T = TypeVar('T')

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorHandler:
    """Centralized error handling with categorization and reporting."""
    
    @staticmethod
    def categorize_error(error: Exception) -> ErrorSeverity:
        """
        Categorize error by severity based on error type and message.
        
        Args:
            error: Exception to categorize
            
        Returns:
            ErrorSeverity level
        """
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # Critical errors - authentication, permissions, credentials
        if any(x in error_str for x in ["auth", "permission", "credential", "unauthorized", "forbidden", "401", "403"]):
            return ErrorSeverity.CRITICAL
        
        # High severity - data loss, database errors, configuration
        if any(x in error_str for x in ["database", "bigquery", "data loss", "corrupt", "invalid config"]):
            return ErrorSeverity.HIGH
        
        # Medium severity - timeouts, rate limits, quotas
        if any(x in error_str for x in ["timeout", "rate limit", "quota", "429", "503", "502"]):
            return ErrorSeverity.MEDIUM
        
        # Low severity - validation, formatting, minor issues
        return ErrorSeverity.LOW
    
    @staticmethod
    def handle_error(
        error: Exception,
        context: Dict[str, Any],
        logger_instance: Optional[logging.Logger] = None
    ) -> Dict[str, Any]:
        """
        Handle error with appropriate logging and response.
        
        Args:
            error: Exception that occurred
            context: Additional context about the error
            logger_instance: Optional logger instance (uses module logger if not provided)
            
        Returns:
            Dictionary with error details
        """
        if logger_instance is None:
            logger_instance = logger
        
        severity = ErrorHandler.categorize_error(error)
        
        error_response = {
            "error": str(error),
            "error_type": type(error).__name__,
            "severity": severity.value,
            "context": context
        }
        
        # Log based on severity
        if severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            logger_instance.error(
                f"Error [{severity.value}]: {error}",
                exc_info=True,
                extra=error_response
            )
        elif severity == ErrorSeverity.MEDIUM:
            logger_instance.warning(
                f"Error [{severity.value}]: {error}",
                extra=error_response
            )
        else:
            logger_instance.info(
                f"Error [{severity.value}]: {error}",
                extra=error_response
            )
        
        return error_response


def with_error_handling(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for consistent error handling.
    
    Usage:
        @with_error_handling
        def my_function():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            context = {
                "function": func.__name__,
                "module": func.__module__,
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys())
            }
            ErrorHandler.handle_error(e, context)
            raise
    return wrapper


def safe_execute(
    func: Callable[..., T],
    default: Optional[T] = None,
    context: Optional[Dict[str, Any]] = None
) -> Optional[T]:
    """
    Safely execute a function with error handling.
    
    Args:
        func: Function to execute
        default: Default value to return on error
        context: Additional context for error reporting
        
    Returns:
        Function result or default value
    """
    try:
        return func()
    except Exception as e:
        error_context = context or {}
        error_context["function"] = func.__name__
        ErrorHandler.handle_error(e, error_context)
        return default

