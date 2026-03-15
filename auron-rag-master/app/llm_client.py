import json
import re
from abc import ABC, abstractmethod
from typing import Dict, List

import requests
from loguru import logger
from pydantic import BaseModel
from settings import (
    LLM_MAX_TOKENS,
    LLM_TEMPERATURE,
    SKODAGPT_API_KEY,
    SKODAGPT_ENDPOINT,
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
)


class LLMRagResponse(BaseModel):
    text: str
    used_documents: List[str] = []


def _extract_title(text: str) -> str | None:
    """Extract 'Název: ...' from article text (present in the first chunk)."""
    for line in text.splitlines():
        if line.startswith("Název:"):
            return line.split(":", 1)[1].strip()
    return None


def _format_context(documents: List[Dict]) -> str:
    context_parts = []
    for i, doc in enumerate(documents, 1):
        title = _extract_title(doc["text"]) or doc["filename"]
        context_parts.append(
            f"[Document {i}]\n"
            f"Filename: {doc['filename']}\n"
            f"Source: {title}\n"
            f"Relevance: {doc['similarity']:.1%}\n"
            f"Content: {doc['text']}"
        )
    return "\n\n".join(context_parts)


def _parse_llm_json(raw: str) -> LLMRagResponse:
    """Strip markdown fences and parse LLM JSON response."""
    cleaned = re.sub(r"^```json\s*", "", raw.strip())
    cleaned = re.sub(r"^```\s*", "", cleaned)
    cleaned = re.sub(r"```\s*$", "", cleaned).strip()
    data = json.loads(cleaned)
    return LLMRagResponse(**data)


class LLMClient(ABC):
    """Base class for LLM clients."""

    @abstractmethod
    def rag_chat(self, query: str, documents: List[Dict]) -> LLMRagResponse: ...

    @abstractmethod
    def direct_chat(self, messages: List[Dict]) -> str: ...


class SkodaGPTClient(LLMClient):
    """LLM client backed by the SkodaGPT custom REST API."""

    def __init__(self):
        self._url = SKODAGPT_ENDPOINT
        self._headers = {
            "Content-Type": "application/json",
            "Ocp-Apim-Subscription-Key": SKODAGPT_API_KEY,
        }
        logger.info(f"SkodaGPT client initialized (url: {self._url})")

    def _post(self, payload: dict) -> str:
        """Send payload to SkodaGPT API and return response content."""
        try:
            response = requests.post(self._url, headers=self._headers, json=payload)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            error_msg = str(e)
            if SKODAGPT_API_KEY and SKODAGPT_API_KEY in error_msg:
                error_msg = "API authentication error (key hidden for security)"
            logger.error(f"SkodaGPT API error: {error_msg}")
            raise

    def rag_chat(self, query: str, documents: List[Dict]) -> LLMRagResponse:
        """Generate a response grounded in retrieved documents using the system prompt."""
        logger.info(f"RAG chat for: '{query[:50]}...'")
        context = _format_context(documents)
        user_prompt = USER_PROMPT_TEMPLATE.format(context=context, query=query)
        payload = {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": LLM_TEMPERATURE,
            "max_tokens": LLM_MAX_TOKENS,
        }
        raw = self._post(payload)
        logger.info(f"RAG raw response ({len(raw)} chars): {raw[:200]}")
        result = _parse_llm_json(raw)
        logger.info(
            f"RAG parsed: text={len(result.text)} chars, used_documents={result.used_documents}"
        )
        return result

    def direct_chat(self, messages: List[Dict]) -> str:
        """Send messages directly to the LLM, bypassing RAG context."""
        payload = {
            "messages": messages,
            "temperature": LLM_TEMPERATURE,
            "max_tokens": LLM_MAX_TOKENS,
        }
        return self._post(payload)


_PROVIDERS: Dict[str, type] = {
    "skodagpt": SkodaGPTClient,
}


def create_llm_client(provider: str = "skodagpt") -> LLMClient:
    """Returns an LLMClient for the given provider."""
    if provider not in _PROVIDERS:
        raise ValueError(
            f"Unknown LLM provider '{provider}'. Available: {list(_PROVIDERS)}"
        )
    return _PROVIDERS[provider]()
