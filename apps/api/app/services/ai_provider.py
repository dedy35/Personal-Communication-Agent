from __future__ import annotations

from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Protocol

import httpx

from app.core.config import get_settings


class AIProvider(Protocol):
    def is_available(self) -> bool: ...

    def generate_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
    ) -> str | None: ...


class OllamaProvider:
    """Local-first Ollama provider with graceful degradation."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout_seconds: float = 1.5,
        availability_ttl_seconds: int = 30,
        enabled: bool = True,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout_seconds
        self._availability_ttl = timedelta(seconds=availability_ttl_seconds)
        self._enabled = enabled

        self._availability_checked_at: datetime | None = None
        self._is_available_cache: bool | None = None

    def is_available(self) -> bool:
        if not self._enabled:
            return False

        now = datetime.now(tz=UTC)
        if (
            self._availability_checked_at is not None
            and self._is_available_cache is not None
            and now - self._availability_checked_at <= self._availability_ttl
        ):
            return self._is_available_cache

        available = self._probe()
        self._availability_checked_at = now
        self._is_available_cache = available
        return available

    def generate_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
    ) -> str | None:
        if not self.is_available():
            return None

        payload = {
            "model": self._model,
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }

        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(f"{self._base_url}/api/generate", json=payload)
                response.raise_for_status()
            data = response.json()
        except Exception:
            self._is_available_cache = False
            self._availability_checked_at = datetime.now(tz=UTC)
            return None

        generated = data.get("response")
        if not isinstance(generated, str):
            return None

        text = generated.strip()
        return text or None

    def _probe(self) -> bool:
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.get(f"{self._base_url}/api/tags")
                response.raise_for_status()
            data = response.json()
        except Exception:
            return False

        models = data.get("models")
        if not isinstance(models, list):
            return False

        normalized = self._model.lower()
        return any(isinstance(item, dict) and str(item.get("name", "")).lower() == normalized for item in models)


@lru_cache(maxsize=1)
def get_default_ai_provider() -> AIProvider:
    settings = get_settings()
    return OllamaProvider(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        timeout_seconds=settings.ollama_timeout_seconds,
        enabled=settings.ollama_enabled,
    )
