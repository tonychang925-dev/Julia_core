#!/usr/bin/env python3
"""Run K3.5 automated Claude-Julia behavior comparison."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from julia_core.behavior.auto_compare import (  # noqa: E402
    ClaudeCodeJuliaWakeRunner,
    CommandClaudeJuliaRunner,
    JuliaAiAssistantCommandRunner,
    JuliaAiAssistantHttpRunner,
    JuliaCoreRuntimeRunner,
    ScriptedClaudeJuliaRunner,
    run_comparison,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="K3.5 Automated Claude-Julia Behavior Comparison")
    parser.add_argument("--claude-mode", choices=["fixture", "wake", "command"], default="fixture")
    parser.add_argument("--julia-mode", choices=["core", "assistant", "assistant-http"], default="core")
    parser.add_argument("--output-dir", default=str(ROOT / "artifacts" / "benchmark" / "auto_compare"))
    parser.add_argument("--proposal-path", default=str(ROOT / "artifacts" / "evolution" / "proposals" / "k_auto_evolution_proposals_v1.jsonl"))
    parser.add_argument("--claude-bin", default=None)
    parser.add_argument("--claude-project-root", default=None)
    parser.add_argument("--claude-session-id", default=None)
    parser.add_argument("--claude-command", default=None)
    parser.add_argument("--julia-command", default=None)
    args = parser.parse_args()

    if args.claude_mode == "wake":
        claude_runner = ClaudeCodeJuliaWakeRunner(
            claude_bin=args.claude_bin,
            project_root=args.claude_project_root,
            session_id=args.claude_session_id,
        )
    elif args.claude_mode == "command":
        claude_runner = CommandClaudeJuliaRunner(command=args.claude_command)
    else:
        claude_runner = ScriptedClaudeJuliaRunner()

    julia_runner = JuliaAiAssistantCommandRunner(command=args.julia_command) if args.julia_mode == "assistant" else JuliaAiAssistantHttpRunner() if args.julia_mode == "assistant-http" else JuliaCoreRuntimeRunner()
    report = run_comparison(claude_runner=claude_runner, julia_runner=julia_runner, output_dir=args.output_dir, proposal_path=args.proposal_path)
    print(json.dumps({"overall": report["overall"], "question_count": report["question_count"], "claude_runner": report["claude_runner"], "julia_runner": report["julia_runner"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
