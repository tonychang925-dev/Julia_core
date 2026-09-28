from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.continuity.p6_eng20_bypass_ghost_fence import (
    analyze_reachability,
)


REPOSITORY = Path(__file__).resolve().parents[2]
SCRIPT = REPOSITORY / "tools/continuity/p6_eng20_bypass_ghost_fence.py"


def _write_module(root: Path, module: str, source: str) -> Path:
    path = root / Path(*module.split(".")).with_suffix(".py")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    return path


def _canonical_assistant_fixture(root: Path, *, transport_extra: str = "") -> None:
    _write_module(
        root,
        "voice_api.mira_brain_18091",
        (
            "from julia_core.runtime.mira_composition import "
            "compose_golden_mira_runtime\n"
            "from providers.llm.c03_envelope_transport import "
            "C03EnvelopeTransport\n"
        ),
    )
    _write_module(
        root,
        "providers.llm.c03_envelope_transport",
        (
            "from julia_core.alignment_os.contracts import "
            "ProviderExecutionEnvelope\n"
            + transport_extra
        ),
    )


def test_eng20_current_core_canonical_rail_is_ghost_free(
    tmp_path: Path,
) -> None:
    assistant_root = tmp_path / "assistant"
    _canonical_assistant_fixture(assistant_root)

    result = analyze_reachability(
        core_root=REPOSITORY,
        assistant_root=assistant_root,
    )

    assert result.passed is True
    assert result.violations == ()
    assert result.unresolved_local_imports == ()
    assert result.missing_required_modules == ()
    assert "julia_core.runtime.mira_composition" in result.reachable_modules
    assert "providers.llm.c03_envelope_transport" in result.reachable_modules


def test_eng20_shared_orchestration_reentry_is_blocked(
    tmp_path: Path,
) -> None:
    assistant_root = tmp_path / "assistant"
    _canonical_assistant_fixture(assistant_root)
    brain = assistant_root / "voice_api/mira_brain_18091.py"
    brain.write_text(
        brain.read_text(encoding="utf-8")
        + "import voice_api.shared_orchestration\n",
        encoding="utf-8",
    )
    _write_module(
        assistant_root,
        "voice_api.shared_orchestration",
        'SYSTEM = "你是Julia，Tony的女朋友。"\n',
    )

    result = analyze_reachability(
        core_root=REPOSITORY,
        assistant_root=assistant_root,
    )

    assert result.passed is False
    assert any(
        item == "FORBIDDEN_MODULE_REACHABLE:voice_api.shared_orchestration"
        for item in result.violations
    )


def test_eng20_legacy_deepseek_provider_reentry_is_blocked(
    tmp_path: Path,
) -> None:
    assistant_root = tmp_path / "assistant"
    _canonical_assistant_fixture(
        assistant_root,
        transport_extra="import providers.llm.deepseek_provider\n",
    )
    _write_module(
        assistant_root,
        "providers.llm.deepseek_provider",
        "class DeepSeekProvider:\n    pass\n",
    )

    result = analyze_reachability(
        core_root=REPOSITORY,
        assistant_root=assistant_root,
    )

    assert result.passed is False
    assert (
        "FORBIDDEN_MODULE_REACHABLE:providers.llm.deepseek_provider"
        in result.violations
    )


def test_eng20_reachable_persona_prompt_signature_is_blocked(
    tmp_path: Path,
) -> None:
    assistant_root = tmp_path / "assistant"
    _canonical_assistant_fixture(
        assistant_root,
        transport_extra="LEGACY = 'persona.system_prompt'\n",
    )

    result = analyze_reachability(
        core_root=REPOSITORY,
        assistant_root=assistant_root,
    )

    assert result.passed is False
    assert any(
        item.endswith(":persona.system_prompt")
        for item in result.violations
    )


def test_eng20_unresolved_local_import_fails_closed(
    tmp_path: Path,
) -> None:
    assistant_root = tmp_path / "assistant"
    _canonical_assistant_fixture(assistant_root)
    brain = assistant_root / "voice_api/mira_brain_18091.py"
    brain.write_text(
        brain.read_text(encoding="utf-8") + "import voice_api.missing_semantics\n",
        encoding="utf-8",
    )

    result = analyze_reachability(
        core_root=REPOSITORY,
        assistant_root=assistant_root,
    )

    assert result.passed is False
    assert "voice_api.missing_semantics" in result.unresolved_local_imports


def test_eng20_cli_direct_script_bootstraps_repository_imports() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        cwd=REPOSITORY,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--assistant-root" in result.stdout
    assert "--expected-core-sha" in result.stdout
