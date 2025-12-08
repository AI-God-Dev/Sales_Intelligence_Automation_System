"""
Unified Embedding Provider Interface
Abstracts embedding generation across OpenAI, Vertex AI, and local/mock modes.
"""
import os
import logging
import numpy as np
from typing import List, Optional
from abc import ABC, abstractmethod
import warnings

logger = logging.getLogger(__name__)

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning, module="google.cloud.aiplatform")
warnings.filterwarnings("ignore", message=".*pkg_resources.*deprecated.*")

# Conditional imports
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from google.cloud import aiplatform
    from vertexai.language_models import TextEmbeddingModel
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""
    
    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        pass
    
    @abstractmethod
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass
    
    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Return the dimensionality of embeddings."""
        pass


class MockEmbeddingProvider(EmbeddingProvider):
    """Mock embedding provider for testing and local development."""
    
    def __init__(self, dimensions: int = 768):
        self._dimensions = dimensions
        # Use deterministic seed for reproducible mock embeddings
        np.random.seed(42)
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate deterministic mock embedding based on text hash."""
        if not text or not text.strip():
            return [0.0] * self._dimensions
        
        # Create deterministic embedding based on text content
        hash_val = hash(text) % (2**31)
        np.random.seed(hash_val)
        embedding = np.random.normal(0, 0.1, self._dimensions).tolist()
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = (np.array(embedding) / norm).tolist()
        return embedding
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Generate mock embeddings for batch."""
        return [self.generate_embedding(text) for text in texts]
    
    @property
    def dimensions(self) -> int:
        return self._dimensions


class LocalEmbeddingProvider(EmbeddingProvider):
    """Local embedding provider using numpy (for LOCAL_MODE)."""
    
    def __init__(self, dimensions: int = 768):
        self._dimensions = dimensions
        np.random.seed(42)
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate local embedding using simple hash-based approach."""
        if not text or not text.strip():
            return [0.0] * self._dimensions
        
        # Simple hash-based embedding (deterministic)
        hash_val = hash(text) % (2**31)
        np.random.seed(hash_val)
        embedding = np.random.normal(0, 0.1, self._dimensions).tolist()
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = (np.array(embedding) / norm).tolist()
        return embedding
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Generate local embeddings for batch."""
        return [self.generate_embedding(text) for text in texts]
    
    @property
    def dimensions(self) -> int:
        return self._dimensions


class VertexAIEmbeddingProvider(EmbeddingProvider):
    """Vertex AI embedding provider."""
    
    def __init__(self, project_id: str, region: str, model_name: str = "textembedding-gecko@001"):
        if not VERTEX_AI_AVAILABLE:
            raise ImportError("vertexai package not installed. Install with: pip install google-cloud-aiplatform")
        
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning)
                warnings.filterwarnings("ignore", message=".*pkg_resources.*")
                aiplatform.init(project=project_id, location=region)
            
            self.model = TextEmbeddingModel.from_pretrained(model_name)
            self.model_name = model_name
            # Vertex AI embeddings are typically 768 dimensions
            self._dimensions = 768
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI embeddings: {e}")
            raise ValueError(f"Vertex AI initialization failed: {e}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Vertex AI."""
        if not text or not text.strip():
            return []
        
        try:
            # Limit text length
            text = text[:8000]
            embeddings = self.model.get_embeddings([text])
            
            if embeddings and len(embeddings) > 0:
                emb = embeddings[0]
                if hasattr(emb, 'values'):
                    return emb.values
                elif isinstance(emb, list):
                    return emb
                else:
                    return list(emb)
            return []
        except Exception as e:
            logger.error(f"Error generating Vertex AI embedding: {e}", exc_info=True)
            return []
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Generate embeddings for batch using Vertex AI."""
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                # Limit text length
                batch_texts = [t[:8000] for t in batch]
                embeddings = self.model.get_embeddings(batch_texts)
                
                batch_embeddings = []
                for emb in embeddings:
                    if hasattr(emb, 'values'):
                        batch_embeddings.append(emb.values)
                    elif isinstance(emb, list):
                        batch_embeddings.append(emb)
                    else:
                        batch_embeddings.append(list(emb))
                
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.error(f"Error generating batch embeddings: {e}", exc_info=True)
                # Add empty embeddings for failed batch
                all_embeddings.extend([[]] * len(batch))
        
        return all_embeddings
    
    @property
    def dimensions(self) -> int:
        return self._dimensions


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider."""
    
    def __init__(self, api_key: str, model_name: str = "text-embedding-3-small"):
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package not installed. Install with: pip install openai")
        
        if not api_key:
            raise ValueError("OpenAI API key not provided")
        
        self.client = openai.OpenAI(api_key=api_key)
        self.model_name = model_name
        # text-embedding-3-small: 1536, text-embedding-3-large: 3072
        self._dimensions = 3072 if "large" in model_name else 1536
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI."""
        if not text or not text.strip():
            return []
        
        try:
            text = text[:8000]  # Limit text length
            response = self.client.embeddings.create(
                model=self.model_name,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating OpenAI embedding: {e}", exc_info=True)
            return []
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Generate embeddings for batch using OpenAI."""
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                batch_texts = [t[:8000] for t in batch]
                response = self.client.embeddings.create(
                    model=self.model_name,
                    input=batch_texts
                )
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.error(f"Error generating batch embeddings: {e}", exc_info=True)
                # Add empty embeddings for failed batch
                all_embeddings.extend([[]] * len(batch))
        
        return all_embeddings
    
    @property
    def dimensions(self) -> int:
        return self._dimensions


