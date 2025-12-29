"""
Scoring provider abstraction.

Important:
- DOES NOT pass response_schema to Vertex GenerationConfig (avoids protobuf Schema errors)
- Supports call sites that pass bq_client=... into get_scoring_provider()
- Uses safe date/datetime serialization for JSON encoding

Public exports:
- ScoringProvider (Protocol)
- VertexAIScoringProvider (implementation)
- get_scoring_provider (factory)
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, Optional, Protocol

from ai.models import ModelProvider, get_model_provider

logger = logging.getLogger(__name__)


def _json_serializer(obj: Any) -> str:
    """
    Custom JSON serializer for objects that aren't serializable by default.
    Handles date, datetime, and other common types.
    
    Args:
        obj: Object to serialize
        
    Returns:
        String representation of the object
    """
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if hasattr(obj, '__dict__'):
        return str(obj)
    return str(obj)


class ScoringProvider(Protocol):
    """Interface expected by AccountScorer / scoring pipeline."""

    def score_account(self, account_id: str, account_data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


def _safe_json_loads(text: str) -> Dict[str, Any]:
    """
    Best-effort JSON parsing:
    - Strips common Markdown fences
    - Attempts strict JSON parse
    - Falls back to minimal structured payload on failure
    """
    if not isinstance(text, str):
        return {"raw": str(text)}

    cleaned = text.strip()

    # Remove ```json ... ``` or ``` ... ```
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        # If it started with json\n, remove the first line
        cleaned = cleaned.replace("json\n", "", 1).strip()

    # Try strict JSON
    try:
        obj = json.loads(cleaned)
        if isinstance(obj, dict):
            return obj
        return {"value": obj}
    except Exception:
        # Try extracting first {...} block
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                obj = json.loads(cleaned[start : end + 1])
                if isinstance(obj, dict):
                    return obj
                return {"value": obj}
            except Exception:
                pass

    return {"raw": text, "parse_error": True}


@dataclass
class VertexAIScoringProvider:
    """
    Scoring provider that uses an LLM (Vertex/Gemini via ModelProvider) to produce scoring JSON.
    
    bq_client is accepted for compatibility with current wiring but is not required here.
    If later you want this provider to query BigQuery directly, you can use self.bq_client.
    """

    model_provider: ModelProvider
    bq_client: Any = None  # optional, for compatibility / future use

    def score_account(self, account_id: str, account_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._build_prompt(account_id, account_data)

        # Request JSON output without passing response_schema (Vertex SDK schema is not full JSON Schema).
        response_text = self.model_provider.generate(
            prompt,
            want_json=True,
            temperature=0.2,
            max_output_tokens=1200,
        )

        payload = _safe_json_loads(response_text)

        # Normalize minimal expected fields (do not hard-fail if missing)
        payload.setdefault("account_id", account_id)
        
        # Ensure required fields for compatibility with account_scorer.py
        payload.setdefault("priority_score", payload.get("score", 50))
        payload.setdefault("budget_likelihood", 50)
        payload.setdefault("engagement_score", 50)
        payload.setdefault("reasoning", payload.get("recommendation", ""))
        payload.setdefault("recommended_action", "")
        payload.setdefault("key_signals", payload.get("reasons", []))
        
        return payload

    def _build_prompt(self, account_id: str, account_data: Dict[str, Any]) -> str:
        """
        Prompt tuned to force clean JSON. Keep the schema requirements inside the prompt text
        (rather than response_schema) to avoid Vertex Schema protobuf failures.
        
        FIXED: Uses custom JSON serializer to handle date/datetime objects safely.
        """
        # Serialize account_data with safe date handling
        try:
            account_json = json.dumps(account_data, default=_json_serializer, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to serialize account_data for {account_id}: {e}")
            # Fallback: convert to string representation
            account_json = str(account_data)

        return f"""
You are a sales intelligence scoring assistant.

Return ONLY valid JSON (no markdown, no code fences, no commentary).

JSON requirements:
- Must be a single JSON object.
- Use double quotes for all keys/strings.
- Provide these top-level keys:
  - "score" (number 0-100)
  - "tier" (string: "A" | "B" | "C" | "D")
  - "recommendation" (short string)
  - "reasons" (array of 3-6 short strings)
  - "next_steps" (array of 3-6 short strings)
  - "risks" (array of 0-5 short strings)
  - "confidence" (number 0-1)

Context:
account_id: {account_id}
account_data: {account_json}
""".strip()


def get_scoring_provider(
    provider: Optional[str] = None,
    *,
    llm_provider: Optional[str] = None,
    model_provider: Optional[ModelProvider] = None,
    bq_client: Any = None,
    **kwargs: Any,
) -> ScoringProvider:
    """
    Factory that returns a ScoringProvider.
    
    Compatibility:
    - Accepts bq_client=... (previous wiring)
    - Accepts arbitrary **kwargs to avoid breaking older call sites
    
    Provider resolution:
    - provider arg wins
    - else llm_provider
    - else env LLM_PROVIDER
    - default "vertex_ai"
    """
    provider_name = (provider or llm_provider or os.getenv("LLM_PROVIDER") or "vertex_ai").strip().lower()

    if model_provider is None:
        # get_model_provider supports provider=... in our patched ai/models.py
        model_provider = get_model_provider(provider=provider_name)

    if provider_name in ("vertex", "vertex_ai", "vertexai", "google", "gemini"):
        return VertexAIScoringProvider(model_provider=model_provider, bq_client=bq_client)

    # If you later add other scoring providers, branch here.
    raise ValueError(f"Unsupported scoring provider: {provider_name!r}")


__all__ = [
    "ScoringProvider",
    "VertexAIScoringProvider",
    "get_scoring_provider",
]
