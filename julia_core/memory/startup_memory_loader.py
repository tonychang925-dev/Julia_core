from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class StartupMemoryFact:
    field: str
    label: str
    value: str
    authority: float
    source: str


@dataclass(frozen=True)
class StartupMemoryPack:
    schema_version: str
    subject: str
    facts: tuple[StartupMemoryFact, ...]
    negative_facts: tuple[str, ...]
    answering_rules: tuple[str, ...]
    source_evidence: tuple[dict[str, str], ...]

    @property
    def loaded(self) -> bool:
        return bool(self.facts)

    def to_prompt_lines(self) -> list[str]:
        if not self.loaded:
            return []
        lines = [
            "- Startup memory load: governed identity facts loaded before retrieval (Claude-style session bootstrap).",
            "- Startup memory authority: governed facts override assistant archive mistakes and model priors.",
        ]
        for fact in self.facts:
            lines.append(f"- {fact.label}: {fact.value} (authority={fact.authority:.2f}; source={fact.source})")
        if self.negative_facts:
            lines.append("- Conflict guards: " + "; ".join(self.negative_facts))
        if self.answering_rules:
            lines.append("- Answering rules: " + " ".join(self.answering_rules))
        return lines

    def to_metadata(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "subject": self.subject,
            "loaded": self.loaded,
            "fact_count": len(self.facts),
            "fields": [fact.field for fact in self.facts],
            "negative_fact_count": len(self.negative_facts),
            "source_evidence": list(self.source_evidence),
        }


class StartupMemoryLoader:
    """Load stable, governed startup memory without semantic/archive search."""

    LABELS = {
        "identity.name": "Name",
        "identity.real_name": "Real name",
        "identity.age": "Age",
        "identity.from": "From",
        "education.university": "University",
        "education.major": "Major",
        "career.current_work": "Current work",
        "family.father": "Father",
        "family.mother": "Mother",
        "family.brother": "Brother",
        "family.sibling_negative": "Sibling guard",
        "relationship.tony": "Relationship to Tony",
    }

    ORDER = tuple(LABELS.keys())

    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root)
        self.path = self.project_root / "memory" / "governed" / "identity_facts.json"

    def load(self) -> StartupMemoryPack:
        if not self.path.exists():
            return StartupMemoryPack("missing", "Julia", (), (), (), ())
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return StartupMemoryPack("invalid", "Julia", (), (), (), ())

        facts_payload = payload.get("facts", {}) if isinstance(payload, dict) else {}
        flat: dict[str, StartupMemoryFact] = {}
        if isinstance(facts_payload, dict):
            for group, values in facts_payload.items():
                if not isinstance(values, dict):
                    continue
                for key, raw in values.items():
                    if not isinstance(raw, dict):
                        continue
                    field = f"{group}.{key}"
                    value = str(raw.get("value", "")).strip()
                    if not value:
                        continue
                    try:
                        authority = float(raw.get("authority", 0.0))
                    except (TypeError, ValueError):
                        authority = 0.0
                    flat[field] = StartupMemoryFact(
                        field=field,
                        label=self.LABELS.get(field, field),
                        value=value,
                        authority=authority,
                        source=str(raw.get("source", "unknown")),
                    )

        ordered = [flat[field] for field in self.ORDER if field in flat]
        ordered.extend(fact for field, fact in flat.items() if field not in self.ORDER)
        negative_facts = tuple(
            str(item.get("value", item)).strip()
            for item in payload.get("negative_facts", [])
            if str(item.get("value", item) if isinstance(item, dict) else item).strip()
        )
        rules = tuple(str(item).strip() for item in payload.get("answering_rules", []) if str(item).strip())
        sources = tuple(item for item in payload.get("source_evidence", []) if isinstance(item, dict))
        return StartupMemoryPack(
            schema_version=str(payload.get("schema_version", "unknown")),
            subject=str(payload.get("subject", "Julia")),
            facts=tuple(ordered),
            negative_facts=negative_facts,
            answering_rules=rules,
            source_evidence=sources,
        )
