"""
Caching utilities for improved performance
"""

import time
import json
import threading
from functools import wraps
from typing import Callable, Any, Optional


class SimpleCache:
    """Simple in-memory cache implementation"""

    def __init__(self, default_timeout=300):
        self.cache = {}
        self.timeouts = {}
        self.default_timeout = default_timeout

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self.cache:
            return None

        # Check if expired
        if key in self.timeouts:
            if time.time() > self.timeouts[key]:
                del self.cache[key]
                del self.timeouts[key]
                return None

        return self.cache[key]

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        """Set value in cache"""
        self.cache[key] = value
        if timeout is None:
            timeout = self.default_timeout

        if timeout > 0:
            self.timeouts[key] = time.time() + timeout

    def delete(self, key: str) -> None:
        """Delete value from cache"""
        if key in self.cache:
            del self.cache[key]
        if key in self.timeouts:
            del self.timeouts[key]

    def clear(self) -> None:
        """Clear all cache"""
        self.cache.clear()
        self.timeouts.clear()

    def get_stats(self) -> dict:
        """Get cache statistics"""
        return {
            'entries': len(self.cache),
            'timeout_entries': len(self.timeouts),
            'size_bytes': sum(len(json.dumps(v)) for v in self.cache.values())
        }


# Global cache instance (thread-safe)
_cache = None
_cache_lock = threading.Lock()


def get_cache(timeout=300):
    """Get or create global cache instance (thread-safe)"""
    global _cache
    if _cache is None:
        with _cache_lock:
            if _cache is None:
                _cache = SimpleCache(default_timeout=timeout)
    return _cache


def cached(timeout=300, key_prefix=''):
    """Decorator for caching function results"""

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache = get_cache(timeout)

            # Generate cache key from function name, args, and kwargs
            cache_key = f"{key_prefix or f.__name__}:{json.dumps([args, kwargs], sort_keys=True, default=str)}"

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Call function and cache result
            result = f(*args, **kwargs)
            cache.set(cache_key, result, timeout)

            return result

        return decorated_function

    return decorator


def cache_bust(key_pattern=''):
    """Decorator for clearing cache on function call"""

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            result = f(*args, **kwargs)

            # Clear cache entries matching pattern
            cache = get_cache()
            if key_pattern:
                keys_to_delete = [k for k in cache.cache.keys() if key_pattern in k]
                for key in keys_to_delete:
                    cache.delete(key)
            else:
                cache.clear()

            return result

        return decorated_function

    return decorator


class CacheStats:
    """Track cache statistics and hit rates"""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.total_calls = 0

    def record_hit(self):
        """Record a cache hit"""
        self.hits += 1
        self.total_calls += 1

    def record_miss(self):
        """Record a cache miss"""
        self.misses += 1
        self.total_calls += 1

    def get_hit_rate(self) -> float:
        """Get cache hit rate as percentage"""
        if self.total_calls == 0:
            return 0.0
        return (self.hits / self.total_calls) * 100

    def get_stats(self) -> dict:
        """Get statistics"""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'total_calls': self.total_calls,
            'hit_rate': self.get_hit_rate()
        }

    def reset(self):
        """Reset statistics"""
        self.hits = 0
        self.misses = 0
        self.total_calls = 0


# Global stats instance
_stats = CacheStats()


def get_cache_stats():
    """Get global cache statistics"""
    return _stats


def record_cache_hit():
    """Record cache hit"""
    _stats.record_hit()


def record_cache_miss():
    """Record cache miss"""
    _stats.record_miss()
