"""
Tests for retry utility
"""

import pytest
import time
from unittest.mock import Mock, patch
from googleapiclient.errors import HttpError
from gcphound.utils.retry import retry_with_backoff, RateLimiter


class TestRetryWithBackoff:
    """Test the retry_with_backoff decorator"""
    
    def test_successful_call_no_retry(self):
        """Test successful function call without retry"""
        mock_func = Mock(return_value="success")
        decorated_func = retry_with_backoff(max_retries=3)(mock_func)
        
        result = decorated_func()
        
        assert result == "success"
        assert mock_func.call_count == 1
    
    def test_retry_on_transient_error(self):
        """Test retry on transient HTTP errors (500, 502, 503, 504)"""
        mock_resp = Mock(status=503)
        mock_func = Mock(side_effect=[
            HttpError(mock_resp, b'Service Unavailable'),
            HttpError(mock_resp, b'Service Unavailable'),
            "success"
        ])
        
        decorated_func = retry_with_backoff(max_retries=3, initial_delay=0.01)(mock_func)
        
        result = decorated_func()
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    def test_retry_on_rate_limit_error(self):
        """Test retry on rate limit error (429)"""
        mock_resp = Mock(status=429)
        mock_func = Mock(side_effect=[
            HttpError(mock_resp, b'Too Many Requests'),
            "success"
        ])
        
        decorated_func = retry_with_backoff(max_retries=3, initial_delay=0.01)(mock_func)
        
        result = decorated_func()
        
        assert result == "success"
        assert mock_func.call_count == 2
    
    def test_no_retry_on_client_error(self):
        """Test no retry on client errors (4xx except 429)"""
        mock_resp = Mock(status=404)
        mock_func = Mock(side_effect=HttpError(mock_resp, b'Not Found'))
        
        decorated_func = retry_with_backoff(max_retries=3)(mock_func)
        
        with pytest.raises(HttpError) as exc_info:
            decorated_func()
        
        assert exc_info.value.resp.status == 404
        assert mock_func.call_count == 1  # No retry
    
    def test_max_retries_exceeded(self):
        """Test that function fails after max retries"""
        mock_resp = Mock(status=503)
        mock_func = Mock(side_effect=HttpError(mock_resp, b'Service Unavailable'))
        
        decorated_func = retry_with_backoff(max_retries=3, initial_delay=0.01)(mock_func)
        
        with pytest.raises(HttpError):
            decorated_func()
        
        assert mock_func.call_count == 4  # Initial + 3 retries
    
    def test_exponential_backoff(self):
        """Test exponential backoff timing"""
        mock_resp = Mock(status=503)
        mock_func = Mock(side_effect=[
            HttpError(mock_resp, b'Service Unavailable'),
            HttpError(mock_resp, b'Service Unavailable'),
            "success"
        ])
        
        with patch('time.sleep') as mock_sleep:
            decorated_func = retry_with_backoff(
                max_retries=3,
                initial_delay=1,
                backoff_factor=2
            )(mock_func)
            
            result = decorated_func()
            
            assert result == "success"
            assert mock_sleep.call_count == 2
            # First retry: 1 second, Second retry: 2 seconds
            mock_sleep.assert_any_call(1)
            mock_sleep.assert_any_call(2)
    
    def test_max_delay_cap(self):
        """Test that delay is capped at max_delay"""
        mock_resp = Mock(status=503)
        mock_func = Mock(side_effect=[
            HttpError(mock_resp, b'Service Unavailable'),
            HttpError(mock_resp, b'Service Unavailable'),
            HttpError(mock_resp, b'Service Unavailable'),
            "success"
        ])
        
        with patch('time.sleep') as mock_sleep:
            decorated_func = retry_with_backoff(
                max_retries=5,
                initial_delay=1,
                backoff_factor=10,
                max_delay=5
            )(mock_func)
            
            result = decorated_func()
            
            assert result == "success"
            # All delays should be capped at 5
            for call in mock_sleep.call_args_list:
                assert call[0][0] <= 5
    
    def test_retry_with_custom_exception(self):
        """Test retry with non-HttpError exceptions"""
        mock_func = Mock(side_effect=[
            ConnectionError("Connection failed"),
            TimeoutError("Timeout"),
            "success"
        ])
        
        # Standard decorator only retries HttpError
        decorated_func = retry_with_backoff(max_retries=3)(mock_func)
        
        with pytest.raises(ConnectionError):
            decorated_func()
        
        assert mock_func.call_count == 1  # No retry for non-HttpError
    
    def test_retry_with_function_arguments(self):
        """Test retry with function that takes arguments"""
        mock_func = Mock(side_effect=[
            HttpError(Mock(status=503), b'Error'),
            "success"
        ])
        
        decorated_func = retry_with_backoff(max_retries=2, initial_delay=0.01)(mock_func)
        
        result = decorated_func("arg1", "arg2", kwarg1="value1")
        
        assert result == "success"
        assert mock_func.call_count == 2
        mock_func.assert_called_with("arg1", "arg2", kwarg1="value1")
    
    def test_retry_preserves_function_metadata(self):
        """Test that decorator preserves function metadata"""
        def test_function():
            """Test function docstring"""
            pass
        
        decorated_func = retry_with_backoff()(test_function)
        
        assert decorated_func.__name__ == "test_function"
        assert decorated_func.__doc__ == "Test function docstring"


