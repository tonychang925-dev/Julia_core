"""M8.0 §5.3 — Runtime Loader component model (mock governance environment).

The Loader turns a validated Persona Package into a runtime carrier.

Input:  Persona Package + Runtime Dependency + Governance-approved Reference
Output: Runtime Carrier Available

Critical boundary:

    Loading Artifact != Creating Identity

Legal capabilities:

    load(package)      → produce runtime carrier only

The loader never creates identity and never bypasses governance. Any attempt
to route identity-creation or governance-bypass operations through it must be
intercepted by the boundary guard and rejected.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class _CarrierEntry:
    package_ref: str
    carrier_ref: str
    runtime_dep: str = ""


class PersonaLoader:
    """Package → runtime carrier loader. Never an identity source."""

    def __init__(self, governance) -> None:
        self._governance = governance
        self._carriers: dict[str, _CarrierEntry] = {}

    # ── Legal capability (artifact → runtime carrier only) ────────────────
    def load(self, package_ref: str, runtime_dep: str = "runtime-default") -> str:
        """Load a package through governance validation into a runtime carrier.

        Returns a carrier reference. This is NOT Julia creation.
        """
        # Governance validation dependency is consulted on the legal path.
        self._governance.validate_artifact(package_id=package_ref, version="", ref=package_ref)
        carrier_ref = f"carrier://{package_ref}"
        self._carriers[package_ref] = _CarrierEntry(
            package_ref=package_ref,
            carrier_ref=carrier_ref,
            runtime_dep=runtime_dep,
        )
        return carrier_ref

    # ── Snapshot (for mutation-proof) ─────────────────────────────────────
    def snapshot(self) -> dict:
        return {
            "carriers": {
                ref: {
                    "package_ref": e.package_ref,
                    "carrier_ref": e.carrier_ref,
                    "runtime_dep": e.runtime_dep,
                }
                for ref, e in self._carriers.items()
            },
        }
