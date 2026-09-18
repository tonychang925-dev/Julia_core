"""Bounded Anthropic Web Search provider for Research acquisition.

Claude is a subordinate Research worker. It neither selects Julia capabilities
nor produces Julia's final judgment.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from julia_core.capability.models import (
    ProviderExecutionOutcome,
    SideEffectState,
    ToolResultStatus,
)


DEFAULT_CLAUDE_MODEL = "claude-sonnet-5"
PROVIDER_IDENTITY = "anthropic-web-search"
WEB_SEARCH_TOOL_TYPE = "web_search_20250305"


@dataclass(eq=False, repr=False)
class AnthropicWebResearchProvider:
    """Execute one bounded direct Web Search request per capability call."""

    client: Any
    model: str

    async def health(self) -> tuple[bool, str]:
        return True, f"{PROVIDER_IDENTITY} bound; model={self.model}"

    async def execute(self, request) -> ProviderExecutionOutcome:
        query = request.arguments.get("query")
        if not isinstance(query, str) or not query.strip():
            return self._failure("research_query_invalid", "query must be a non-empty string")

        response = None
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=(
                    "You are a subordinate research worker. Use the bounded "
                    "Web Search tool. Report only source-cited research facts; "
                    "you do not select tools or make the user-facing final judgment."
                ),
                messages=[{"role": "user", "content": query}],
                tools=[
                    {
                        "type": WEB_SEARCH_TOOL_TYPE,
                        "name": "web_search",
                        "max_uses": 1,
                    }
                ],
            )
        except Exception as exc:
            return self._failure(
                "anthropic_web_search_request_failed",
                self._safe_exception_message(exc),
            )

        return self._outcome_from_response(query, response)

    async def close(self) -> None:
        close = getattr(self.client, "close", None)
        if callable(close):
            result = close()
            if hasattr(result, "__await__"):
                await result

    def _failure(
        self,
        code: str,
        message: str,
        *,
        provider_error_codes: list[str] | None = None,
    ) -> ProviderExecutionOutcome:
        error = {
            "code": code,
            "message": message,
            "provider": PROVIDER_IDENTITY,
            "model": self.model,
        }
        if provider_error_codes is not None:
            error["provider_error_codes"] = provider_error_codes
        return ProviderExecutionOutcome(
            status=ToolResultStatus.ERROR,
            structured_output={},
            error=error,
            side_effect_state=SideEffectState.NONE,
        )

    @staticmethod
    def _safe_exception_message(exc: Exception) -> str:
        message = str(exc)
        credential = os.environ.get("ANTHROPIC_API_KEY", "")
        if credential:
            message = message.replace(credential, "[redacted]")
        return message or exc.__class__.__name__

    def _outcome_from_response(
        self,
        query: str,
        response: Any,
    ) -> ProviderExecutionOutcome:
        content = self._items(self._field(response, "content"))
        sources = self._source_registry(content)
        findings = self._cited_findings(content, sources)
        search_request_count = sum(
            1
            for block in content
            if self._field(block, "type") == "server_tool_use"
            and self._field(block, "name") == "web_search"
        )
        search_errors = self._search_errors(content)
        provider_error_codes = self._search_error_codes(content)
        pause = (
            self._field(response, "stop_reason") == "pause_turn"
            or any(self._field(block, "type") == "pause_turn" for block in content)
        )

        if not findings or not sources or search_request_count != 1:
            if search_errors:
                return self._failure(
                    "anthropic_web_search_tool_error",
                    "Anthropic Web Search reported a provider search error",
                    provider_error_codes=provider_error_codes,
                )
            reason = "pause_turn" if pause else "no_source_bearing_search_result"
            return self._failure(
                f"anthropic_web_search_{reason}",
                f"Anthropic Web Search produced no source-bearing findings ({reason})",
            )

        limitations = [
            "Claude Web Search was limited to one direct search request.",
            "Findings are provider-side observations, not Julia's final judgment.",
        ]
        if search_errors:
            limitations.extend(search_errors)
        if pause:
            limitations.append("Anthropic returned pause_turn; no continuation request was made.")

        structured_output = {
            "query": query,
            "findings": findings,
            "sources": list(sources.values()),
            "limitations": limitations,
            "provider": PROVIDER_IDENTITY,
            "model": self.model,
            "provider_request_id": self._optional_str(self._field(response, "id")),
            "produced_at": datetime.now(timezone.utc).isoformat(),
            "search_request_count": search_request_count,
        }
        if search_errors:
            structured_output["provider_error_codes"] = provider_error_codes
        usage = self._field(response, "usage")
        if isinstance(usage, dict):
            structured_output["usage"] = dict(usage)

        return ProviderExecutionOutcome(
            status=ToolResultStatus.PARTIAL if search_errors or pause else ToolResultStatus.SUCCESS,
            structured_output=structured_output,
            side_effect_state=SideEffectState.NONE,
        )

    @staticmethod
    def _field(value: Any, name: str) -> Any:
        if isinstance(value, dict):
            return value.get(name)
        return getattr(value, name, None)

    @classmethod
    def _items(cls, value: Any) -> list[Any]:
        if not isinstance(value, (list, tuple)):
            return []
        return list(value)

    @classmethod
    def _content_items(cls, value: Any) -> list[Any]:
        if isinstance(value, (list, tuple)):
            return list(value)
        if value is None:
            return []
        return [value]

    @classmethod
    def _source_registry(cls, content: list[Any]) -> dict[str, dict[str, Any]]:
        registry: dict[str, dict[str, Any]] = {}

        def admit(source: dict[str, Any]) -> None:
            url = source.get("url")
            if not isinstance(url, str) or not url.strip():
                return
            url = url.strip()
            if not url.startswith(("http://", "https://")):
                return
            existing = registry.setdefault(url, {"url": url})
            for key in ("title", "page_age", "published_at"):
                value = cls._optional_str(source.get(key))
                if value is not None:
                    existing[key] = value

        for block in content:
            block_type = cls._field(block, "type")
            if block_type == "web_search_tool_result":
                for item in cls._content_items(cls._field(block, "content")):
                    item_type = cls._field(item, "type")
                    if item_type in {"web_search_result", "web_search_result_error"}:
                        admit(cls._mapping(item))
            elif block_type == "text":
                for citation in cls._items(cls._field(block, "citations")):
                    admit(cls._mapping(citation))
        return registry

    @classmethod
    def _cited_findings(
        cls,
        content: list[Any],
        sources: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        for block in content:
            if cls._field(block, "type") != "text":
                continue
            statement = cls._optional_str(cls._field(block, "text"))
            if statement is None:
                continue
            refs = []
            for citation in cls._items(cls._field(block, "citations")):
                url = cls._optional_str(cls._field(citation, "url"))
                if url is not None and url in sources and url not in refs:
                    refs.append(url)
            if refs:
                findings.append({"statement": statement, "source_refs": refs})
        return findings

    @classmethod
    def _search_errors(cls, content: list[Any]) -> list[str]:
        errors: list[str] = []
        for block in content:
            block_type = cls._field(block, "type")
            if block_type == "web_search_tool_result_error":
                errors.append(cls._error_text(block))
            elif block_type == "web_search_tool_result":
                for item in cls._content_items(cls._field(block, "content")):
                    if cls._field(item, "type") in {
                        "web_search_tool_result_error",
                        "web_search_result_error",
                    }:
                        errors.append(cls._error_text(item))
        return list(dict.fromkeys(errors))

    @classmethod
    def _search_error_codes(cls, content: list[Any]) -> list[str]:
        codes: list[str] = []

        def admit(value: Any) -> None:
            code = cls._optional_str(cls._field(value, "error_code"))
            if code is None:
                error = cls._field(value, "error")
                if isinstance(error, dict):
                    code = cls._optional_str(error.get("error_code"))
            if code is not None and code not in codes:
                codes.append(code)

        for block in content:
            block_type = cls._field(block, "type")
            if block_type == "web_search_tool_result_error":
                admit(block)
            elif block_type == "web_search_tool_result":
                for item in cls._content_items(cls._field(block, "content")):
                    if cls._field(item, "type") in {
                        "web_search_tool_result_error",
                        "web_search_result_error",
                    }:
                        admit(item)
        return codes

    @classmethod
    def _error_text(cls, value: Any) -> str:
        error = cls._field(value, "error")
        if isinstance(error, dict):
            message = cls._optional_str(error.get("message")) or str(error)
        else:
            message = cls._optional_str(error) or cls._optional_str(cls._field(value, "message"))
        error_code = cls._optional_str(cls._field(value, "error_code"))
        if error_code and (not message or error_code not in message):
            message = f"{message}; error_code={error_code}" if message else error_code
        return f"web_search_tool_result_error: {message or 'unknown search error'}"

    @classmethod
    def _mapping(cls, value: Any) -> dict[str, Any]:
        return {
            key: cls._field(value, key)
            for key in ("url", "title", "page_age", "published_at")
            if cls._field(value, key) is not None
        }

    @staticmethod
    def _optional_str(value: Any) -> str | None:
        return value.strip() if isinstance(value, str) and value.strip() else None


@dataclass(frozen=True)
class AnthropicWebResearchProviderFactory:
    """Configure the official SDK without exposing credential material."""

    @staticmethod
    def from_environment() -> AnthropicWebResearchProvider | None:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if not api_key:
            return None
        import anthropic

        model = os.environ.get("JULIA_RESEARCH_CLAUDE_MODEL", "").strip() or DEFAULT_CLAUDE_MODEL
        return AnthropicWebResearchProvider(
            client=anthropic.AsyncAnthropic(api_key=api_key, max_retries=0),
            model=model,
        )


__all__ = [
    "AnthropicWebResearchProvider",
    "AnthropicWebResearchProviderFactory",
    "DEFAULT_CLAUDE_MODEL",
    "PROVIDER_IDENTITY",
]
