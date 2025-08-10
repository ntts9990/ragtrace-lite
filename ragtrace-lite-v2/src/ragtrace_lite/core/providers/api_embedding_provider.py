"""API-based Embedding Provider"""

import httpx
import json
import logging
from typing import List, Optional, Dict, Any
import asyncio

from .base import EmbeddingProvider

logger = logging.getLogger(__name__)


class APIEmbeddingProvider(EmbeddingProvider):
    """API-based embedding provider"""
    
    def __init__(
        self,
        api_url: str,
        api_key: str,
        model_name: str = "bge-m3",
        timeout: int = 30,
        max_batch_size: int = 100
    ):
        self.api_url = api_url
        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout
        self.max_batch_size = max_batch_size
        self.client = httpx.Client(timeout=self.timeout)
        self.async_client = httpx.AsyncClient(timeout=self.timeout)
        self._dimension = None
    
    def encode(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Encode texts to embeddings synchronously"""
        if not texts:
            return []
        
        # Limit batch size to max allowed
        effective_batch_size = min(batch_size, self.max_batch_size)
        
        all_embeddings = []
        for i in range(0, len(texts), effective_batch_size):
            batch = texts[i:i + effective_batch_size]
            batch_embeddings = self._encode_batch(batch)
            all_embeddings.extend(batch_embeddings)
        
        logger.debug(f"Encoded {len(texts)} texts via API")
        return all_embeddings
    
    def _encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Encode a batch of texts"""
        headers = self._get_headers()
        data = self._get_payload(texts)
        
        try:
            response = self.client.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            # Extract embeddings from response
            embeddings = self._extract_embeddings(result)
            
            # Cache dimension if not set
            if embeddings and self._dimension is None:
                self._dimension = len(embeddings[0])
            
            return embeddings
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error for embedding API: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error for embedding API: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from embedding API")
            raise ValueError("Invalid JSON response from embedding API")
    
    async def encode_async(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Encode texts to embeddings asynchronously"""
        if not texts:
            return []
        
        # Limit batch size to max allowed
        effective_batch_size = min(batch_size, self.max_batch_size)
        
        # Create tasks for concurrent processing
        tasks = []
        for i in range(0, len(texts), effective_batch_size):
            batch = texts[i:i + effective_batch_size]
            task = self._encode_batch_async(batch)
            tasks.append(task)
        
        # Execute all batches concurrently
        batch_results = await asyncio.gather(*tasks)
        
        # Flatten results
        all_embeddings = []
        for batch_embeddings in batch_results:
            all_embeddings.extend(batch_embeddings)
        
        logger.debug(f"Encoded {len(texts)} texts via API (async)")
        return all_embeddings
    
    async def _encode_batch_async(self, texts: List[str]) -> List[List[float]]:
        """Encode a batch of texts asynchronously"""
        headers = self._get_headers()
        data = self._get_payload(texts)
        
        try:
            response = await self.async_client.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            # Extract embeddings from response
            embeddings = self._extract_embeddings(result)
            
            # Cache dimension if not set
            if embeddings and self._dimension is None:
                self._dimension = len(embeddings[0])
            
            return embeddings
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error for embedding API: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error for embedding API: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from embedding API")
            raise ValueError("Invalid JSON response from embedding API")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for requests"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _get_payload(self, texts: List[str]) -> Dict[str, Any]:
        """Get request payload"""
        return {
            "model": self.model_name,
            "input": texts,
            "encoding_format": "float"
        }
    
    def _extract_embeddings(self, response_data: Dict[str, Any]) -> List[List[float]]:
        """Extract embeddings from API response"""
        # This should be customized based on your API response format
        # Common formats:
        # OpenAI-style: {"data": [{"embedding": [...]}, ...]}
        # Custom format: {"embeddings": [[...], ...]}
        
        if "data" in response_data:
            # OpenAI-style format
            return [item["embedding"] for item in response_data["data"]]
        elif "embeddings" in response_data:
            # Direct embeddings format
            return response_data["embeddings"]
        else:
            raise ValueError(f"Unknown response format: {response_data.keys()}")
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension"""
        if self._dimension is None:
            # Try to get dimension by encoding a test string
            try:
                test_embeddings = self.encode(["test"])
                if test_embeddings:
                    self._dimension = len(test_embeddings[0])
                else:
                    self._dimension = 1024  # Default fallback
            except:
                self._dimension = 1024  # Default fallback
        
        return self._dimension
    
    async def aclose(self):
        """Close async client"""
        if hasattr(self, 'async_client') and self.async_client:
            await self.async_client.aclose()
    
    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'client') and self.client:
            try:
                self.client.close()
            except:
                pass