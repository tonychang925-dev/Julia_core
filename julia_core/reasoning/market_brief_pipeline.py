"""M2.3 Market Brief Pipeline — Capability → Context → Reasoning → Julia Brief.

The full cognitive chain from user utterance to Julia's natural-language
market interpretation. This is the M2 core — it proves Julia can USE
capabilities, not just CALL them.

Flow:
  User text → Intent Resolver → CapabilityRequest → CapabilityManager
  → market.snapshot.read → AiThemeProvider → DecisionEnvelope v1.1
  → MarketBriefContextAdapter → ContextBlocks → Julia Brief

ADR-026 P2: Context OS is Single Authority.
ADR-026 P4: Provider supplies capability, not cognition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta

from julia_core.capability.manager import CapabilityManager
from julia_core.capability.models import CapabilityRequest
from julia_core.context_os.providers.market_context import MarketBriefContextAdapter
from julia_core.reasoning.intents.market_brief import (
    MarketBriefIntentResolver,
    MarketIntent,
    IntentResult,
)

CST = timezone(timedelta(hours=8))


# ── Brief Result ────────────────────────────────────────────────────────────

@dataclass
class MarketBriefResult:
    """The full output of a Market Brief pipeline execution.

    Contains everything needed for evidence tracing (M2-AC3) and
    future M7 Feedback Loop integration.
    """
    brief_id: str
    user_query: str
    intent: MarketIntent
    capability_status: str            # "success" | "unavailable" | "denied" | "unknown"
    capability_request_id: str = ""
    provider: str = ""
    schema_version: str = ""
    prediction_ids: tuple[str, ...] = ()
    context_blocks: list = field(default_factory=list)
    julia_response: str = ""
    generated_at: str = field(default_factory=lambda: datetime.now(CST).isoformat())
    evidence: dict = field(default_factory=dict)


# ── Pipeline ────────────────────────────────────────────────────────────────

class MarketBriefPipeline:
    """Orchestrates the full Market Brief cognitive chain.

    Usage:
        pipeline = MarketBriefPipeline(manager)
        result = await pipeline.process("Julia，今天市场怎么样？")

    The pipeline:
      1. Resolves user intent
      2. Creates CapabilityRequest
      3. Routes through CapabilityManager (permission + evidence)
      4. Converts result to ContextBlocks
      5. Produces structured output for Reasoning layer

    Step 5 (Reasoning → Julia response) is handled by the Reasoning Engine
    consuming the ContextBlocks. This pipeline produces the blocks and metadata
    that Reasoning uses.
    """

    def __init__(self, manager: CapabilityManager):
        self.manager = manager
        self.intent_resolver = MarketBriefIntentResolver()
        self.context_adapter = MarketBriefContextAdapter()

    async def process(
        self,
        user_text: str,
        session_id: str | None = None,
    ) -> MarketBriefResult:
        """Execute the full Market Brief pipeline from user query to structured output."""

        # Step 1: Detect intent
        intent_result = self.intent_resolver.resolve(user_text)

        brief_id = f"brief_{datetime.now(CST).strftime('%Y%m%d_%H%M%S')}"

        if not intent_result.is_market_related:
            return MarketBriefResult(
                brief_id=brief_id,
                user_query=user_text,
                intent=intent_result.intent,
                capability_status="not_requested",
                julia_response="",
            )

        # Step 2: Create CapabilityRequest
        request = self.intent_resolver.to_capability_request(intent_result, session_id)
        if request is None:
            return MarketBriefResult(
                brief_id=brief_id,
                user_query=user_text,
                intent=intent_result.intent,
                capability_status="not_requested",
            )

        # Step 3: Execute through CapabilityManager
        capability_result = await self.manager.execute(request)

        # Step 4: Extract prediction_ids from the result data
        prediction_ids: tuple[str, ...] = ()
        if capability_result.status == "success":
            data_wrapper = capability_result.data
            inner_data = data_wrapper.get("data", {})
            if isinstance(inner_data, dict):
                signals = inner_data.get("top_signals", [])
                pids = []
                for s in signals:
                    if isinstance(s, dict) and s.get("prediction_id"):
                        pids.append(s["prediction_id"])
                prediction_ids = tuple(pids)

        # Step 5: Convert to ContextBlocks
        context_blocks = []
        if capability_result.status == "success":
            context_blocks = self.context_adapter.build_context_blocks(
                capability_result.data
            )

        # Step 6: Build evidence record
        evidence = {
            "capability": request.capability_name,
            "capability_request_id": request.request_id,
            "capability_status": capability_result.status,
            "provider": capability_result.provider,
            "schema_version": capability_result.schema_version,
            "evidence_ledger_entries": [
                {
                    "capability": e.capability_name,
                    "provider": e.provider,
                    "status": e.status,
                    "timestamp": e.timestamp,
                }
                for e in self.manager.evidence.entries[-3:]
            ],
        }

        return MarketBriefResult(
            brief_id=brief_id,
            user_query=user_text,
            intent=intent_result.intent,
            capability_status=capability_result.status,
            capability_request_id=request.request_id,
            provider=capability_result.provider,
            schema_version=capability_result.schema_version,
            prediction_ids=prediction_ids,
            context_blocks=context_blocks,
            evidence=evidence,
        )


__all__ = ["MarketBriefPipeline", "MarketBriefResult"]
