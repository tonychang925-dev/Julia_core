"""Julia OS v2.3 World Access — Web search + fetch tools.

LLM decides: what to search, when to fetch, how to use results.
Runtime does: provider-agnostic HTTP requests. Nothing more.

Provider abstraction: LLM never knows which search engine.
  Dev:  DuckDuckGo (free, no key)
  Prod: SerpAPI (set SERPAPI_KEY env var)
  Extend: Brave, Google CSE, Bing — implement SearchProvider, drop in.
"""

from __future__ import annotations

import re
import urllib.request
from julia_core.capability.web_provider import WebSearchEngine


class WebSearchTool:
    """Provider-agnostic search. LLM decides when to search, never knows engine."""

    @staticmethod
    def search(query: str, max_results: int = 5) -> str:
        return WebSearchEngine.search(query, max_results)


class WebFetchTool:
    """Fetch and extract text from a web page."""

    @staticmethod
    def fetch(url: str, max_chars: int = 4000) -> str:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "JuliaOS/2.3"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
            # Strip scripts, styles, tags
            html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
            html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', html)
            text = re.sub(r'\s+', ' ', text).strip()
            if len(text) > max_chars:
                text = text[:max_chars] + f"\n... (截断, 原文{len(text)}字符)"
            return f"=== {url} ===\n{text}"
        except Exception as e:
            return f"获取失败: {e}"


def register_web_tools(registry):
    from julia_core.capability.tool_protocol import ToolSchema, ToolCategory

    registry.register(
        ToolSchema(
            name="web_search",
            description=f"搜索互联网获取最新信息（引擎: {WebSearchEngine.provider_name()}）。当需要实时知识时使用。设置 SERPAPI_KEY 可升级为生产级搜索。",
            category=ToolCategory.WEB,
            parameters={"query": "搜索关键词"},
            example="web_search(query='Claude Code latest features')",
        ),
        lambda query="", max_results=5: WebSearchTool.search(query, int(max_results)),
    )

    registry.register(
        ToolSchema(
            name="web_fetch",
            description="获取并提取网页文本内容。当想深入了解搜索结果中的某个链接时使用。",
            category=ToolCategory.WEB,
            parameters={"url": "网页URL"},
            example="web_fetch(url='https://arxiv.org/abs/...')",
        ),
        lambda url="", max_chars=4000: WebFetchTool.fetch(url, int(max_chars)),
    )
