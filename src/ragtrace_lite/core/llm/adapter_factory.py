"""Factory for creating LLM adapters from configuration"""

import os
import logging
from typing import Dict, Any, Optional

from .base_adapter import LLMAdapter

logger = logging.getLogger(__name__)


class LLMAdapterFactory:
    """Factory class for creating LLM adapters"""
    
    # Default API endpoints
    DEFAULT_ENDPOINTS = {
        "hcx": "https://clovastudio.stream.ntruss.com/testapp/v3/chat-completions/HCX-005",
        "gemini": "https://generativelanguage.googleapis.com/v1beta/models"
    }
    
    @classmethod
    def create_from_config(cls, config: Dict[str, Any]) -> LLMAdapter:
        """
        Create LLM adapter from configuration dictionary
        
        Args:
            config: Configuration dictionary with LLM settings
            
        Returns:
            Configured LLMAdapter instance
        """
        llm_config = config.get("llm", {})
        provider = llm_config.get("provider", "hcx")
        
        # Get provider-specific configuration
        provider_config = llm_config.get(provider, {})
        
        # Get API key from environment or config
        api_key = cls._get_api_key(provider, provider_config)
        
        # Get API URL with fallback to defaults
        api_url = provider_config.get("api_url", cls.DEFAULT_ENDPOINTS.get(provider))
        
        # Create adapter with configuration
        adapter = LLMAdapter(
            provider=provider,
            api_url=api_url,
            api_key=api_key,
            model_name=provider_config.get("model_name", cls._get_default_model(provider)),
            temperature=provider_config.get("temperature", 0.1),
            max_tokens=provider_config.get("max_tokens", 1024),
            timeout=provider_config.get("timeout", 30)
        )
        
        logger.info(f"Created LLM adapter for provider: {provider}")
        return adapter
    
    @classmethod
    def create_from_env(cls, provider: str = None) -> LLMAdapter:
        """
        Create LLM adapter from environment variables
        
        Args:
            provider: Provider name (defaults to DEFAULT_LLM env var)
            
        Returns:
            Configured LLMAdapter instance
        """
        # Determine provider
        if provider is None:
            provider = os.getenv("DEFAULT_LLM", "hcx")
        
        # Get API key from environment
        api_key = cls._get_api_key(provider, {})
        
        # Get other settings from environment
        api_url = os.getenv(f"{provider.upper()}_API_URL", cls.DEFAULT_ENDPOINTS.get(provider))
        model_name = os.getenv(f"{provider.upper()}_MODEL", cls._get_default_model(provider))
        temperature = float(os.getenv(f"{provider.upper()}_TEMPERATURE", "0.1"))
        max_tokens = int(os.getenv(f"{provider.upper()}_MAX_TOKENS", "1024"))
        
        # Create adapter
        adapter = LLMAdapter(
            provider=provider,
            api_url=api_url,
            api_key=api_key,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        logger.info(f"Created LLM adapter from environment for provider: {provider}")
        return adapter
    
    @staticmethod
    def _get_api_key(provider: str, config: Dict[str, Any]) -> str:
        """Get API key from environment or config"""
        # Check environment variable first
        env_var_name = {
            "hcx": "CLOVA_STUDIO_API_KEY",
            "gemini": "GEMINI_API_KEY"
        }.get(provider, f"{provider.upper()}_API_KEY")
        
        api_key = os.getenv(env_var_name)
        
        # Fall back to config
        if not api_key:
            api_key = config.get("api_key", "")
            
            # Handle template variables in config
            if api_key.startswith("${") and api_key.endswith("}"):
                env_var = api_key[2:-1]
                api_key = os.getenv(env_var, "")
        
        if not api_key:
            logger.warning(f"No API key found for {provider}")
        
        return api_key
    
    @staticmethod
    def _get_default_model(provider: str) -> str:
        """Get default model name for provider"""
        defaults = {
            "hcx": "HCX-005",
            "gemini": "gemini-2.5-flash-lite"
        }
        return defaults.get(provider, "default-model")