"""
Unified AI Model Abstraction Layer
Provides a single interface for all AI operations across the system.
Supports OpenAI, Vertex AI, and local/mock modes.
"""
from ai.models import ModelProvider, get_model_provider
from ai.embeddings import EmbeddingProvider, get_embedding_provider
from ai.semantic_search import SemanticSearchProvider
from ai.scoring import ScoringProvider
from ai.summarization import SummarizationProvider
from ai.insights import InsightsProvider

__all__ = [
    "ModelProvider",
    "get_model_provider",
    "EmbeddingProvider",
    "get_embedding_provider",
    "SemanticSearchProvider",
    "ScoringProvider",
    "SummarizationProvider",
    "InsightsProvider",
]
