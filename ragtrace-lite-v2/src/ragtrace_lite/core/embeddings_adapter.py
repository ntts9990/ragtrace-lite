"""Flexible embeddings adapter supporting local and API modes"""

import os
import logging
import requests
import json
from typing import List, Optional, Dict, Any
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)


class LocalBGEEmbeddings:
    """Local BGE-M3 model embeddings"""
    
    def __init__(self, model_path: Optional[str] = None, use_gpu: bool = False):
        """
        Args:
            model_path: Path to BGE-M3 model
            use_gpu: Whether to use GPU for inference
        """
        if model_path is None:
            # Default path relative to project root
            project_root = Path(__file__).parent.parent.parent
            model_path = project_root / "models" / "bge-m3"
        else:
            model_path = Path(model_path)
        
        if not model_path.exists():
            raise FileNotFoundError(f"BGE-M3 model not found at {model_path}")
        
        self.model_path = str(model_path)
        self.use_gpu = use_gpu
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the model"""
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"Loading BGE-M3 model from {self.model_path}")
            
            # Set device
            device = 'cuda' if self.use_gpu else 'cpu'
            self.model = SentenceTransformer(self.model_path, device=device)
            
            logger.info(f"BGE-M3 model loaded successfully (device: {device})")
            
        except ImportError:
            logger.error("sentence-transformers not installed")
            raise
        except Exception as e:
            logger.error(f"Failed to load BGE-M3 model: {e}")
            raise
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed documents"""
        if not texts:
            return []
        
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        
        return embeddings.tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """Embed query"""
        embedding = self.model.encode(
            [text],
            normalize_embeddings=True,
            show_progress_bar=False
        )[0]
        
        return embedding.tolist()


class APIBGEEmbeddings:
    """API-based BGE-M3 embeddings"""
    
    def __init__(
        self,
        api_url: str,
        model_name: str = "bge-m3",
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_batch_size: int = 100
    ):
        """
        Args:
            api_url: API endpoint for embeddings
            model_name: Model name on server
            api_key: API key if required
            timeout: Request timeout in seconds
            max_batch_size: Maximum batch size per request
        """
        self.api_url = api_url
        self.model_name = model_name
        self.api_key = api_key
        self.timeout = timeout
        self.max_batch_size = max_batch_size
    
    def _make_request(self, texts: List[str], is_query: bool = False) -> List[List[float]]:
        """Make API request for embeddings"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        # Split into batches if necessary
        all_embeddings = []
        
        for i in range(0, len(texts), self.max_batch_size):
            batch = texts[i:i + self.max_batch_size]
            
            payload = {
                "model": self.model_name,
                "texts": batch,
                "type": "query" if is_query else "document"
            }
            
            try:
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                result = response.json()
                embeddings = result.get("embeddings", [])
                all_embeddings.extend(embeddings)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"API request failed: {e}")
                raise
            except (KeyError, json.JSONDecodeError) as e:
                logger.error(f"Invalid API response: {e}")
                raise
        
        return all_embeddings
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed documents via API"""
        if not texts:
            return []
        
        return self._make_request(texts, is_query=False)
    
    def embed_query(self, text: str) -> List[float]:
        """Embed query via API"""
        embeddings = self._make_request([text], is_query=True)
        return embeddings[0] if embeddings else []


class EmbeddingsAdapter:
    """Unified embeddings adapter supporting multiple providers"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize embeddings adapter
        
        Args:
            config: Embeddings configuration
        """
        if config is None:
            from ..config.config_loader import get_config
            config_loader = get_config()
            config = config_loader.get_embeddings_config()
        
        self.provider = config.get("provider", "local")
        self._embeddings = None
        
        if self.provider == "local":
            self._embeddings = LocalBGEEmbeddings(
                model_path=config.get("model_path"),
                use_gpu=config.get("use_gpu", False)
            )
        elif self.provider == "api":
            self._embeddings = APIBGEEmbeddings(
                api_url=config.get("api_url"),
                model_name=config.get("model_name", "bge-m3"),
                api_key=config.get("api_key"),
                timeout=config.get("timeout", 30),
                max_batch_size=config.get("max_batch_size", 100)
            )
        else:
            raise ValueError(f"Unknown embeddings provider: {self.provider}")
        
        logger.info(f"Embeddings initialized: {self.provider}")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed documents"""
        return self._embeddings.embed_documents(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """Embed query"""
        return self._embeddings.embed_query(text)
    
    # LangChain compatibility methods
    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """Async embed documents (sync wrapper)"""
        return self.embed_documents(texts)
    
    async def aembed_query(self, text: str) -> List[float]:
        """Async embed query (sync wrapper)"""
        return self.embed_query(text)