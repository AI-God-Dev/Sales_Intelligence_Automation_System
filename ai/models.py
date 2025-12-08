"""
Unified Model Provider Interface
Abstracts LLM calls across OpenAI, Vertex AI, Anthropic, and mock modes.
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

# Conditional imports
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from google.cloud import aiplatform
    from vertexai.generative_models import GenerativeModel
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
    """Mock model provider for testing and local development."""
    
    def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        """Return mock response."""
        if "score" in prompt.lower() or "scoring" in prompt.lower():
            return """{
  "priority_score": 75,
  "budget_likelihood": 60,
  "engagement_score": 80,
  "reasoning": "Mock reasoning: Account shows moderate engagement with recent email activity.",
  "recommended_action": "Follow up with pricing discussion",
  "key_signals": ["Recent email exchange", "Budget discussion mentioned"]
}"""
        elif "summary" in prompt.lower():
            return "Mock summary: This is a placeholder summary generated in MOCK_MODE."
        elif "insight" in prompt.lower():
            return "Mock insight: Account shows positive engagement signals."
        else:
            return "Mock response: This is a placeholder response generated in MOCK_MODE."
    
    def generate_stream(self, prompt: str, system_prompt: str = "", **kwargs):
        """Return mock stream."""
        response = self.generate(prompt, system_prompt, **kwargs)
        for word in response.split():
            yield word + " "


class VertexAIModelProvider(ModelProvider):
    """Vertex AI (Gemini) model provider."""
    
    def __init__(self, project_id: str, region: str, model_name: str = "gemini-pro"):
        if not VERTEX_AI_AVAILABLE:
            raise ImportError("vertexai package not installed. Install with: pip install google-cloud-aiplatform")
        
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning)
                warnings.filterwarnings("ignore", message=".*pkg_resources.*")
                aiplatform.init(project=project_id, location=region)
            
            self.model = GenerativeModel(model_name)
            self.model_name = model_name
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")
            raise ValueError(f"Vertex AI initialization failed: {e}")
    
    def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        """Generate text using Vertex AI."""
        try:
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            
            # Handle max_tokens if provided
            generation_config = {}
            if "max_tokens" in kwargs:
                generation_config["max_output_tokens"] = kwargs["max_tokens"]
            if "temperature" in kwargs:
                generation_config["temperature"] = kwargs["temperature"]
            
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


class OpenAIModelProvider(ModelProvider):
    """OpenAI model provider."""
    
    def __init__(self, api_key: str, model_name: str = "gpt-4"):
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package not installed. Install with: pip install openai")
        
        if not api_key:
            raise ValueError("OpenAI API key not provided")
        
        self.client = openai.OpenAI(api_key=api_key)
        self.model_name = model_name
    
    def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        """Generate text using OpenAI."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=kwargs.get("max_tokens", 2000),
                temperature=kwargs.get("temperature", 0.7)
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling OpenAI: {e}", exc_info=True)
            raise
    
    def generate_stream(self, prompt: str, system_prompt: str = "", **kwargs):
        """Generate streaming text using OpenAI."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=kwargs.get("max_tokens", 2000),
                temperature=kwargs.get("temperature", 0.7),
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Error streaming from OpenAI: {e}", exc_info=True)
            raise


class AnthropicModelProvider(ModelProvider):
    """Anthropic (Claude) model provider."""
    
    def __init__(self, api_key: str, model_name: str = "claude-3-5-sonnet-20241022"):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic package not installed. Install with: pip install anthropic")
        
        if not api_key:
            raise ValueError("Anthropic API key not provided")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model_name = model_name
    
    def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        """Generate text using Anthropic."""
        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=kwargs.get("max_tokens", 2000),
                system=system_prompt if system_prompt else "",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text
        except Exception as e:
            logger.error(f"Error calling Anthropic: {e}", exc_info=True)
            raise
    
    def generate_stream(self, prompt: str, system_prompt: str = "", **kwargs):
        """Generate streaming text using Anthropic."""
        try:
            with self.client.messages.stream(
                model=self.model_name,
                max_tokens=kwargs.get("max_tokens", 2000),
                system=system_prompt if system_prompt else "",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            ) as stream:
                for text in stream.text_stream:
                    yield text
        except Exception as e:
            logger.error(f"Error streaming from Anthropic: {e}", exc_info=True)
            raise


def get_model_provider(
    provider: str = None,
    project_id: str = None,
    region: str = None,
    model_name: str = None,
    api_key: str = None
) -> ModelProvider:
    """
    Factory function to get the appropriate model provider.
    
    Args:
        provider: 'vertex_ai', 'openai', 'anthropic', or 'mock'
        project_id: GCP project ID (required for Vertex AI)
        region: GCP region (required for Vertex AI)
        model_name: Model name to use
        api_key: API key (required for OpenAI/Anthropic)
    
    Returns:
        ModelProvider instance
    """
    # Check for MOCK_MODE first
    mock_mode = os.getenv("MOCK_MODE", "0").strip().lower() in ("1", "true", "yes")
    if mock_mode:
        logger.info("MOCK_MODE enabled - using MockModelProvider")
        return MockModelProvider()
    
    # Get provider from environment if not specified
    if not provider:
        provider = os.getenv("LLM_PROVIDER", "vertex_ai").strip().lower()
    
    if not model_name:
        model_name = os.getenv("LLM_MODEL", "gemini-pro").strip()
    
    if provider == "mock":
        return MockModelProvider()
    elif provider == "vertex_ai":
        if not project_id:
            project_id = os.getenv("GCP_PROJECT_ID", "").strip()
        if not region:
            region = os.getenv("GCP_REGION", "us-central1").strip()
        if not project_id:
            raise ValueError("GCP_PROJECT_ID required for Vertex AI provider")
        return VertexAIModelProvider(project_id, region, model_name)
    elif provider == "openai":
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise ValueError("OPENAI_API_KEY required for OpenAI provider")
        return OpenAIModelProvider(api_key, model_name)
    elif provider == "anthropic":
        if not api_key:
            api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY required for Anthropic provider")
        return AnthropicModelProvider(api_key, model_name)
    else:
        raise ValueError(f"Unsupported provider: {provider}. Use 'vertex_ai', 'openai', 'anthropic', or 'mock'")
