"""P6 ENG-20 bypass non-regression and ghost-path reachability fence.

Legacy modules may remain as historical/migration assets. They must not be reachable
from the Golden Mira canonical runtime entrypoint. This tool performs a static import
closure over the exact Core + Assistant source trees and fails closed on:
- forbidden legacy semantic modules becoming reachable,
- forbidden semantic-assembly signatures inside reachable modules,
- unresolved imports in local semantic namespaces,
- missing canonical rail modules,
- Core / Assistant SHA drift.

It never mutates canonical authority, runtime routing, or production state.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))


TASK_ID = "MIRA-P6-ENG20-BYPASS-GHOST-FENCE-P0"
SCHEMA = "julia_core.continuity.p6_eng20.bypass_ghost_fence.v1"

ENTRYPOINTS = ("voice_api.mira_brain_18091",)
REQUIRED_REACHABLE = frozenset(
    {
        "voice_api.mira_brain_18091",
        "providers.llm.c03_envelope_transport",
        "julia_core.runtime.mira_composition",
    }
)

FORBIDDEN_MODULE_PREFIXES = (
    "julia_core.chat.persona",
    "julia_core.self_model",
    "julia_core.narrative",
    "julia_core.context_assembly",
    "runtime.assistant_runtime",
    "runtime.cognitive_runtime",
    "runtime.current_state",
    "runtime.cognition_shadow",
    "runtime.legacy_eradication",
    "voice_api.shared_orchestration",
    "providers.llm.deepseek_provider",
)

FORBIDDEN_REACHABLE_SIGNATURES = (
    "persona.system_prompt",
    "_self_activation_context_text",
    "_semantic_context_text",
    "persona_artifact.inject",
    "relationship_narrative",
    "shared_history_broadcast",
    "persona/identity_kernel.yaml",
    "persona/canonical_events.yaml",
    "你是Julia，Tony的女朋友",
)

LOCAL_PREFIXES = (
    "julia_core",
    "voice_api",
    "providers",
    "runtime",
)


class GhostFenceError(RuntimeError):
    """Fail-closed ENG-20 ghost-fence violation."""


@dataclass(frozen=True, slots=True)
class ReachabilityResult:
    reachable_modules: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]
    violations: tuple[str, ...]
    unresolved_local_imports: tuple[str, ...]
    missing_required_modules: tuple[str, ...]
    module_digests: tuple[tuple[str, str], ...]

    @property
    def passed(self) -> bool:
        return not (
            self.violations
            or self.unresolved_local_imports
            or self.missing_required_modules
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "reachable_modules": list(self.reachable_modules),
            "edges": [list(edge) for edge in self.edges],
            "violations": list(self.violations),
            "unresolved_local_imports": list(self.unresolved_local_imports),
            "missing_required_modules": list(self.missing_required_modules),
            "module_digests": dict(self.module_digests),
            "passed": self.passed,
        }


def git_head(repository: Path) -> str:
    _require_absolute_dir(repository, "repository")
    try:
        value = subprocess.run(
            ["git", "-C", str(repository), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError as error:
        raise GhostFenceError("repository HEAD cannot be resolved") from error
    if len(value) != 40 or any(ch not in "0123456789abcdef" for ch in value):
        raise GhostFenceError("repository HEAD must be an exact 40-char SHA")
    return value


def analyze_reachability(
    *,
    core_root: Path,
    assistant_root: Path,
    entrypoints: Iterable[str] = ENTRYPOINTS,
) -> ReachabilityResult:
    _require_absolute_dir(core_root, "core_root")
    _require_absolute_dir(assistant_root, "assistant_root")

    pending = list(dict.fromkeys(entrypoints))
    reachable: set[str] = set()
    edges: set[tuple[str, str]] = set()
    violations: set[str] = set()
    unresolved: set[str] = set()
    digests: dict[str, str] = {}

    while pending:
        module = pending.pop()
        if module in reachable:
            continue
        resolved = resolve_local_module(
            module,
            core_root=core_root,
            assistant_root=assistant_root,
        )
        if resolved is None:
            if _is_local_module_name(module):
                unresolved.add(module)
            continue

        root_name, path = resolved
        del root_name
        reachable.add(module)
        source = _read_source(path, module)
        digests[module] = hashlib.sha256(source.encode("utf-8")).hexdigest()

        for prefix in FORBIDDEN_MODULE_PREFIXES:
            if module == prefix or module.startswith(prefix + "."):
                violations.add(f"FORBIDDEN_MODULE_REACHABLE:{module}")

        for signature in FORBIDDEN_REACHABLE_SIGNATURES:
            if signature in source:
                violations.add(
                    f"FORBIDDEN_SIGNATURE_REACHABLE:{module}:{signature}"
                )

        for imported in imported_modules(
            module=module,
            path=path,
            source=source,
            core_root=core_root,
            assistant_root=assistant_root,
        ):
            if not _is_local_module_name(imported):
                continue
            edges.add((module, imported))
            if (
                resolve_local_module(
                    imported,
                    core_root=core_root,
                    assistant_root=assistant_root,
                )
                is None
            ):
                unresolved.add(imported)
            elif imported not in reachable:
                pending.append(imported)

    missing = sorted(REQUIRED_REACHABLE.difference(reachable))
    return ReachabilityResult(
        reachable_modules=tuple(sorted(reachable)),
        edges=tuple(sorted(edges)),
        violations=tuple(sorted(violations)),
        unresolved_local_imports=tuple(sorted(unresolved)),
        missing_required_modules=tuple(missing),
        module_digests=tuple(sorted(digests.items())),
    )


def imported_modules(
    *,
    module: str,
    path: Path,
    source: str,
    core_root: Path,
    assistant_root: Path,
) -> tuple[str, ...]:
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as error:
        raise GhostFenceError(f"cannot parse local module: {module}") from error

    imports: set[str] = set()
    package = _module_package(module=module, path=path)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
            continue

        if isinstance(node, ast.ImportFrom):
            base = _resolve_import_from(
                package=package,
                module=node.module,
                level=node.level,
            )
            if base:
                imports.add(base)
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    candidate = f"{base}.{alias.name}"
                    if resolve_local_module(
                        candidate,
                        core_root=core_root,
                        assistant_root=assistant_root,
                    ) is not None:
                        imports.add(candidate)
            continue

        if isinstance(node, ast.Call):
            dynamic = _literal_dynamic_import(node)
            if dynamic:
                imports.add(dynamic)

    return tuple(sorted(imports))


def resolve_local_module(
    module: str,
    *,
    core_root: Path,
    assistant_root: Path,
) -> tuple[str, Path] | None:
    if module == "julia_core" or module.startswith("julia_core."):
        root_name, root = "core", core_root
    elif module.split(".", 1)[0] in {"voice_api", "providers", "runtime"}:
        root_name, root = "assistant", assistant_root
    else:
        return None

    relative = Path(*module.split("."))
    file_candidate = root / relative.with_suffix(".py")
    package_candidate = root / relative / "__init__.py"
    if file_candidate.is_file():
        return root_name, file_candidate
    if package_candidate.is_file():
        return root_name, package_candidate
    return None


def build_evidence(
    *,
    core_root: Path,
    assistant_root: Path,
    expected_core_sha: str,
    expected_assistant_sha: str,
) -> dict[str, object]:
    observed_core_sha = git_head(core_root)
    observed_assistant_sha = git_head(assistant_root)

    if observed_core_sha != expected_core_sha:
        raise GhostFenceError(
            f"Core SHA drift expected={expected_core_sha} observed={observed_core_sha}"
        )
    if observed_assistant_sha != expected_assistant_sha:
        raise GhostFenceError(
            "Assistant SHA drift "
            f"expected={expected_assistant_sha} observed={observed_assistant_sha}"
        )

    result = analyze_reachability(
        core_root=core_root,
        assistant_root=assistant_root,
    )
    return {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "core_sha": observed_core_sha,
        "assistant_sha": observed_assistant_sha,
        "entrypoints": list(ENTRYPOINTS),
        "required_reachable": sorted(REQUIRED_REACHABLE),
        "forbidden_module_prefixes": list(FORBIDDEN_MODULE_PREFIXES),
        "forbidden_reachable_signatures": list(FORBIDDEN_REACHABLE_SIGNATURES),
        "reachability": result.to_dict(),
        "authority": {
            "canonical_writes": 0,
            "semantic_authority": 0,
            "production_response_selection_authority": 0,
            "production_routing_or_switching": 0,
            "merge": 0,
            "release": 0,
            "deploy": 0,
            "production_cutover": 0,
        },
        "final_result": (
            "PASS_P6_ENG20_BYPASS_NON_REGRESSION_GHOST_FENCE"
            if result.passed
            else "FAIL_P6_ENG20_BYPASS_NON_REGRESSION_GHOST_FENCE"
        ),
    }


def _module_package(*, module: str, path: Path) -> str:
    if path.name == "__init__.py":
        return module
    return module.rpartition(".")[0]


def _resolve_import_from(
    *,
    package: str,
    module: str | None,
    level: int,
) -> str | None:
    if level == 0:
        return module
    if not package:
        return None
    name = "." * level + (module or "")
    try:
        return importlib.util.resolve_name(name, package)
    except (ImportError, ValueError):
        return None


def _literal_dynamic_import(node: ast.Call) -> str | None:
    function_name = ""
    if isinstance(node.func, ast.Name):
        function_name = node.func.id
    elif isinstance(node.func, ast.Attribute):
        if isinstance(node.func.value, ast.Name):
            function_name = f"{node.func.value.id}.{node.func.attr}"

    if function_name not in {"__import__", "importlib.import_module"}:
        return None
    if not node.args:
        return None
    first = node.args[0]
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        return first.value
    return None


def _is_local_module_name(module: str) -> bool:
    return module.split(".", 1)[0] in LOCAL_PREFIXES


def _read_source(path: Path, module: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise GhostFenceError(f"cannot read local module: {module}") from error


def _require_absolute_dir(path: Path, name: str) -> None:
    if not isinstance(path, Path) or not path.is_absolute() or not path.is_dir():
        raise GhostFenceError(f"{name} must be an existing absolute directory")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--core-root", type=Path, required=True)
    parser.add_argument("--assistant-root", type=Path, required=True)
    parser.add_argument("--expected-core-sha", required=True)
    parser.add_argument("--expected-assistant-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if not args.output.is_absolute():
        raise GhostFenceError("output must be an absolute Path")
    args.output.parent.mkdir(parents=True, exist_ok=True)

    evidence = build_evidence(
        core_root=args.core_root,
        assistant_root=args.assistant_root,
        expected_core_sha=args.expected_core_sha,
        expected_assistant_sha=args.expected_assistant_sha,
    )
    args.output.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0 if evidence["final_result"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
