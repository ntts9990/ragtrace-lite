"""Base LLM adapter implementing LangChain interface"""

import logging
import asyncio
from typing import Any, List, Optional, Dict, Union
from langchain_core.language_models.llms import LLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun, AsyncCallbackManagerForLLMRun

from ..providers import HCXProvider, GeminiProvider
from .prompt_enhancer import PromptEnhancer
from .response_processor import ResponseProcessor

logger = logging.getLogger(__name__)


class LLMAdapter(LLM):
    """Unified adapter for multiple LLM providers with RAGAS support"""
    
    provider: str = "hcx"
    api_url: str = ""
    api_key: str = ""
    model_name: str = ""
    temperature: float = 0.1
    max_tokens: int = 1024
    timeout: int = 30
    
    _provider_instance: Optional[Union[HCXProvider, GeminiProvider]] = None
    _prompt_enhancer: PromptEnhancer = None
    _response_processor: ResponseProcessor = None
    
    def __init__(self, **kwargs):
        """Initialize LLM adapter with provider configuration"""
        super().__init__(**kwargs)
        
        # Initialize utilities
        self._prompt_enhancer = PromptEnhancer()
        self._response_processor = ResponseProcessor()
        
        # Initialize provider based on type
        if self.provider == "hcx":
            self._provider_instance = HCXProvider(
                api_url=self.api_url,
                api_key=self.api_key,
                model_name=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout
            )
            logger.info("Initialized HCX provider")
        elif self.provider == "gemini":
            self._provider_instance = GeminiProvider(
                api_url=self.api_url,
                api_key=self.api_key,
                model_name=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout
            )
            logger.info("Initialized Gemini provider")
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    @property
    def _llm_type(self) -> str:
        """Return identifier for the LLM"""
        return f"ragtrace_{self.provider}"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call LLM synchronously"""
        # Check for RAGAS evaluation prompt patterns
        enhanced_prompt = self._prompt_enhancer.enhance_prompt(prompt)
        
        try:
            # Use provider's generate method
            response = self._provider_instance.generate(enhanced_prompt, stop)
            
            # Clean and validate response for RAGAS
            cleaned_response = self._response_processor.clean_response(response, prompt)
            
            return cleaned_response
            
        except Exception as e:
            logger.error(f"Error calling {self.provider}: {e}")
            # Return fallback response for RAGAS
            return self._response_processor.get_fallback_response(prompt)
    
    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call LLM asynchronously"""
        # Check for RAGAS evaluation prompt patterns
        enhanced_prompt = self._prompt_enhancer.enhance_prompt(prompt)
        
        try:
            # Use provider's async generate method
            response = await self._provider_instance.generate_async(enhanced_prompt, stop)
            
            # Clean and validate response for RAGAS
            cleaned_response = self._response_processor.clean_response(response, prompt)
            
            return cleaned_response
            
        except Exception as e:
            logger.error(f"Error calling {self.provider} async: {e}")
            # Return fallback response for RAGAS
            return self._response_processor.get_fallback_response(prompt)
    
    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """Get rate limit statistics from provider"""
        if hasattr(self._provider_instance, 'get_rate_limit_stats'):
            return self._provider_instance.get_rate_limit_stats()
        return {}
    
    async def aclose(self):
        """Close async resources"""
        if self._provider_instance and hasattr(self._provider_instance, 'aclose'):
            await self._provider_instance.aclose()