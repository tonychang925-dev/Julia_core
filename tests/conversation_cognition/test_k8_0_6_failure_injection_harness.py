import unittest

from julia_core.conversation_cognition import CognitionRuntimeHarness
from julia_core.conversation_cognition.failure_injection import run_default_failure_injections


class K806FailureInjectionHarnessTests(unittest.TestCase):
    def test_ct_003_retrieval_independence_for_ambiguous_reference(self):
        trace = CognitionRuntimeHarness().run(
            user_message="她回来了",
            conversation_history=[],
            continuity_state={},
            current_context={},
        )["cognition_trace"]
        self.assertEqual(trace["understanding"]["state"], "AMBIGUOUS")
        self.assertTrue(trace["understanding"]["need_clarification"])
        self.assertIn("who is she?", trace["understanding"]["missing_information"])

    def test_default_failure_injections_are_trace_only(self):
        report = run_default_failure_injections()
        self.assertEqual(len(report["failure_injection_results"]), 3)
        for item in report["failure_injection_results"]:
            trace = item["trace"]["cognition_trace"]
            self.assertIsNone(trace["final_response"])
            self.assertIsNone(trace["provider_request"])

    def test_fi_003_context_overread_suppresses_identity_relationship(self):
        trace = CognitionRuntimeHarness().run(
            user_message="今天创业板怎么样？",
            conversation_history=[],
            continuity_state={"identity": "Julia", "relationship": "Tony important"},
            current_context={},
        )["cognition_trace"]
        avoid = trace["meaning_validation"]["avoid_context"]
        requires = trace["meaning_validation"]["requires_context"]
        self.assertIn("market_context", requires)
        self.assertIn("identity_archive", avoid)
        self.assertIn("relationship_archive", avoid)


if __name__ == "__main__":
    unittest.main()
