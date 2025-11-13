"""
Caching utilities for improving performance and reducing API calls.
"""
import time
import hashlib
import json
import logging
from typing import Any, Optional, Callable, TypeVar, Dict
from functools import wraps
from functools import lru_cache as functools_lru_cache

logger = logging.getLogger(__name__)

T = TypeVar('T')


class TTLCache:
    """Time-to-live cache implementation."""
    
    def __init__(self, ttl_seconds: int = 300):
        """
        Initialize TTL cache.
        
        Args:
            ttl_seconds: Time to live in seconds
        """
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, tuple[Any, float]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if not expired.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if expired/not found
        """
        if key not in self._cache:
            return None
        
        value, timestamp = self._cache[key]
        
        if time.time() - timestamp > self.ttl_seconds:
            del self._cache[key]
            return None
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        self._cache[key] = (value, time.time())
    
    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
    
    def invalidate(self, key: str) -> None:
        """
        Invalidate a specific cache key.
        
        Args:
            key: Cache key to invalidate
        """
        if key in self._cache:
            del self._cache[key]


# Global cache instance
_global_cache = TTLCache(ttl_seconds=300)


def cached(ttl_seconds: int = 300, key_func: Optional[Callable] = None):
    """
    Decorator for caching function results with TTL.
    
    Args:
        ttl_seconds: Time to live in seconds
        key_func: Optional function to generate cache key from arguments
    
    Example:
        @cached(ttl_seconds=600)
        def expensive_operation(param1, param2):
            return compute_result(param1, param2)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache = TTLCache(ttl_seconds=ttl_seconds)
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default: hash arguments
                key_data = json.dumps({
                    "args": args,
                    "kwargs": kwargs
                }, sort_keys=True, default=str)
                cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Check cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value
            
            # Compute and cache
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            logger.debug(f"Cache miss for {func.__name__}, result cached")
            
            return result
        
        # Add cache management methods
        wrapper.cache_clear = cache.clear
        wrapper.cache_invalidate = cache.invalidate
        
        return wrapper
    return decorator


def cache_key_from_args(*args, **kwargs) -> str:
    """Generate cache key from function arguments."""
    key_data = json.dumps({
        "args": args,
        "kwargs": kwargs
    }, sort_keys=True, default=str)
    return hashlib.md5(key_data.encode()).hexdigest()

