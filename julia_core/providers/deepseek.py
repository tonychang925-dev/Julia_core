"""Core-owned transport-only DeepSeek cognition provider."""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any

from .core_cognition import NativeToolInvocation, TextResult


_CANONICAL_TOOL_NAME = re.compile(r"[A-Za-z0-9_.-]+\Z")
_WIRE_TOOL_NAME = re.compile(r"[A-Za-z0-9_-]+\Z")
_MAX_WIRE_TOOL_NAME_LENGTH = 128


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
        raw_response = self._request({
            "model": "deepseek-chat",
            "messages": self._exact_messages(messages),
            "stream": False,
        })
        return self._extract_content(raw_response)

    def chat_with_tools(
        self,
        messages: list[dict],
        available_tools: list[dict],
        *,
        cognitive_mode: str = "",
    ) -> TextResult | NativeToolInvocation:
        del cognitive_mode
        native_tools, advertised_ids = self._project_native_tools(available_tools)
        raw_response = self._request({
            "model": "deepseek-chat",
            "messages": self._exact_messages(messages),
            "tools": native_tools,
            "tool_choice": "auto",
            "stream": False,
        })
        return self._extract_native_result(raw_response, advertised_ids)

    def _request(self, payload: dict[str, Any]) -> bytes:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(self.endpoint, data=body, method="POST")
        request.add_header("Authorization", f"Bearer {self._api_key}")
        request.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise DeepSeekCognitionProviderError(
                "DeepSeek cognition transport failed"
            ) from error

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

    @classmethod
    def _project_native_tools(
        cls,
        available_tools: list[dict],
    ) -> tuple[list[dict[str, Any]], tuple[str, ...]]:
        if type(available_tools) is not list or not available_tools:
            raise DeepSeekCognitionProviderError(
                "native tool invocation requires a non-empty advertised tool catalog"
            )
        projected: list[dict[str, Any]] = []
        advertised_ids: list[str] = []
        seen_wire_names: set[str] = set()
        for tool in available_tools:
            if type(tool) is not dict or set(tool) != {
                "capability_id",
                "description",
                "input_schema",
            }:
                raise DeepSeekCognitionProviderError(
                    "advertised native tool definition shape is inexact"
                )
            capability_id = tool["capability_id"]
            description = tool["description"]
            input_schema = tool["input_schema"]
            if type(capability_id) is not str or not capability_id:
                raise DeepSeekCognitionProviderError(
                    "advertised capability_id is invalid"
                )
            if type(description) is not str or type(input_schema) is not dict:
                raise DeepSeekCognitionProviderError(
                    "advertised native tool metadata is invalid"
                )
            if capability_id in advertised_ids:
                raise DeepSeekCognitionProviderError(
                    "duplicate advertised capability_id"
                )
            wire_name = cls._encode_tool_name(capability_id)
            if wire_name in seen_wire_names:
                raise DeepSeekCognitionProviderError(
                    "native tool wire-name collision"
                )
            properties: dict[str, dict[str, str]] = {}
            for argument_name, argument_description in input_schema.items():
                if (
                    type(argument_name) is not str
                    or not argument_name
                    or type(argument_description) is not str
                ):
                    raise DeepSeekCognitionProviderError(
                        "advertised input_schema is invalid"
                    )
                properties[argument_name] = {
                    "description": argument_description,
                }
            projected.append({
                "type": "function",
                "function": {
                    "name": wire_name,
                    "description": description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                    },
                },
            })
            advertised_ids.append(capability_id)
            seen_wire_names.add(wire_name)
        return projected, tuple(advertised_ids)

    @staticmethod
    def _encode_tool_name(capability_id: str) -> str:
        if (
            type(capability_id) is not str
            or _CANONICAL_TOOL_NAME.fullmatch(capability_id) is None
        ):
            raise DeepSeekCognitionProviderError(
                "canonical capability_id is not transport-safe"
            )
        encoded = "".join(
            "_5F_" if char == "_" else "_2E_" if char == "." else char
            for char in capability_id
        )
        if (
            len(encoded) > _MAX_WIRE_TOOL_NAME_LENGTH
            or _WIRE_TOOL_NAME.fullmatch(encoded) is None
        ):
            raise DeepSeekCognitionProviderError(
                "encoded native tool name violates provider constraints"
            )
        return encoded

    @classmethod
    def _decode_tool_name(
        cls,
        wire_name: str,
        advertised_ids: tuple[str, ...],
    ) -> str:
        if (
            type(wire_name) is not str
            or not wire_name
            or len(wire_name) > _MAX_WIRE_TOOL_NAME_LENGTH
            or _WIRE_TOOL_NAME.fullmatch(wire_name) is None
        ):
            raise DeepSeekCognitionProviderError(
                "provider returned an invalid native tool name"
            )
        decoded: list[str] = []
        index = 0
        while index < len(wire_name):
            if wire_name[index] != "_":
                decoded.append(wire_name[index])
                index += 1
                continue
            token = wire_name[index:index + 4]
            if token == "_5F_":
                decoded.append("_")
            elif token == "_2E_":
                decoded.append(".")
            else:
                raise DeepSeekCognitionProviderError(
                    "provider returned a malformed native tool-name escape"
                )
            index += 4
        capability_id = "".join(decoded)
        if (
            capability_id not in advertised_ids
            or cls._encode_tool_name(capability_id) != wire_name
        ):
            raise DeepSeekCognitionProviderError(
                "provider returned an unadvertised native tool name"
            )
        return capability_id

    @classmethod
    def _extract_native_result(
        cls,
        raw_response: bytes,
        advertised_ids: tuple[str, ...],
    ) -> TextResult | NativeToolInvocation:
        try:
            response: Any = json.loads(raw_response)
            choice = response["choices"][0]
            message = choice["message"]
            finish_reason = choice.get("finish_reason")
            content = message.get("content")
            tool_calls = message.get("tool_calls")
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
            KeyError,
            IndexError,
            TypeError,
        ) as error:
            raise DeepSeekCognitionProviderError(
                "DeepSeek returned a malformed native cognition response"
            ) from error

        if tool_calls is not None and type(tool_calls) is not list:
            raise DeepSeekCognitionProviderError(
                "DeepSeek returned an invalid native tool_calls shape"
            )
        if tool_calls:
            if finish_reason != "tool_calls" or len(tool_calls) != 1:
                raise DeepSeekCognitionProviderError(
                    "DeepSeek returned an inconsistent native tool-call response"
                )
            if content is not None:
                if type(content) is not str:
                    raise DeepSeekCognitionProviderError(
                        "DeepSeek returned invalid mixed native content"
                    )
            call = tool_calls[0]
            if (
                type(call) is not dict
                or call.get("type") != "function"
                or type(call.get("function")) is not dict
            ):
                raise DeepSeekCognitionProviderError(
                    "DeepSeek returned a malformed native tool call"
                )
            function = call["function"]
            wire_name = function.get("name")
            raw_arguments = function.get("arguments")
            if type(wire_name) is not str or type(raw_arguments) is not str:
                raise DeepSeekCognitionProviderError(
                    "DeepSeek returned malformed native tool arguments"
                )
            try:
                arguments = json.loads(raw_arguments)
            except json.JSONDecodeError as error:
                raise DeepSeekCognitionProviderError(
                    "DeepSeek returned malformed native tool arguments"
                ) from error
            if type(arguments) is not dict:
                raise DeepSeekCognitionProviderError(
                    "DeepSeek native tool arguments must be an object"
                )
            return NativeToolInvocation(
                capability_id=cls._decode_tool_name(wire_name, advertised_ids),
                arguments=arguments,
            )

        if finish_reason == "tool_calls":
            raise DeepSeekCognitionProviderError(
                "DeepSeek declared a native tool call without tool_calls"
            )
        if type(content) is not str or not content.strip():
            raise DeepSeekCognitionProviderError(
                "DeepSeek returned an empty native cognition response"
            )
        return TextResult(content=content)

    @staticmethod
    def _extract_content(raw_response: bytes) -> str:
        try:
            response: Any = json.loads(raw_response)
            content = response["choices"][0]["message"]["content"]
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, IndexError, TypeError) as error:
            raise DeepSeekCognitionProviderError(
                "DeepSeek returned a malformed cognition response"
            ) from error
        if type(content) is not str or not content.strip():
            raise DeepSeekCognitionProviderError(
                "DeepSeek returned an empty cognition response"
            )
        return content


__all__ = [
    "DeepSeekCognitionProvider",
    "DeepSeekCognitionProviderError",
]
