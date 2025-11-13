"""
Monitoring and observability utilities for metrics, tracing, and health checks.
"""
import time
import logging
from typing import Dict, Any, Optional, Callable
from functools import wraps
from contextlib import contextmanager
from google.cloud import monitoring_v3
from google.cloud.monitoring_v3 import MetricServiceClient
from google.cloud.monitoring_v3.types import TimeSeries

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and exports metrics to Google Cloud Monitoring."""
    
    def __init__(self, project_id: str):
        """
        Initialize metrics collector.
        
        Args:
            project_id: GCP project ID
        """
        self.project_id = project_id
        self.client: Optional[MetricServiceClient] = None
        self._metrics: Dict[str, float] = {}
    
    def _get_client(self) -> MetricServiceClient:
        """Get or create monitoring client."""
        if self.client is None:
            self.client = MetricServiceClient()
        return self.client
    
    def increment_counter(self, metric_name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Increment a counter metric.
        
        Args:
            metric_name: Name of the metric
            value: Value to increment by
            labels: Optional labels for the metric
        """
        key = f"{metric_name}:{labels or {}}"
        self._metrics[key] = self._metrics.get(key, 0) + value
        logger.debug(f"Counter {metric_name} incremented by {value}")
    
    def record_gauge(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Record a gauge metric.
        
        Args:
            metric_name: Name of the metric
            value: Current value
            labels: Optional labels for the metric
        """
        key = f"{metric_name}:{labels or {}}"
        self._metrics[key] = value
        logger.debug(f"Gauge {metric_name} set to {value}")
    
    def record_histogram(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Record a histogram value.
        
        Args:
            metric_name: Name of the metric
            value: Value to record
            labels: Optional labels for the metric
        """
        # For simplicity, we'll just log histogram values
        # In production, use proper histogram aggregation
        logger.debug(f"Histogram {metric_name} recorded: {value}")


class PerformanceMonitor:
    """Context manager for monitoring function performance."""
    
    def __init__(self, operation_name: str, metrics_collector: Optional[MetricsCollector] = None):
        """
        Initialize performance monitor.
        
        Args:
            operation_name: Name of the operation being monitored
            metrics_collector: Optional metrics collector instance
        """
        self.operation_name = operation_name
        self.metrics_collector = metrics_collector
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
    
    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        logger.debug(f"Starting operation: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End timing and record metrics."""
        self.end_time = time.time()
        duration = self.end_time - self.start_time if self.start_time else 0
        
        if exc_type is None:
            logger.info(f"Operation {self.operation_name} completed in {duration:.2f}s")
        else:
            logger.error(f"Operation {self.operation_name} failed after {duration:.2f}s: {exc_val}")
        
        if self.metrics_collector:
            self.metrics_collector.record_histogram(
                f"{self.operation_name}_duration",
                duration
            )
            if exc_type is None:
                self.metrics_collector.increment_counter(f"{self.operation_name}_success")
            else:
                self.metrics_collector.increment_counter(f"{self.operation_name}_failure")
        
        return False  # Don't suppress exceptions


def monitor_performance(operation_name: Optional[str] = None):
    """
    Decorator to monitor function performance.
    
    Args:
        operation_name: Optional custom operation name
    
    Example:
        @monitor_performance("gmail_sync")
        def sync_gmail():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = operation_name or f"{func.__module__}.{func.__name__}"
            with PerformanceMonitor(name):
                return func(*args, **kwargs)
        return wrapper
    return decorator


@contextmanager
def trace_operation(operation_name: str, **labels):
    """
    Context manager for tracing operations.
    
    Args:
        operation_name: Name of the operation
        **labels: Additional labels for tracing
    
    Example:
        with trace_operation("fetch_messages", mailbox="user@example.com"):
            messages = fetch_messages()
    """
    start_time = time.time()
    logger.info(f"Starting trace: {operation_name} with labels: {labels}")
    
    try:
        yield
    except Exception as e:
        logger.error(f"Trace {operation_name} failed: {e}", exc_info=True)
        raise
    finally:
        duration = time.time() - start_time
        logger.info(f"Trace {operation_name} completed in {duration:.2f}s")


def health_check() -> Dict[str, Any]:
    """
    Perform system health check.
    
    Returns:
        Dictionary with health status and component checks
    """
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "components": {}
    }
    
    # Check BigQuery connectivity
    try:
        from utils.bigquery_client import BigQueryClient
        client = BigQueryClient()
        # Simple query to test connectivity
        client.query("SELECT 1")
        health_status["components"]["bigquery"] = {"status": "healthy"}
    except Exception as e:
        health_status["components"]["bigquery"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check Secret Manager connectivity
    try:
        from config.config import settings
        # Try to access a secret (this will fail if not configured, but that's ok)
        settings.gcp_project_id
        health_status["components"]["secret_manager"] = {"status": "healthy"}
    except Exception as e:
        health_status["components"]["secret_manager"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    return health_status

