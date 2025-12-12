"""
Unified Model Provider Interface
Abstracts LLM calls using Vertex AI only (with mock mode for testing).
"""
import os
import logging
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
import warnings

logger = logging.getLogger(__name__)

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning, module="google.cloud.aiplatform")
warnings.filterwarnings("ignore", message=".*pkg_resources.*deprecated.*")

# Vertex AI imports
try:
    from google.cloud import aiplatform
    from vertexai.generative_models import GenerativeModel
    from vertexai import init as vertex_init
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False


class ModelProvider(ABC):
    """Abstract base class for model providers."""
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        """Generate text from prompt."""
        pass
    
    @abstractmethod
    def generate_stream(self, prompt: str, system_prompt: str = "", **kwargs):
        """Generate text stream from prompt."""
        pass


class MockModelProvider(ModelProvider):
    """Mock model provider for testing and local development.
    
    Simulates Vertex AI Gemini behavior for MOCK_MODE.
    Returns deterministic responses based on prompt content.
    """
    
    def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        """Return mock response simulating Vertex AI Gemini output."""
        # Simulate Vertex AI JSON output for scoring
        if "score" in prompt.lower() or "scoring" in prompt.lower() or "priority_score" in prompt.lower():
            return """{
  "priority_score": 75,
  "budget_likelihood": 60,
  "engagement_score": 80,
  "reasoning": "Mock reasoning: Account shows moderate engagement with recent email activity. Simulated Vertex AI Gemini response.",
  "recommended_action": "Follow up with pricing discussion",
  "key_signals": ["Recent email exchange", "Budget discussion mentioned"]
}"""
        # Simulate Vertex AI summary output
        elif "summary" in prompt.lower() or "summarize" in prompt.lower():
            return "Mock summary: This is a placeholder summary generated in MOCK_MODE, simulating Vertex AI Gemini output."
        # Simulate Vertex AI insight output
        elif "insight" in prompt.lower() or "analyze" in prompt.lower():
            return "Mock insight: Account shows positive engagement signals. Simulated Vertex AI Gemini analysis."
        # Simulate Vertex AI SQL generation
        elif "sql" in prompt.lower() or "query" in prompt.lower() or "SELECT" in prompt.upper():
            return "SELECT * FROM `{project_id}.{dataset_id}.gmail_messages` LIMIT 10"
        # Default mock response
        else:
            return "Mock response: This is a placeholder response generated in MOCK_MODE, simulating Vertex AI Gemini behavior."
    
    def generate_stream(self, prompt: str, system_prompt: str = "", **kwargs):
        """Return mock stream."""
        response = self.generate(prompt, system_prompt, **kwargs)
        for word in response.split():
            yield word + " "


