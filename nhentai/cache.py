# coding: utf-8
import os
import json
import time
import hashlib
from functools import wraps

from nhentai import constant
from nhentai.logger import logger

class Cache:
    def __init__(self, max_age=3600):  # 1 hour default cache lifetime
        self.max_age = max_age
        self.cache_dir = os.path.join(os.path.expanduser('~'), '.nhentai', 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def _get_cache_path(self, key):
        """Generate a cache file path from a cache key"""
        if isinstance(key, str):
            key_hash = hashlib.md5(key.encode()).hexdigest()
        else:
            key_hash = hashlib.md5(str(key).encode()).hexdigest()
        return os.path.join(self.cache_dir, key_hash)
        
    def get(self, key):
        """Get a cached response if it exists and is not expired"""
        cache_path = self._get_cache_path(key)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                    if time.time() - data['timestamp'] < self.max_age:
                        logger.info(f"Cache hit for {key}")
                        return data['content']
                    else:
                        logger.info(f"Cache expired for {key}")
            except Exception as e:
                logger.error(f"Error reading cache: {e}")
        logger.info(f"Cache miss for {key}")
        return None
        
    def set(self, key, content):
        """Save response to cache"""
        cache_path = self._get_cache_path(key)
        try:
            with open(cache_path, 'w') as f:
                json.dump({
                    'timestamp': time.time(),
                    'content': content
                }, f)
            return True
        except Exception as e:
            logger.error(f"Error writing to cache: {e}")
            return False
            
    def clear(self):
        """Clear all cached responses"""
        for file in os.listdir(self.cache_dir):
            try:
                os.remove(os.path.join(self.cache_dir, file))
            except Exception as e:
                logger.error(f"Error removing cache file {file}: {e}")

# Create a global cache instance
cache = Cache()

def cached(key_func=None, max_age=None):
    """
    Decorator for caching function responses.
    
    Args:
        key_func: Function that takes the same args as the wrapped function 
                 and returns a cache key. Default is the URL parameter.
        max_age: Override the default cache lifetime.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default assumes first positional arg after 'self' is URL
                if len(args) >= 2:
                    cache_key = args[1]  # args[0] is typically 'self' or method
                else:
                    cache_key = kwargs.get('url')
                    
            if not cache_key:
                # No suitable cache key found, just call the function
                return func(*args, **kwargs)
            
            # Use specific max_age if provided, otherwise use default
            current_max_age = max_age if max_age is not None else cache.max_age
            
            # Check cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
                
            # Call the original function
            result = func(*args, **kwargs)
            
            # Cache the result
            cache.set(cache_key, result)
            return result
        return wrapper
    return decorator
