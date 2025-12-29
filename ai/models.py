"""
Model provider abstraction layer.

Key behaviors:
- Supports Vertex AI (Gemini) as the default provider.
- If want_json is requested, we set response_mime_type="application/json"
- We DO NOT pass response_schema into GenerationConfig because Vertex SDK Schema is not full JSON Schema
  (passing arbitrary JSON Schema frequently causes protobuf Schema parse errors like "additionalProperties").

Supported kwargs (common):
  - want_json: bool
  - temperature: float
  - max_output_tokens: int
  - top_p: float
  - top_k: int
  - response_schema: (ignored for Vertex; logged)
  - system_instruction / system_prompt: str (best-effort; Vertex)
"""
from __future__ import annotations

import abc
import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol, Union

logger = logging.getLogger(__name__)


class ModelProvider(Protocol):
    """Simple interface expected by the rest of the app."""

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a text response from a prompt."""
        raise NotImplementedError


@dataclass
class VertexAIModelProvider:
    """
    Vertex AI (Gemini) provider.

    Notes:
    - Imports vertexai lazily to avoid import-time failures breaking container startup.
    - Uses response_mime_type="application/json" when want_json is requested.
    - Ignores response_schema to avoid protobuf Schema errors.
    """

    project_id: Optional[str] = None
    region: Optional[str] = None
    model_name: Optional[str] = None

    def __post_init__(self) -> None:
        self.project_id = self.project_id or os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.region = self.region or os.getenv("GCP_REGION") or os.getenv("GOOGLE_CLOUD_REGION") or "us-central1"
        self.model_name = self.model_name or os.getenv("LLM_MODEL") or os.getenv("VERTEX_MODEL") or os.getenv("VERTEX_MODEL_NAME") or "gemini-2.5-pro"

        # Initialize Vertex lazily but at provider init time (still safe).
        try:
            import vertexai  # type: ignore

            vertexai.init(project=self.project_id, location=self.region)
        except Exception as e:
            # Do not raise here; raise only when generating to help container start and show clearer errors.
            logger.warning("Vertex AI init did not complete at provider init time: %s", e)

    def generate(self, prompt: str, **kwargs: Any) -> str:
        try:
            from vertexai.generative_models import (  # type: ignore
                GenerationConfig,
                GenerativeModel,
            )
        except Exception as e:
            raise RuntimeError(f"Vertex AI SDK import failed: {e}") from e

        system_instruction = (
            kwargs.get("system_instruction")
            or kwargs.get("system_prompt")
            or os.getenv("LLM_SYSTEM_INSTRUCTION")
            or None
        )

        temperature = kwargs.get("temperature", float(os.getenv("LLM_TEMPERATURE", "0.2")))
        max_output_tokens = kwargs.get("max_output_tokens", int(os.getenv("LLM_MAX_TOKENS", "1024")))
        top_p = kwargs.get("top_p", float(os.getenv("LLM_TOP_P", "0.95")))
        top_k = kwargs.get("top_k", int(os.getenv("LLM_TOP_K", "40")))

        # If caller asked for JSON OR provided response_schema, prefer JSON mime type.
        want_json = bool(kwargs.get("want_json")) or ("response_schema" in kwargs)

        config_params: Dict[str, Any] = {
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
            "top_p": top_p,
            "top_k": top_k,
        }

        if want_json:
            config_params["response_mime_type"] = "application/json"

        # IMPORTANT: Do NOT pass response_schema into GenerationConfig.
        # Vertex SDK expects a proto Schema, not a full JSON Schema; fields like "additionalProperties" break parsing.
        if "response_schema" in kwargs and kwargs["response_schema"] is not None:
            logger.info(
                "Ignoring response_schema for Vertex AI GenerationConfig to avoid protobuf Schema parse errors."
            )

        generation_config = GenerationConfig(**config_params)

        # Create model (system_instruction is best-effort)
        try:
            if system_instruction:
                model = GenerativeModel(self.model_name, system_instruction=system_instruction)
            else:
                model = GenerativeModel(self.model_name)
        except TypeError:
            # Older SDKs may not accept system_instruction; fall back.
            model = GenerativeModel(self.model_name)

        try:
            resp = model.generate_content(prompt, generation_config=generation_config)
        except Exception as e:
            logger.exception("Error calling Vertex AI generate_content")
            raise

        # Vertex SDK response handling can vary; normalize to string.
        text = getattr(resp, "text", None)
        if isinstance(text, str) and text.strip():
            return text

        # Fallback: attempt to pull text from candidates
        try:
            candidates = getattr(resp, "candidates", None) or []
            if candidates:
                content = getattr(candidates[0], "content", None)
                parts = getattr(content, "parts", None) or []
                if parts:
                    part0 = parts[0]
                    part_text = getattr(part0, "text", None)
                    if isinstance(part_text, str):
                        return part_text
        except Exception:
            pass

        # Last resort
        return str(resp)


@dataclass
class OpenAIModelProvider:
    """
    Optional OpenAI provider (only used if LLM_PROVIDER=openai).
    Implemented defensively so importing does not break if openai is not installed.
    """

    api_key: Optional[str] = None
    model_name: Optional[str] = None

    def __post_init__(self) -> None:
        self.api_key = self.api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = self.model_name or os.getenv("OPENAI_MODEL") or "gpt-4o-mini"

    def generate(self, prompt: str, **kwargs: Any) -> str:
        try:
            from openai import OpenAI  # type: ignore
        except Exception as e:
            raise RuntimeError(f"openai SDK import failed: {e}") from e

        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")

        client = OpenAI(api_key=self.api_key)

        temperature = kwargs.get("temperature", float(os.getenv("LLM_TEMPERATURE", "0.2")))
        max_output_tokens = kwargs.get("max_output_tokens", int(os.getenv("LLM_MAX_TOKENS", "1024")))

        system_instruction = kwargs.get("system_instruction") or kwargs.get("system_prompt")

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        resp = client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_output_tokens,
        )

        return resp.choices[0].message.content or ""


def get_model_provider(
    provider: Optional[str] = None,
    *,
    llm_provider: Optional[str] = None,
    **kwargs: Any,
) -> ModelProvider:
    """
    Factory that returns the configured ModelProvider.

    Backward-compatible argument handling:
      - provider=... (older call sites)
      - llm_provider=... (explicit)
      - env var LLM_PROVIDER (default: vertex_ai)
    """
    provider_name = (
        provider
        or llm_provider
        or kwargs.get("provider_name")
        or os.getenv("LLM_PROVIDER")
        or "vertex_ai"
    )

    provider_name = str(provider_name).strip().lower()

    if provider_name in ("vertex", "vertex_ai", "vertexai", "google", "gemini"):
        return VertexAIModelProvider(
            project_id=kwargs.get("project_id") or os.getenv("GCP_PROJECT_ID"),
            region=kwargs.get("region") or os.getenv("GCP_REGION"),
            model_name=kwargs.get("model_name") or os.getenv("LLM_MODEL") or os.getenv("VERTEX_MODEL") or os.getenv("VERTEX_MODEL_NAME"),
        )

    if provider_name in ("openai",):
        return OpenAIModelProvider(
            api_key=kwargs.get("api_key") or os.getenv("OPENAI_API_KEY"),
            model_name=kwargs.get("model_name") or os.getenv("OPENAI_MODEL"),
        )

    raise ValueError(f"Unsupported LLM provider: {provider_name!r}")


__all__ = [
    "ModelProvider",
    "VertexAIModelProvider",
    "OpenAIModelProvider",
    "get_model_provider",
]