def get_embedding_provider(
    provider: str = None,
    project_id: str = None,
    region: str = None,
    model_name: str = None,
    api_key: str = None
) -> EmbeddingProvider:
    """
    Factory function to get the appropriate embedding provider.
    
    Args:
        provider: 'vertex_ai', 'openai', 'local', or 'mock'
        project_id: GCP project ID (required for Vertex AI)
        region: GCP region (required for Vertex AI)
        model_name: Model name to use
        api_key: API key (required for OpenAI)
    
    Returns:
        EmbeddingProvider instance
    """
    # Check for MOCK_MODE or LOCAL_MODE first
    mock_mode = os.getenv("MOCK_MODE", "0").strip().lower() in ("1", "true", "yes")
    local_mode = os.getenv("LOCAL_MODE", "0").strip().lower() in ("1", "true", "yes")
    
    if mock_mode or local_mode:
        logger.info(f"{'MOCK_MODE' if mock_mode else 'LOCAL_MODE'} enabled - using {'Mock' if mock_mode else 'Local'}EmbeddingProvider")
        return MockEmbeddingProvider() if mock_mode else LocalEmbeddingProvider()
    
    # Get provider from environment if not specified
    if not provider:
        provider = os.getenv("EMBEDDING_PROVIDER", "vertex_ai").strip().lower()
    
    if not model_name:
        model_name = os.getenv("EMBEDDING_MODEL", "textembedding-gecko@001").strip()
    
    if provider == "mock":
        return MockEmbeddingProvider()
    elif provider == "local":
        return LocalEmbeddingProvider()
    elif provider == "vertex_ai":
        if not project_id:
            project_id = os.getenv("GCP_PROJECT_ID", "").strip()
        if not region:
            region = os.getenv("GCP_REGION", "us-central1").strip()
        if not project_id:
            raise ValueError("GCP_PROJECT_ID required for Vertex AI provider")
        return VertexAIEmbeddingProvider(project_id, region, model_name)
    elif provider == "openai":
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise ValueError("OPENAI_API_KEY required for OpenAI provider")
        return OpenAIEmbeddingProvider(api_key, model_name)
    else:
        raise ValueError(f"Unsupported provider: {provider}. Use 'vertex_ai', 'openai', 'local', or 'mock'")
