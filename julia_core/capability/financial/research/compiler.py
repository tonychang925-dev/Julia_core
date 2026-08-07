"""M3.2.7 Strategy Research Compiler — Card → ResearchPlan → CapabilityRequest.

Deterministic. Zero LLM. Located in Julia_core (owns research process).
ai_theme_app StrategyCards provide: what to investigate.
This compiler provides: how Julia investigates.

Usage:
  compiler = StrategyResearchCompiler()
  plan = compiler.compile(card_dict, subject_context)
  # plan.capability_requests are native Julia CapabilityRequest objects
  # ready for CapabilityManager.execute()
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from julia_core.capability.models import CapabilityRequest
from julia_core.capability.financial.research.models import (
    ResearchPlan,
    EvidenceItem,
    EvidenceBundle,
)
from julia_core.capability.financial.research.requirement_bindings import (
    REQUIREMENT_BINDINGS,
    RequirementBinding,
)


class UnresolvedRequirementBinding(Exception):
    """Template variable not resolved — capability request cannot be formed."""


class StrategyResearchCompiler:
    """Compiles ai_theme_app StrategyCard → executable Julia ResearchPlan.

    Steps:
      1. Card.possible_states → candidate_hypotheses (all untested)
      2. Card.required_data → REQUIREMENT_BINDINGS → CapabilityRequest[]
      3. Card.research_questions → included verbatim
      4. Unrecognized requirements → plan.missing_requirements

    Does NOT call LLM. Does NOT connect to external data.
    """

    def compile(self, card: dict, subject: dict) -> ResearchPlan:
        """Compile a ResearchPlan from a StrategyCard dict + subject context.

        Args:
            card: loaded StrategyCard JSON (from ai_theme_app)
            subject: {"subject_key", "subject_name", "trade_date",
                      "leader_code", "julia_stage", "workbench_stage"}
        """
        # Validate required subject fields
        for required in ("subject_key", "trade_date"):
            if not subject.get(required):
                raise ValueError(f"subject.{required} is required")

        plan = ResearchPlan(
            subject_key=subject["subject_key"],
            subject_name=subject.get("subject_name", ""),
            trade_date=subject["trade_date"],
            triggered_card=card.get("strategy_id", ""),
        )

        # Step 1: possible_states → untested hypotheses
        for state in card.get("possible_states", []):
            plan.candidate_hypotheses.append({
                "state": f"{card['strategy_id']}.{state['state']}",
                "canonical_state": state["state"],
                "evidence_pattern": state.get("evidence_pattern", {}),
                "strategy_guidance": {
                    "stance": state.get("action", "observe"),
                    "authority": "advisory_only",
                },
                "status": "untested",
            })

        # Step 2: required_data → CapabilityRequest
        for req_name in card.get("required_data", []):
            binding = REQUIREMENT_BINDINGS.get(req_name)
            if binding is None:
                plan.missing_requirements.append(req_name)
                continue

            try:
                args = self._resolve_args(binding, subject)
            except UnresolvedRequirementBinding as e:
                plan.missing_requirements.append(f"{req_name}: {e}")
                continue

            cr = CapabilityRequest(
                capability_name=binding.capability_name,
                arguments=args,
                cognitive_mode="investment_research",
                reason=(
                    f"ResearchCase {plan.research_case_id[:12]}: "
                    f"test {card['strategy_id']} for {subject['subject_key']} "
                    f"(req: {req_name})"
                ),
            )
            plan.capability_requests.append(cr)

        # Step 3: research questions — verbatim
        plan.research_questions = card.get("research_questions", [])

        return plan

    def _resolve_args(self, binding: RequirementBinding, subject: dict) -> dict:
        """Resolve $subject. template variables in binding arguments."""
        args = {}
        for k, v in binding.arguments_template.items():
            if isinstance(v, str) and "$subject." in v:
                resolved = v
                for sk, sv in subject.items():
                    resolved = resolved.replace(f"$subject.{sk}", str(sv))
                if "$subject." in resolved:
                    raise UnresolvedRequirementBinding(
                        f"Unresolved template in '{k}': {resolved} "
                        f"(missing subject field?)"
                    )
                args[k] = resolved
            else:
                args[k] = v
        return args


def create_evidence_bundle(plan: ResearchPlan) -> EvidenceBundle:
    """Initialize an EvidenceBundle to track capability execution results."""
    return EvidenceBundle(
        research_case_id=plan.research_case_id,
        subject_key=plan.subject_key,
        as_of=plan.trade_date,
        evidence=[
            EvidenceItem(
                requirement_id=_req_name_from_cr(cr),
                capability_request_id=cr.request_id,
            )
            for cr in plan.capability_requests
        ],
        evidence_count=len(plan.capability_requests),
    )


def _req_name_from_cr(cr: CapabilityRequest) -> str:
    """Extract requirement name from capability request reason."""
    import re
    m = re.search(r'req:\s*(\S+)', cr.reason)
    return m.group(1) if m else cr.capability_name


__all__ = ["StrategyResearchCompiler", "UnresolvedRequirementBinding", "create_evidence_bundle"]
