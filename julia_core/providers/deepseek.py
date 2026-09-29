"""Core-owned transport-only DeepSeek cognition provider."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


_MISSING = object()


class DeepSeekCognitionProviderError(RuntimeError):
    """DeepSeek transport failed; no substitute response is permitted."""


class DeepSeekCognitionProvider:
    """Send exact Core-prepared messages to DeepSeek without semantic edits."""

    provider_id = "core-deepseek-v1"
    provider_name = "deepseek"
    endpoint = "https://api.deepseek.com/v1/chat/completions"

    def __init__(self) -> None:
        self._api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if not self._api_key:
            raise DeepSeekCognitionProviderError(
                "DEEPSEEK_API_KEY is not configured; DeepSeek is unavailable"
            )

    def chat(self, messages: list[dict], *, cognitive_mode: str = "") -> str:
        del cognitive_mode
        exact_messages = self._exact_messages(messages)
        payload = json.dumps(
            {
                "model": "deepseek-chat",
                "messages": exact_messages,
                "stream": False,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        request = urllib.request.Request(self.endpoint, data=payload, method="POST")
        request.add_header("Authorization", f"Bearer {self._api_key}")
        request.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                raw_response = response.read()
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise DeepSeekCognitionProviderError(
                "DeepSeek cognition transport failed"
            ) from error
        return self._extract_content(raw_response)

    @staticmethod
    def _exact_messages(messages: list[dict]) -> list[dict[str, str]]:
        if type(messages) is not list:
            raise TypeError("DeepSeek transport requires an exact message list")
        copied: list[dict[str, str]] = []
        for message in messages:
            if type(message) is not dict:
                raise TypeError("DeepSeek transport message shape is inexact")
            role = message["role"]
            content = message["content"]
            if type(role) is not str or type(content) is not str:
                raise TypeError("DeepSeek transport message fields are inexact")
            copied.append({"role": role, "content": content})
        return copied

    @staticmethod
    def _extract_content(raw_response: bytes) -> str:
        try:
            response: Any = json.loads(raw_response)
            choice = response["choices"][0]
            content = choice["message"]["content"]
            finish_reason = choice.get("finish_reason", _MISSING)
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, IndexError, TypeError, AttributeError) as error:
            raise DeepSeekCognitionProviderError(
                "DeepSeek returned a malformed cognition response"
            ) from error
        # Only a completion DeepSeek reports as finished is a cognition
        # response. Truncated, filtered, resource-limited or unknown
        # completions fail closed: no retry, no partial text, no substitute.
        if finish_reason != "stop":
            observed = "<missing>" if finish_reason is _MISSING else repr(finish_reason)
            raise DeepSeekCognitionProviderError(
                f"DeepSeek cognition response incomplete: finish_reason={observed}"
            )
        if type(content) is not str or not content.strip():
            raise DeepSeekCognitionProviderError(
                "DeepSeek returned an empty cognition response"
            )
        return content


__all__ = [
    "DeepSeekCognitionProvider",
    "DeepSeekCognitionProviderError",
]
