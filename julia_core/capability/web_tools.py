"""Julia OS v2.3 World Access — Web search + fetch tools.

LLM decides: what to search, when to fetch, how to use results.
Runtime does: HTTP requests. Nothing more.

Principle: capability = Tool exposed to LLM. Never a Runtime decision.
"""

from __future__ import annotations

import json
import os
import urllib.request
import urllib.parse
from typing import Optional


class WebSearchTool:
    """Web search capability. LLM decides when the world has information Julia doesn't."""

    tool_name = "web_search"
    tool_description = "搜索互联网获取最新信息。当你不知道答案或Tony问最新事件时使用。返回搜索结果摘要。"

    @staticmethod
    def search(query: str, max_results: int = 5) -> str:
        """Search the web. Uses DuckDuckGo (no API key)."""
        try:
            url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1"
            req = urllib.request.Request(url, headers={"User-Agent": "JuliaOS/2.2"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            results = []
            # Abstract
            abstract = data.get("AbstractText", "")
            if abstract:
                results.append(f"摘要: {abstract}")

            # Related topics
            for topic in data.get("RelatedTopics", [])[:max_results]:
                text = topic.get("Text", "")
                if text:
                    results.append(f"• {text}")

            # External links
            for result in data.get("Results", [])[:3]:
                results.append(f"• {result.get('Text', '')}")

            if not results:
                return f"未找到 '{query}' 的相关结果"

            return "\n".join(results[:max_results + 1])

        except Exception as e:
            return f"搜索失败: {e}"


class WebFetchTool:
    """Fetch and read a web page. LLM decides which pages are worth reading."""

    tool_name = "web_fetch"
    tool_description = "获取网页内容。当你想深入了解搜索结果中的某个链接时使用。"

    @staticmethod
    def fetch(url: str, max_chars: int = 4000) -> str:
        """Fetch a web page and extract readable text."""
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "JuliaOS/2.2"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            # Simple text extraction: strip HTML tags
            import re
            # Remove scripts and styles
            html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
            html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
            # Remove tags
            text = re.sub(r'<[^>]+>', ' ', html)
            # Collapse whitespace
            text = re.sub(r'\s+', ' ', text).strip()

            if len(text) > max_chars:
                text = text[:max_chars] + f"\n... (截断, 原文{len(text)}字符)"

            return f"=== {url} ===\n{text}"
        except Exception as e:
            return f"获取失败: {e}"


# ── Tool Registration ───────────────────────────────────────────────────────

def register_web_tools(registry):
    """Register web tools in the capability registry."""
    from julia_core.capability.tool_protocol import ToolSchema, ToolCategory

    registry.register(
        ToolSchema(
            name="web_search",
            description=WebSearchTool.tool_description,
            category=ToolCategory.WEB,
            parameters={"query": "搜索关键词", "max_results": "最大结果数（默认5）"},
            example="web_search(query='Claude Code latest features')",
        ),
        lambda query="", max_results=5: WebSearchTool.search(query, int(max_results)),
    )

    registry.register(
        ToolSchema(
            name="web_fetch",
            description=WebFetchTool.tool_description,
            category=ToolCategory.WEB,
            parameters={"url": "网页URL", "max_chars": "最大字符数（默认4000）"},
            example="web_fetch(url='https://example.com/article')",
        ),
        lambda url="", max_chars=4000: WebFetchTool.fetch(url, int(max_chars)),
    )
