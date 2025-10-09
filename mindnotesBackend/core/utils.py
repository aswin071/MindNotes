"""
Utility functions for performance optimization
"""
from functools import wraps
from django.core.cache import cache
from django.db import connection
from typing import Any, Callable
import hashlib
import json


def cache_result(timeout: int = 300, key_prefix: str = ''):
    """
    Decorator to cache function results in Redis

    Args:
        timeout: Cache timeout in seconds (default 5 minutes)
        key_prefix: Custom prefix for cache key
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Generate cache key from function name and arguments
            key_parts = [key_prefix or func.__name__]

            # Add args to key
            for arg in args:
                if hasattr(arg, 'id'):
                    key_parts.append(str(arg.id))
                else:
                    key_parts.append(str(arg))

            # Add kwargs to key
            if kwargs:
                kwargs_str = json.dumps(kwargs, sort_keys=True)
                kwargs_hash = hashlib.md5(kwargs_str.encode()).hexdigest()[:8]
                key_parts.append(kwargs_hash)

            cache_key = ':'.join(key_parts)

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)

            return result
        return wrapper
    return decorator


def invalidate_cache(key_pattern: str):
    """
    Invalidate cache keys matching pattern

    Args:
        key_pattern: Pattern to match cache keys (e.g., 'user:123:*')
    """
    cache.delete_pattern(key_pattern)


def get_query_count():
    """Get the number of database queries executed"""
    return len(connection.queries)


def reset_query_count():
    """Reset database query counter"""
    connection.queries_log.clear()


def bulk_create_optimized(model_class, objects, batch_size=500):
    """
    Optimized bulk create with batching

    Args:
        model_class: Django model class
        objects: List of model instances
        batch_size: Number of objects per batch
    """
    created = []
    for i in range(0, len(objects), batch_size):
        batch = objects[i:i + batch_size]
        created.extend(
            model_class.objects.bulk_create(batch, ignore_conflicts=False)
        )
    return created


def bulk_update_optimized(model_class, objects, fields, batch_size=500):
    """
    Optimized bulk update with batching

    Args:
        model_class: Django model class
        objects: List of model instances
        fields: List of field names to update
        batch_size: Number of objects per batch
    """
    for i in range(0, len(objects), batch_size):
        batch = objects[i:i + batch_size]
        model_class.objects.bulk_update(batch, fields)
