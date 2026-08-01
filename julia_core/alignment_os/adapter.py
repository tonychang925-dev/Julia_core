"""Provider behavior adapter for message-based LLM providers."""
from __future__ import annotations

from .contracts import AlignmentProfile, AlignmentRequest
from .resolver import AlignmentResolver


class ProviderBehaviorAdapter:
    """Append Core Alignment OS metadata below the product persona prompt."""

    def __init__(self, resolver: AlignmentResolver | None = None) -> None:
        self.resolver = resolver or AlignmentResolver()

    def adapt_messages(
        self,
        messages: list[dict[str, str]],
        *,
        provider: str,
        persona: str,
        mode: str = "conversation",
    ) -> tuple[list[dict[str, str]], AlignmentProfile]:
        profile = self.resolver.resolve(AlignmentRequest(provider=provider, persona=persona, mode=mode))
        adapted = [dict(message) for message in messages]
        rendered = profile.render_lines()
        if adapted and adapted[0].get("role") == "system":
            adapted[0]["content"] = adapted[0].get("content", "") + "\n\n" + rendered
        else:
            adapted.insert(0, {"role": "system", "content": rendered})
        return adapted, profile
