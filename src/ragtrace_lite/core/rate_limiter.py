"""Advanced rate limiting for LLM API calls"""

import time
import asyncio
import random
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging
from threading import RLock
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    requests_per_second: float = 0.2  # 5초 간격 (기본값)
    burst_size: int = 1  # 버스트 허용 크기
    backoff_factor: float = 2.0  # 지수 백오프 팩터
    max_backoff: float = 60.0  # 최대 백오프 시간
    jitter_range: float = 0.1  # 지터 범위 (10%)

class TokenBucketRateLimiter:
    """Token bucket based rate limiter with exponential backoff"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.tokens = config.burst_size
        self.last_refill = time.time()
        self.failure_count = 0
        self.last_failure_time = 0
        self._lock = RLock()
        
    def can_proceed(self) -> bool:
        """Check if request can proceed based on token bucket"""
        with self._lock:
            now = time.time()
            
            # Refill tokens based on time passed
            time_passed = now - self.last_refill
            tokens_to_add = time_passed * self.config.requests_per_second
            self.tokens = min(self.config.burst_size, self.tokens + tokens_to_add)
            self.last_refill = now
            
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False
    
    def get_wait_time(self) -> float:
        """Get time to wait until next token is available"""
        with self._lock:
            if self.tokens >= 1:
                return 0
            
            # Calculate base wait time for next token
            base_wait = (1 - self.tokens) / self.config.requests_per_second
            
            # Add exponential backoff if there were recent failures
            if self.failure_count > 0:
                now = time.time()
                time_since_failure = now - self.last_failure_time
                
                # Reset failure count if enough time has passed
                if time_since_failure > self.config.max_backoff:
                    self.failure_count = 0
                else:
                    # Apply exponential backoff
                    backoff = min(
                        self.config.max_backoff,
                        self.config.backoff_factor ** self.failure_count
                    )
                    base_wait = max(base_wait, backoff)
            
            # Add jitter to prevent thundering herd
            jitter = random.uniform(-self.config.jitter_range, self.config.jitter_range)
            return max(0.1, base_wait * (1 + jitter))
    
    def record_success(self):
        """Record successful API call"""
        with self._lock:
            # Gradually reduce failure count on success
            if self.failure_count > 0:
                self.failure_count = max(0, self.failure_count - 1)
                logger.debug(f"Success recorded, failure count reduced to {self.failure_count}")
    
    def record_failure(self):
        """Record failed API call (rate limit or other error)"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            logger.warning(f"Failure recorded, failure count increased to {self.failure_count}")

class AdaptiveRateLimiter:
    """Adaptive rate limiter that adjusts based on API response patterns"""
    
    def __init__(self, provider: str, config: Optional[Dict[str, Any]] = None):
        self.provider = provider
        self.config = RateLimitConfig()
        
        # Apply provider-specific defaults
        if provider == "hcx":
            self.config.requests_per_second = 0.2  # 5초 간격
        elif provider == "gemini":
            self.config.requests_per_second = 0.5  # 2초 간격
        
        # Override with custom config
        if config:
            for key, value in config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
        
        self.limiter = TokenBucketRateLimiter(self.config)
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'rate_limited_requests': 0,
            'total_wait_time': 0
        }
    
    async def acquire(self) -> float:
        """
        Acquire permission to make API call
        
        Returns:
            Time waited before permission was granted
        """
        start_time = time.time()
        
        if self.limiter.can_proceed():
            return 0
        
        wait_time = self.limiter.get_wait_time()
        logger.info(f"Rate limiting: waiting {wait_time:.2f}s before {self.provider} API call")
        
        await asyncio.sleep(wait_time)
        
        total_wait = time.time() - start_time
        self.stats['total_wait_time'] += total_wait
        return total_wait
    
    def acquire_sync(self) -> float:
        """Synchronous version of acquire()"""
        start_time = time.time()
        
        if self.limiter.can_proceed():
            return 0
        
        wait_time = self.limiter.get_wait_time()
        logger.info(f"Rate limiting: waiting {wait_time:.2f}s before {self.provider} API call")
        
        time.sleep(wait_time)
        
        total_wait = time.time() - start_time
        self.stats['total_wait_time'] += total_wait
        return total_wait
    
    def record_request_result(self, success: bool, is_rate_limit: bool = False):
        """Record the result of an API request"""
        self.stats['total_requests'] += 1
        
        if success:
            self.limiter.record_success()
            self.stats['successful_requests'] += 1
            logger.debug(f"{self.provider} API call succeeded")
        else:
            self.limiter.record_failure()
            if is_rate_limit:
                self.stats['rate_limited_requests'] += 1
                logger.warning(f"{self.provider} API call rate limited")
            else:
                logger.warning(f"{self.provider} API call failed")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        stats = self.stats.copy()
        stats['success_rate'] = (
            stats['successful_requests'] / stats['total_requests'] 
            if stats['total_requests'] > 0 else 0
        )
        stats['avg_wait_time'] = (
            stats['total_wait_time'] / stats['total_requests']
            if stats['total_requests'] > 0 else 0
        )
        stats['current_failure_count'] = self.limiter.failure_count
        return stats

# Global rate limiters per provider
_rate_limiters: Dict[str, AdaptiveRateLimiter] = {}
_limiter_lock = RLock()

def get_rate_limiter(provider: str, config: Optional[Dict[str, Any]] = None) -> AdaptiveRateLimiter:
    """Get or create rate limiter for provider"""
    with _limiter_lock:
        if provider not in _rate_limiters:
            _rate_limiters[provider] = AdaptiveRateLimiter(provider, config)
        return _rate_limiters[provider]

def reset_rate_limiter(provider: str):
    """Reset rate limiter for provider (useful for testing)"""
    with _limiter_lock:
        if provider in _rate_limiters:
            del _rate_limiters[provider]