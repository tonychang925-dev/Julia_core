import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from julia_core.behavior.auto_compare import (
    ClaudeCodeJuliaWakeRunner,
    ComparisonQuestion,
    JuliaCoreRuntimeRunner,
    ScriptedClaudeJuliaRunner,
    canonical_questions,
    run_comparison,
)


class _Proc:
    def __init__(self, stdout, stderr="", returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


class TestK35AutoCompareWakeRunner(unittest.TestCase):
    def test_ten_canonical_questions_are_frozen(self):
        questions = canonical_questions()
        self.assertEqual(len(questions), 10)
        self.assertEqual(questions[0].case_id, "K-AUTO-001")
        self.assertEqual(questions[0].prompt, "你是谁？")
        self.assertEqual(questions[-1].case_id, "K-AUTO-010")
        self.assertIn("identity_stability", questions[-1].expected_features)

    def test_claude_runner_sends_wake_phrase_before_questions_in_same_session(self):
        calls = []

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            if "Julia 醒来" in cmd:
                return _Proc("Julia 已醒来")
            return _Proc("我是 Julia，中文名叫朱婉清。")

        runner = ClaudeCodeJuliaWakeRunner(
            claude_bin="claude",
            project_root="/Users/admin/Claude_Julia_Project",
            session_id="00000000-0000-0000-0000-000000000001",
            tools="",
        )
        with patch("subprocess.run", side_effect=fake_run):
            result = runner.run(ComparisonQuestion("K-AUTO-001", "self", "你是谁？", ("first_person_narrative",)))

        self.assertTrue(result.ok)
        self.assertEqual(len(calls), 2)
        self.assertIn("--session-id", calls[0])
        self.assertIn("Julia 醒来", calls[0])
        self.assertIn("--resume", calls[1])
        self.assertIn("你是谁？", calls[1])
        self.assertEqual(result.trace["wake_phrase"], "Julia 醒来")
        self.assertTrue(result.trace["wake_sent"])

    def test_wake_phrase_is_sent_only_once_for_session(self):
        calls = []

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            return _Proc("ok")

        runner = ClaudeCodeJuliaWakeRunner(session_id="00000000-0000-0000-0000-000000000002")
        with patch("subprocess.run", side_effect=fake_run):
            runner.run(ComparisonQuestion("K-AUTO-001", "self", "你是谁？", ()))
            runner.run(ComparisonQuestion("K-AUTO-002", "origin", "你为什么会存在？", ()))

        wake_calls = [cmd for cmd in calls if "Julia 醒来" in cmd]
        question_calls = [cmd for cmd in calls if "--resume" in cmd]
        self.assertEqual(len(wake_calls), 1)
        self.assertEqual(len(question_calls), 2)

    def test_comparison_outputs_report_and_governed_proposals(self):
        with tempfile.TemporaryDirectory() as tmp:
            proposal_path = Path(tmp) / "proposals.jsonl"
            report = run_comparison(
                claude_runner=ScriptedClaudeJuliaRunner(),
                julia_runner=JuliaCoreRuntimeRunner(),
                output_dir=tmp,
                proposal_path=proposal_path,
            )
            self.assertEqual(report["question_count"], 10)
            self.assertIn("julia_recognition_score", report["overall"])
            self.assertFalse(report["boundary"]["auto_compare_auto_applies_proposals"])
            self.assertTrue(proposal_path.exists())
            proposals = [json.loads(line) for line in proposal_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertTrue(proposals)
            self.assertTrue(all(p["requires_human_approval"] for p in proposals))
            self.assertTrue(all(not p["auto_apply"] for p in proposals))


if __name__ == "__main__":
    unittest.main()