class TestRateLimiter:
    """Test the RateLimiter class"""
    
    def test_rate_limiter_initialization(self):
        """Test RateLimiter initialization"""
        limiter = RateLimiter(requests_per_second=10, burst_size=20)
        
        assert limiter.requests_per_second == 10
        assert limiter.burst_size == 20
        assert limiter.tokens == 20  # Starts with full burst
    
    def test_rate_limiter_single_request(self):
        """Test single request within rate limit"""
        limiter = RateLimiter(requests_per_second=10, burst_size=10)
        
        start_time = time.time()
        with limiter:
            pass  # Simulate request
        end_time = time.time()
        
        # Should not delay for first request
        assert end_time - start_time < 0.1
        assert limiter.tokens == 9  # One token consumed
    
    def test_rate_limiter_burst_requests(self):
        """Test burst requests consume tokens"""
        limiter = RateLimiter(requests_per_second=10, burst_size=5)
        
        # Make 5 burst requests
        for _ in range(5):
            with limiter:
                pass
        
        # All tokens should be consumed (or very close to 0)
        assert limiter.tokens < 0.01  # Allow for small floating point differences
    
    def test_rate_limiter_exceeds_burst(self):
        """Test requests exceeding burst size"""
        limiter = RateLimiter(requests_per_second=10, burst_size=2)
        
        # Consume burst
        for _ in range(2):
            with limiter:
                pass
        
        # Next request should wait
        start_time = time.time()
        with limiter:
            pass
        end_time = time.time()
        
        # Should wait approximately 0.1 seconds (1/10 requests per second)
        assert 0.05 < end_time - start_time < 0.15
    
    def test_rate_limiter_token_refill(self):
        """Test tokens refill over time"""
        limiter = RateLimiter(requests_per_second=10, burst_size=5)
        
        # Consume all tokens
        for _ in range(5):
            with limiter:
                pass
        
        # Tokens should be close to 0
        assert limiter.tokens < 0.01
        
        # Wait for tokens to refill
        time.sleep(0.5)  # Should refill ~5 tokens
        
        # Trigger token update by acquiring 0 tokens
        limiter.acquire(0)
        
        # Check tokens have refilled (with some tolerance for timing)
        assert limiter.tokens > 2.0  # At least some tokens refilled
    
    def test_rate_limiter_concurrent_access(self):
        """Test rate limiter with simulated concurrent access"""
        limiter = RateLimiter(requests_per_second=10, burst_size=5)
        
        # Simulate multiple rapid requests
        request_times = []
        for _ in range(10):
            start = time.time()
            with limiter:
                request_times.append(time.time() - start)
        
        # First 5 should be fast (burst)
        for i in range(5):
            assert request_times[i] < 0.01
        
        # Remaining should be rate limited
        for i in range(5, 10):
            assert request_times[i] > 0.05
    
    def test_rate_limiter_context_manager_exception(self):
        """Test rate limiter handles exceptions in context"""
        limiter = RateLimiter(requests_per_second=10, burst_size=10)
        
        initial_tokens = limiter.tokens
        
        try:
            with limiter:
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Token should still be consumed even with exception
        assert limiter.tokens == initial_tokens - 1
    
    def test_rate_limiter_zero_burst_size(self):
        """Test rate limiter with zero burst size"""
        limiter = RateLimiter(requests_per_second=10, burst_size=0)
        
        # Should start with 0 tokens
        assert limiter.tokens == 0
        
        # Every request should wait
        start_time = time.time()
        with limiter:
            pass
        end_time = time.time()
        
        # Should wait for token
        assert end_time - start_time > 0.05
    
    def test_rate_limiter_high_rate(self):
        """Test rate limiter with high request rate"""
        limiter = RateLimiter(requests_per_second=1000, burst_size=100)
        
        # Should handle high rate without significant delays
        start_time = time.time()
        for _ in range(100):
            with limiter:
                pass
        end_time = time.time()
        
        # 100 requests within burst should be fast
        assert end_time - start_time < 0.1 