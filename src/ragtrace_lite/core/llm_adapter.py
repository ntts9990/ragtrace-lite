"""
LLM adapter module - maintains backward compatibility

This module re-exports the modularized LLM adapter components
to maintain backward compatibility with existing code.
"""

from .llm.base_adapter import LLMAdapter
from .llm.adapter_factory import LLMAdapterFactory

# For backward compatibility
from_config = LLMAdapterFactory.create_from_config

__all__ = [
    'LLMAdapter',
    'from_config'
]

# Create convenience function for backward compatibility
def create_llm_adapter(config):
    """
    Create LLM adapter from configuration (backward compatibility)
    
    Args:
        config: Configuration dictionary
        
    Returns:
        LLMAdapter instance
    """
    return LLMAdapterFactory.create_from_config(config)