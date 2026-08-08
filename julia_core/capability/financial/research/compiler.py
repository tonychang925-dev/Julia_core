"""M3.2.7 Strategy Research Compiler — Card → ResearchProbe[] → ResearchPlan.

Deterministic. Zero LLM. No regex on reason strings.
ResearchProbe is the stable identity carrier — probe_id never parsed from text.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from julia_core.capability.models import CapabilityRequest
from julia_core.capability.financial.research.models import (
    ResearchPlan,
    ResearchProbe,
    EvidenceItem,
    EvidenceBundle,
)
from julia_core.capability.financial.research.requirement_bindings import (
    REQUIREMENT_BINDINGS,
    RequirementBinding,
)


class UnresolvedRequirementBinding(Exception):
    pass


class StrategyResearchCompiler:
    """Compiles ai_theme_app StrategyCard → executable Julia ResearchPlan.

    Each required_data → RequirementBinding → ResearchProbe + CapabilityRequest.
    Probes carry stable probe_id — no regex extraction from reason strings.
    """

    def compile(self, card: dict, subject: dict) -> ResearchPlan:
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
                "predicates": state.get("predicates", []),
                "evidence_pattern": state.get("evidence_pattern", {}),
                "strategy_guidance": {
                    "stance": state.get("action", "observe"),
                    "authority": "advisory_only",
                },
                "status": "untested",
            })

        # Step 2: required_data → ResearchProbe[] (NOT raw CapabilityRequest[])
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
                    f"test {card['strategy_id']} for {subject['subject_key']}"
                ),
            )

            probe = ResearchProbe(
                requirement_id=req_name,
                binding_id=binding.requirement_id,
                request=cr,
                derive_metric=binding.derive_metric,
                missing_policy=binding.missing_policy,
            )
            plan.probes.append(probe)

        plan.research_questions = card.get("research_questions", [])
        return plan

    def _resolve_args(self, binding: RequirementBinding, subject: dict) -> dict:
        args = {}
        for k, v in binding.arguments_template.items():
            if isinstance(v, str) and "$subject." in v:
                resolved = v
                for sk, sv in subject.items():
                    resolved = resolved.replace(f"$subject.{sk}", str(sv))
                if "$subject." in resolved:
                    raise UnresolvedRequirementBinding(
                        f"Unresolved template in '{k}': {resolved}"
                    )
                args[k] = resolved
            else:
                args[k] = v
        return args


def create_evidence_bundle(plan: ResearchPlan) -> EvidenceBundle:
    """Initialize EvidenceBundle from ResearchProbes.

    probe_id is the stable identity carrier.
    No regex. No string parsing.
    """
    bundle = EvidenceBundle(
        research_case_id=plan.research_case_id,
        subject_key=plan.subject_key,
        as_of=plan.trade_date,
        evidence_count=len(plan.probes),
    )
    for probe in plan.probes:
        bundle.evidence.append(EvidenceItem(
            requirement_id=probe.requirement_id,
            probe_id=probe.probe_id,
            capability_request_id=probe.request.request_id,
            derived_metric=probe.derive_metric,
            missing_policy=probe.missing_policy,
        ))
    return bundle


__all__ = ["StrategyResearchCompiler", "UnresolvedRequirementBinding", "create_evidence_bundle"]
