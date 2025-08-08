"""로컬 BGE-M3 임베딩 모델 래퍼"""

import os
import logging
from typing import List, Optional
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)


class LocalBGEEmbeddings:
    """로컬 BGE-M3 모델을 사용한 임베딩"""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Args:
            model_path: BGE-M3 모델 경로
        """
        if model_path is None:
            # 기본 경로: 프로젝트 루트의 models/bge-m3
            project_root = Path(__file__).parent.parent.parent.parent.parent
            model_path = project_root / "models" / "bge-m3"
        else:
            model_path = Path(model_path)
        
        if not model_path.exists():
            raise FileNotFoundError(f"BGE-M3 model not found at {model_path}")
        
        self.model_path = str(model_path)
        self.model = None
        self.tokenizer = None
        self._load_model()
    
    def _load_model(self):
        """모델 로드"""
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"Loading BGE-M3 model from {self.model_path}")
            self.model = SentenceTransformer(self.model_path)
            logger.info("BGE-M3 model loaded successfully")
            
        except ImportError:
            logger.error("sentence-transformers not installed. Installing...")
            import subprocess
            subprocess.check_call(["pip", "install", "sentence-transformers"])
            
            # 재시도
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_path)
            logger.info("BGE-M3 model loaded after installing dependencies")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """문서 임베딩
        
        Args:
            texts: 임베딩할 텍스트 리스트
            
        Returns:
            임베딩 벡터 리스트
        """
        if not texts:
            return []
        
        # BGE-M3는 문서에 대해 특별한 프리픽스를 사용하지 않음
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        
        return embeddings.tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """쿼리 임베딩
        
        Args:
            text: 임베딩할 쿼리 텍스트
            
        Returns:
            임베딩 벡터
        """
        # BGE-M3는 쿼리에 대해 특별한 프리픽스를 사용하지 않음
        embedding = self.model.encode(
            [text],
            normalize_embeddings=True,
            show_progress_bar=False
        )[0]
        
        return embedding.tolist()
    
    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """비동기 문서 임베딩 (동기 버전 사용)"""
        return self.embed_documents(texts)
    
    async def aembed_query(self, text: str) -> List[float]:
        """비동기 쿼리 임베딩 (동기 버전 사용)"""
        return self.embed_query(text)


# LangChain 호환 래퍼
class BGEEmbeddings:
    """LangChain 호환 BGE-M3 임베딩"""
    
    def __init__(self, model_path: Optional[str] = None):
        self._embeddings = LocalBGEEmbeddings(model_path)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """문서 임베딩"""
        return self._embeddings.embed_documents(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """쿼리 임베딩"""
        return self._embeddings.embed_query(text)
    
    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """비동기 문서 임베딩"""
        return await self._embeddings.aembed_documents(texts)
    
    async def aembed_query(self, text: str) -> List[float]:
        """비동기 쿼리 임베딩"""
        return await self._embeddings.aembed_query(text)