"""Enhanced embeddings adapter with provider abstraction"""

import logging
from typing import List, Optional, Union, Dict, Any
from pathlib import Path

from .providers.base import EmbeddingProvider
from .providers.local_embedding_provider import LocalBGEProvider
from .providers.api_embedding_provider import APIEmbeddingProvider

logger = logging.getLogger(__name__)


class EmbeddingsAdapter:
    """Unified embeddings adapter supporting local and API providers"""
    
    def __init__(
        self,
        provider_type: str = "local",
        model_path: Optional[str] = None,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: str = "bge-m3",
        use_gpu: bool = False,
        timeout: int = 30,
        max_batch_size: int = 100
    ):
        self.provider_type = provider_type
        self.provider: EmbeddingProvider = self._create_provider(
            provider_type=provider_type,
            model_path=model_path,
            api_url=api_url,
            api_key=api_key,
            model_name=model_name,
            use_gpu=use_gpu,
            timeout=timeout,
            max_batch_size=max_batch_size
        )
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "EmbeddingsAdapter":
        """Create adapter from configuration dictionary"""
        provider = config.get("provider", "local")
        
        if provider == "local":
            local_config = config.get("local", {})
            return cls(
                provider_type="local",
                model_path=local_config.get("model_path"),
                use_gpu=local_config.get("use_gpu", False)
            )
        elif provider == "api":
            api_config = config.get("api", {})
            return cls(
                provider_type="api",
                api_url=api_config.get("api_url"),
                api_key=api_config.get("api_key"),
                model_name=api_config.get("model_name", "bge-m3"),
                timeout=api_config.get("timeout", 30),
                max_batch_size=api_config.get("max_batch_size", 100)
            )
        else:
            raise ValueError(f"Unknown embedding provider: {provider}")
    
    
    def _create_provider(
        self,
        provider_type: str,
        model_path: Optional[str],
        api_url: Optional[str],
        api_key: Optional[str],
        model_name: str,
        use_gpu: bool,
        timeout: int,
        max_batch_size: int
    ) -> EmbeddingProvider:
        """Create the appropriate provider based on type"""
        
        if provider_type == "local":
            return LocalBGEProvider(
                model_path=model_path,
                use_gpu=use_gpu
            )
        elif provider_type == "api":
            if not api_url or not api_key:
                raise ValueError("API provider requires api_url and api_key")
            
            return APIEmbeddingProvider(
                api_url=api_url,
                api_key=api_key,
                model_name=model_name,
                timeout=timeout,
                max_batch_size=max_batch_size
            )
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed documents (RAGAS compatibility)"""
        return self.provider.encode(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query (RAGAS compatibility)"""
        embeddings = self.provider.encode([text])
        return embeddings[0] if embeddings else []
    
    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed documents asynchronously (RAGAS compatibility)"""
        return await self.provider.encode_async(texts)
    
    async def aembed_query(self, text: str) -> List[float]:
        """Embed a single query asynchronously (RAGAS compatibility)"""
        embeddings = await self.provider.encode_async([text])
        return embeddings[0] if embeddings else []
    
    def encode(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Direct encoding interface"""
        return self.provider.encode(texts, batch_size)
    
    async def encode_async(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Direct async encoding interface"""
        return await self.provider.encode_async(texts, batch_size)
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension"""
        return self.provider.dimension
    
    async def aclose(self):
        """Close provider resources"""
        await self.provider.aclose()
    
    def __enter__(self):
        """Context manager support"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        pass
    
    async def __aenter__(self):
        """Async context manager support"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager cleanup"""
        await self.aclose()


# Factory function for backward compatibility
def create_embeddings_adapter(
    provider: str = "local",
    model_path: Optional[str] = None,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
    use_gpu: bool = False,
    **kwargs
) -> EmbeddingsAdapter:
    """Factory function to create embeddings adapter"""
    
    return EmbeddingsAdapter(
        provider_type=provider,
        model_path=model_path,
        api_url=api_url,
        api_key=api_key,
        use_gpu=use_gpu,
        **kwargs
    )


# Legacy class names for backward compatibility
LocalBGEEmbeddings = LocalBGEProvider
APIEmbeddings = APIEmbeddingProvider