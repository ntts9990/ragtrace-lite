"""Base interfaces for LLM and Embedding providers"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import asyncio


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(
        self,
        api_url: str,
        api_key: str,
        model_name: str,
        temperature: float,
        max_tokens: int,
        timeout: int = 30
    ):
        self.api_url = api_url
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
    
    @abstractmethod
    def generate(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """Generate text synchronously"""
        pass
    
    @abstractmethod
    async def generate_async(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """Generate text asynchronously"""
        pass
    
    @abstractmethod
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for requests"""
        pass
    
    @abstractmethod
    def _get_payload(self, prompt: str, stop: Optional[List[str]]) -> Dict[str, Any]:
        """Get request payload"""
        pass
    
    async def aclose(self):
        """Close async resources (optional override)"""
        pass


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers"""
    
    @abstractmethod
    def encode(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Encode texts to embeddings synchronously"""
        pass
    
    @abstractmethod
    async def encode_async(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Encode texts to embeddings asynchronously"""
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Get embedding dimension"""
        pass
    
    async def aclose(self):
        """Close async resources (optional override)"""
        pass