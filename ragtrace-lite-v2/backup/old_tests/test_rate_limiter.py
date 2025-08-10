#!/usr/bin/env python
"""Test improved rate limiter functionality"""

import sys
sys.path.insert(0, 'src')

import time
import logging
from ragtrace_lite.core.rate_limiter import AdaptiveRateLimiter, RateLimitConfig

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_rate_limiter():
    """Test the new adaptive rate limiter"""
    
    print("🧪 Testing Advanced Rate Limiter")
    print("="*60)
    
    # Create a fast rate limiter for testing
    config = {
        'requests_per_second': 2.0,  # 0.5초 간격
        'burst_size': 2,
        'backoff_factor': 2.0,
        'max_backoff': 10.0,
        'jitter_range': 0.1
    }
    
    limiter = AdaptiveRateLimiter("test", config)
    
    print(f"✅ Created rate limiter for 'test' provider")
    print(f"   - Requests per second: {config['requests_per_second']}")
    print(f"   - Burst size: {config['burst_size']}")
    
    # Test burst requests (should be fast)
    print(f"\n🔥 Testing burst requests...")
    start_time = time.time()
    
    for i in range(2):  # Burst size
        wait_time = limiter.acquire_sync()
        print(f"Request {i+1}: waited {wait_time:.3f}s")
        limiter.record_request_result(success=True)
    
    burst_time = time.time() - start_time
    print(f"✅ Burst requests completed in {burst_time:.3f}s")
    
    # Test rate limited request (should wait)
    print(f"\n⏱️ Testing rate limited request...")
    start_time = time.time()
    wait_time = limiter.acquire_sync()
    limited_time = time.time() - start_time
    
    print(f"✅ Rate limited request waited {wait_time:.3f}s (actual: {limited_time:.3f}s)")
    limiter.record_request_result(success=True)
    
    # Test failure handling
    print(f"\n❌ Testing failure handling...")
    limiter.record_request_result(success=False, is_rate_limit=True)
    limiter.record_request_result(success=False, is_rate_limit=True)
    
    # Next request should have longer wait due to backoff
    start_time = time.time()
    wait_time = limiter.acquire_sync()
    backoff_time = time.time() - start_time
    
    print(f"✅ Request after failures waited {wait_time:.3f}s (actual: {backoff_time:.3f}s)")
    limiter.record_request_result(success=True)
    
    # Show statistics
    print(f"\n📊 Rate Limiter Statistics:")
    stats = limiter.get_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"   - {key}: {value:.3f}")
        else:
            print(f"   - {key}: {value}")
    
    print(f"\n🎉 Rate limiter test completed!")

def test_llm_adapter_integration():
    """Test rate limiter integration with LLMAdapter"""
    print(f"\n🔗 Testing LLMAdapter Integration")
    print("="*60)
    
    try:
        from ragtrace_lite.core.llm_adapter import LLMAdapter
        
        # Create LLMAdapter with test config
        adapter = LLMAdapter(
            provider="test",  # Use test provider
            api_key="test_key",
            model_name="test-model",
            rate_limit_delay=1.0  # 1초 간격
        )
        
        print(f"✅ LLMAdapter created with rate limiter")
        
        # Check rate limiter stats
        initial_stats = adapter.get_rate_limit_stats()
        print(f"📊 Initial stats: {initial_stats}")
        
        # Simulate successful API calls
        adapter.rate_limiter.record_request_result(success=True)
        adapter.rate_limiter.record_request_result(success=True)
        
        # Check updated stats
        updated_stats = adapter.get_rate_limit_stats()
        print(f"📊 Updated stats: {updated_stats}")
        
        print(f"✅ LLMAdapter integration test passed!")
        
    except Exception as e:
        print(f"⚠️ LLMAdapter integration test failed: {e}")

if __name__ == "__main__":
    test_rate_limiter()
    test_llm_adapter_integration()