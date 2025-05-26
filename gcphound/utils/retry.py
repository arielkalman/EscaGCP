"""
Retry logic and rate limiting for API calls
"""

import time
import functools
from typing import Callable, Any, Optional, Type, Tuple
# Removed tenacity import - using simple retry logic instead
from googleapiclient.errors import HttpError
import threading
from collections import deque
from .logger import get_logger


logger = get_logger(__name__)


def is_retryable_error(error: HttpError) -> bool:
    """
    Check if an HTTP error is retryable
    
    Args:
        error: The HTTP error
        
    Returns:
        True if the error is retryable
    """
    if not isinstance(error, HttpError):
        return False
    
    # Retry on rate limit errors (429) and server errors (5xx)
    status = error.resp.status
    return status == 429 or (500 <= status < 600)


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (HttpError,)
) -> Callable:
    """
    Decorator for retrying functions with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Exponential backoff multiplier
        exceptions: Tuple of exception types to retry on
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            attempt = 0
            delay = initial_delay
            func_name = getattr(func, '__name__', repr(func))
            
            while attempt <= max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if isinstance(e, HttpError) and not is_retryable_error(e):
                        # Don't retry non-retryable errors
                        raise
                    
                    attempt += 1
                    if attempt > max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded for {func_name}")
                        raise
                    
                    # Log retry attempt
                    logger.warning(
                        f"Retry {attempt}/{max_retries} for {func_name} "
                        f"after error: {str(e)}. Waiting {delay:.1f}s"
                    )
                    
                    # Wait before retry
                    time.sleep(delay)
                    
                    # Calculate next delay with exponential backoff
                    delay = min(delay * backoff_factor, max_delay)
            
            return None  # Should never reach here
        
        return wrapper
    return decorator


class RateLimiter:
    """
    Token bucket rate limiter for API calls
    """
    
    def __init__(self, requests_per_second: float = 10.0, burst_size: int = 20):
        """
        Initialize rate limiter
        
        Args:
            requests_per_second: Sustained request rate
            burst_size: Maximum burst size
        """
        self.requests_per_second = requests_per_second
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = time.time()
        self.lock = threading.Lock()
        
        # Track request times for sliding window
        self.request_times = deque(maxlen=100)
    
    def acquire(self, tokens: int = 1) -> float:
        """
        Acquire tokens from the bucket, blocking if necessary
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            Time waited in seconds
        """
        wait_time = 0.0
        
        with self.lock:
            now = time.time()
            
            # Refill tokens based on time elapsed
            elapsed = now - self.last_update
            self.tokens = min(
                self.burst_size,
                self.tokens + elapsed * self.requests_per_second
            )
            self.last_update = now
            
            # Wait if not enough tokens
            if self.tokens < tokens:
                wait_time = (tokens - self.tokens) / self.requests_per_second
                time.sleep(wait_time)
                
                # Update tokens after waiting
                now = time.time()
                elapsed = now - self.last_update
                self.tokens = min(
                    self.burst_size,
                    self.tokens + elapsed * self.requests_per_second
                )
                self.last_update = now
            
            # Consume tokens
            self.tokens -= tokens
            
            # Track request time
            self.request_times.append(now)
        
        return wait_time
    
    def get_current_rate(self) -> float:
        """
        Get the current request rate (requests per second)
        
        Returns:
            Current rate
        """
        with self.lock:
            now = time.time()
            
            # Remove old request times (older than 1 minute)
            cutoff = now - 60
            while self.request_times and self.request_times[0] < cutoff:
                self.request_times.popleft()
            
            # Calculate rate over the last minute
            if len(self.request_times) < 2:
                return 0.0
            
            time_span = now - self.request_times[0]
            if time_span == 0:
                return 0.0
            
            return len(self.request_times) / time_span
    
    def __enter__(self):
        """Context manager entry"""
        self.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        pass


def rate_limited(limiter: RateLimiter) -> Callable:
    """
    Decorator to apply rate limiting to a function
    
    Args:
        limiter: RateLimiter instance
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Acquire token before making request
            wait_time = limiter.acquire()
            if wait_time > 0:
                func_name = getattr(func, '__name__', repr(func))
                logger.debug(f"Rate limited: waited {wait_time:.2f}s before {func_name}")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Advanced retry functionality removed - using simple retry_with_backoff instead 