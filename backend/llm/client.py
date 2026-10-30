"""Groq LLM Client"""
import json
import logging
from typing import Any, Dict, List, Optional

from groq import Groq

from backend.config import settings

logger = logging.getLogger(__name__)


class GroqClient:
    """Thin wrapper around the Groq chat completions API"""

    def __init__(self, api_key: str, model: str):
        self.model = model
        self._client = Groq(api_key=api_key) if api_key else None

    def complete_json(self, messages: List[Dict[str, str]], temperature: Optional[float] = None) -> Dict[str, Any]:
        """Send messages to Groq and parse the response as JSON.

        Raises on any failure (missing key, network error, invalid JSON) —
        callers are expected to fall back to rule-based logic.
        """
        if self._client is None:
            raise RuntimeError("GROQ_API_KEY is not configured")

        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature if temperature is not None else settings.GROQ_TEMPERATURE,
            max_tokens=settings.GROQ_MAX_TOKENS,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        return json.loads(content)


groq_client = GroqClient(api_key=settings.GROQ_API_KEY, model=settings.GROQ_MODEL)
