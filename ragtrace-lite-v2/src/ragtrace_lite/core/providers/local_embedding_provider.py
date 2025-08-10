"""Local BGE-M3 Embedding Provider"""

import logging
from pathlib import Path
from typing import List, Optional
import asyncio

from .base import EmbeddingProvider

logger = logging.getLogger(__name__)


class LocalBGEProvider(EmbeddingProvider):
    """Local BGE-M3 embedding provider"""
    
    def __init__(self, model_path: Optional[str] = None, use_gpu: bool = False):
        """
        Args:
            model_path: Path to BGE-M3 model
            use_gpu: Whether to use GPU for inference
        """
        if model_path is None:
            # Default path relative to project root
            project_root = Path(__file__).parent.parent.parent.parent
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
            logger.error("sentence-transformers not available. Install with: pip install sentence-transformers")
            raise
        except Exception as e:
            logger.error(f"Failed to load BGE-M3 model: {e}")
            raise
    
    def encode(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Encode texts to embeddings synchronously"""
        if not texts:
            return []
        
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        try:
            # Process in batches
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                embeddings = self.model.encode(batch, convert_to_numpy=True, show_progress_bar=False)
                all_embeddings.extend(embeddings.tolist())
            
            logger.debug(f"Encoded {len(texts)} texts to embeddings")
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Error encoding texts: {e}")
            raise
    
    async def encode_async(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Encode texts to embeddings asynchronously"""
        # Run the synchronous encoding in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.encode, texts, batch_size)
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension"""
        return 1024  # BGE-M3 embedding dimension
    
    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'model') and self.model is not None:
            try:
                # Clear model from memory
                del self.model
            except:
                pass