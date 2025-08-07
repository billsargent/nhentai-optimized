# coding: utf-8
import time
import asyncio
import random
from functools import wraps

from nhentai.logger import logger

class RateLimiter:
    """Adaptive rate limiting for HTTP requests."""
    
    def __init__(self, initial_rate=5, min_rate=1, max_rate=10):
        self.current_rate = initial_rate  # Requests per second
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.success_count = 0
        self.fail_count = 0
        self.last_adjustment = time.time()
        self.lock = asyncio.Lock()
    
    async def wait(self):
        """Wait for an appropriate time before the next request."""
        async with self.lock:
            # Calculate wait time based on current rate
            wait_time = 1.0 / self.current_rate
            # Add small jitter to prevent request bursts
            jitter = random.uniform(0, 0.1)
            await asyncio.sleep(wait_time + jitter)
    
    async def success(self):
        """Record a successful request."""
        async with self.lock:
            self.success_count += 1
            self._maybe_adjust_rate()
    
    async def failure(self):
        """Record a failed request."""
        async with self.lock:
            self.fail_count += 1
            self._maybe_adjust_rate()
    
    def _maybe_adjust_rate(self):
        """Adaptively adjust the request rate based on success/failure ratio."""
        now = time.time()
        # Only adjust rate every 5 seconds
        if now - self.last_adjustment < 5:
            return
            
        total = self.success_count + self.fail_count
        if total < 5:
            # Not enough data to make a decision
            return
            
        success_ratio = self.success_count / total
        
        if success_ratio > 0.95:
            # Very successful, increase rate
            self.current_rate = min(self.current_rate * 1.1, self.max_rate)
            logger.info(f"Increased request rate to {self.current_rate:.2f} req/s")
        elif success_ratio < 0.8:
            # Too many failures, decrease rate
            self.current_rate = max(self.current_rate * 0.8, self.min_rate)
            logger.info(f"Decreased request rate to {self.current_rate:.2f} req/s")
            
        # Reset counters
        self.success_count = 0
        self.fail_count = 0
        self.last_adjustment = now

# Global rate limiter instance
rate_limiter = RateLimiter()

async def with_retry(func, *args, max_retries=3, backoff_factor=1.5, **kwargs):
    """
    Execute a function with exponential backoff retry logic.
    
    Args:
        func: Async function to execute
        max_retries: Maximum number of retries
        backoff_factor: Multiplier for backoff time between retries
        *args, **kwargs: Arguments to pass to the function
    """
    retries = 0
    last_exception = None
    
    while retries <= max_retries:
        try:
            # Wait based on rate limiter
            await rate_limiter.wait()
            
            # Execute the function
            result = await func(*args, **kwargs)
            
            # Record success and return the result
            await rate_limiter.success()
            return result
            
        except Exception as e:
            await rate_limiter.failure()
            last_exception = e
            retries += 1
            
            if retries <= max_retries:
                # Calculate backoff time with jitter
                backoff_time = (backoff_factor ** retries) + random.uniform(0, 1)
                logger.warning(f"Retry {retries}/{max_retries} after {backoff_time:.2f}s: {str(e)}")
                await asyncio.sleep(backoff_time)
            else:
                logger.error(f"Failed after {max_retries} retries: {str(e)}")
                
    # If we get here, all retries have failed
    if last_exception:
        raise last_exception
    return None