class VertexAIModelProvider(ModelProvider):
    """Vertex AI (Gemini) model provider - THE ONLY PERMITTED AI ENGINE."""
    
    def __init__(self, project_id: str, region: str, model_name: str = "gemini-1.5-pro-002"):
        if not VERTEX_AI_AVAILABLE:
            raise ImportError("vertexai package not installed. Install with: pip install google-cloud-aiplatform")
        
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning)
                warnings.filterwarnings("ignore", message=".*pkg_resources.*")
                # Initialize Vertex AI with Application Default Credentials (ADC)
                vertex_init(project=project_id, location=region)
                aiplatform.init(project=project_id, location=region)
            
            self.model = GenerativeModel(model_name)
            self.model_name = model_name
            self.project_id = project_id
            self.region = region
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")
            raise ValueError(f"Vertex AI initialization failed: {e}")
    
    def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        """Generate text using Vertex AI Gemini models."""
        try:
            # Combine system prompt and user prompt
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            
            # Handle generation config
            from vertexai.generative_models import GenerationConfig
            generation_config = None
            
            config_params = {}
            if "max_tokens" in kwargs:
                config_params["max_output_tokens"] = kwargs["max_tokens"]
            if "temperature" in kwargs:
                config_params["temperature"] = kwargs.get("temperature", 0.7)
            
            # Handle response_schema for structured JSON output (Gemini feature)
            if "response_schema" in kwargs:
                config_params["response_schema"] = kwargs["response_schema"]
            
            if config_params:
                generation_config = GenerationConfig(**config_params)
            
            # Generate content
            if generation_config:
                response = self.model.generate_content(
                    full_prompt,
                    generation_config=generation_config
                )
            else:
                response = self.model.generate_content(full_prompt)
            
            # Handle Vertex AI response format
            if hasattr(response, 'text'):
                return response.text
            elif hasattr(response, 'candidates') and response.candidates:
                if hasattr(response.candidates[0], 'content') and response.candidates[0].content.parts:
                    return response.candidates[0].content.parts[0].text
            else:
                raise ValueError(f"Unexpected Vertex AI response format: {response}")
        except Exception as e:
            logger.error(f"Error calling Vertex AI: {e}", exc_info=True)
            raise
    
    def generate_stream(self, prompt: str, system_prompt: str = "", **kwargs):
        """Generate streaming text using Vertex AI."""
        try:
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = self.model.generate_content(full_prompt, stream=True)
            
            for chunk in response:
                if hasattr(chunk, 'text'):
                    yield chunk.text
                elif hasattr(chunk, 'candidates') and chunk.candidates:
                    yield chunk.candidates[0].content.parts[0].text
        except Exception as e:
            logger.error(f"Error streaming from Vertex AI: {e}", exc_info=True)
            raise




def get_model_provider(
    provider: str = None,
    project_id: str = None,
    region: str = None,
    model_name: str = None,
    api_key: str = None  # Deprecated - kept for backward compatibility but ignored
) -> ModelProvider:
    """
    Factory function to get the appropriate model provider.
    
    ONLY VERTEX AI IS SUPPORTED. OpenAI and Anthropic have been removed.
    
    Args:
        provider: 'vertex_ai' or 'mock' (default: 'vertex_ai')
        project_id: GCP project ID (required for Vertex AI, uses ADC for auth)
        region: GCP region (required for Vertex AI, default: 'us-central1')
        model_name: Model name to use (default: 'gemini-1.5-pro')
        api_key: DEPRECATED - ignored (Vertex AI uses Application Default Credentials)
    
    Returns:
        ModelProvider instance (VertexAIModelProvider or MockModelProvider)
    """
    # Check for MOCK_MODE first
    mock_mode = os.getenv("MOCK_MODE", "0").strip().lower() in ("1", "true", "yes")
    if mock_mode:
        logger.info("MOCK_MODE enabled - using MockModelProvider")
        return MockModelProvider()
    
    # Get provider from environment if not specified
    if not provider:
        provider = os.getenv("LLM_PROVIDER", "vertex_ai").strip().lower()
    
    # Force vertex_ai if anything else is specified (except mock)
    if provider not in ("vertex_ai", "mock"):
        logger.warning(f"Provider '{provider}' is not supported. Only 'vertex_ai' and 'mock' are allowed. Using 'vertex_ai'.")
        provider = "vertex_ai"
    
    if not model_name:
        model_name = os.getenv("LLM_MODEL", "gemini-1.5-pro-002").strip()
    
    if provider == "mock":
        return MockModelProvider()
    elif provider == "vertex_ai":
        if not project_id:
            project_id = os.getenv("GCP_PROJECT_ID", "").strip()
        if not region:
            region = os.getenv("GCP_REGION", "us-central1").strip()
        if not project_id:
            raise ValueError("GCP_PROJECT_ID required for Vertex AI provider. Vertex AI uses Application Default Credentials (ADC) for authentication - no API key needed.")
        return VertexAIModelProvider(project_id, region, model_name)
    else:
        raise ValueError(f"Unsupported provider: {provider}. Only 'vertex_ai' and 'mock' are supported.")
