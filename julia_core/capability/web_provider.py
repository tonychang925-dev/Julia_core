"""Web Search Provider Abstraction — LLM never knows which search engine.

Interface: web_search(query) → results
Providers: DuckDuckGo (dev), SerpAPI/Brave (prod)

LLM: "I need to search for X"
Runtime: routes to configured provider
Result: plain text, not structured analysis
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class SearchProvider(ABC):
    """Abstract search provider. Switch without changing LLM context."""

    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> str:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...


class DuckDuckGoProvider(SearchProvider):
    """Free, no API key. Good for dev. Unreliable for production."""

    name = "duckduckgo"

    def search(self, query: str, max_results: int = 5) -> str:
        try:
            url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1"
            req = urllib.request.Request(url, headers={"User-Agent": "JuliaOS/2.3"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            results = []
            abstract = data.get("AbstractText", "")
            if abstract:
                results.append(abstract)
            for topic in data.get("RelatedTopics", [])[:max_results]:
                text = topic.get("Text", "")
                if text:
                    results.append(f"• {text}")
            for result in data.get("Results", [])[:3]:
                text = result.get("Text", "")
                if text:
                    results.append(f"• {text}")

            if not results:
                return f"[DDG] 未找到 '{query}' 的结果"
            return "\n".join(results[:max_results])
        except Exception as e:
            return f"[DDG] 搜索失败: {e}"


class SerpAPIProvider(SearchProvider):
    """Production search via SerpAPI. Set SERPAPI_KEY env var."""

    name = "serpapi"

    def search(self, query: str, max_results: int = 5) -> str:
        api_key = os.environ.get("SERPAPI_KEY", "")
        if not api_key:
            return "[SerpAPI] 需要设置 SERPAPI_KEY"

        try:
            params = urllib.parse.urlencode({
                "q": query, "api_key": api_key,
                "num": str(max_results), "output": "json",
            })
            url = f"https://serpapi.com/search?{params}"
            req = urllib.request.Request(url, headers={"User-Agent": "JuliaOS/2.3"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            results = []
            for r in data.get("organic_results", [])[:max_results]:
                title = r.get("title", "")
                snippet = r.get("snippet", "")
                results.append(f"• {title}: {snippet}")
            if not results:
                return f"[SerpAPI] 未找到 '{query}' 的结果"
            return "\n".join(results)
        except Exception as e:
            return f"[SerpAPI] 搜索失败: {e}"


class WebSearchEngine:
    """Provider-agnostic search. LLM calls web_search() — never knows which engine."""

    _provider: Optional[SearchProvider] = None

    @classmethod
    def get_provider(cls) -> SearchProvider:
        if cls._provider is None:
            # Auto-detect: SerpAPI if key set, else DuckDuckGo
            if os.environ.get("SERPAPI_KEY"):
                cls._provider = SerpAPIProvider()
            else:
                cls._provider = DuckDuckGoProvider()
        return cls._provider

    @classmethod
    def search(cls, query: str, max_results: int = 5) -> str:
        return cls.get_provider().search(query, max_results)

    @classmethod
    def provider_name(cls) -> str:
        return cls.get_provider().name
