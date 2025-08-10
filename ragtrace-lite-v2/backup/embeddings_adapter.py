"""
Deprecated: use `ragtrace_lite.core.embeddings_adapter_v2` instead.
This module provides a thin compatibility layer for legacy imports.
"""

from .embeddings_adapter_v2 import EmbeddingsAdapter  # noqa: F401
from .providers.local_embedding_provider import (
    LocalBGEProvider as LocalBGEEmbeddings,  # noqa: F401
)
from .providers.api_embedding_provider import (
    APIEmbeddingProvider as APIBGEEmbeddings,  # noqa: F401
)

__all__ = [
    "EmbeddingsAdapter",
    "LocalBGEEmbeddings",
    "APIBGEEmbeddings",
]
