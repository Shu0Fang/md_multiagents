import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from md_multiagents.tools import run_eval_cases


class _FakeOutput:
    def __init__(self, raw: str) -> None:
        self.raw = raw


class _FakeCrew:
    def kickoff(self, inputs):
        return _FakeOutput('{"risk_level": "high"}')


class _FakeCrewFactory:
    def crew(self):
        return _FakeCrew()


class RunEvalCasesRuleIntegrationTestCase(unittest.TestCase):
    def test_run_all_cases_adds_rule_fields_without_affecting_pass_logic(self) -> None:
        case = {
            "case_id": "CASE-1",
            "patient_record": "72岁，半年内认知波动、反复视幻觉，伴帕金森样动作迟缓和偶有跌倒。",
            "expected_risk_level": "high",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            cases_file = tmpdir_path / "cases.json"
            results_file = tmpdir_path / "results.json"
            summary_file = tmpdir_path / "summary.json"

            cases_file.write_text(json.dumps([case], ensure_ascii=False), encoding="utf-8")

            with patch.object(run_eval_cases, "MdMultiagentsCrew", new=_FakeCrewFactory):
                run_eval_cases.run_all_cases(
                    cases_file=str(cases_file),
                    output=str(results_file),
                    summary_output=str(summary_file),
                    repeat=1,
                    use_cache=False,
                    force_cache=False,
                )

            results = json.loads(results_file.read_text(encoding="utf-8"))
            summary = json.loads(summary_file.read_text(encoding="utf-8"))

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["rule_based_risk"], "high")
        self.assertIn("dlb_high", results[0]["matched_rules"])
        self.assertEqual(results[0]["predicted_risk_level"], "high")
        self.assertTrue(results[0]["pass_risk_level"])
        self.assertEqual(summary["rule_agree_with_expected_count"], 1)
        self.assertEqual(summary["rule_agree_with_llm_count"], 1)
        self.assertEqual(summary["rule_unknown_count"], 0)

    def test_build_summary_counts_unknown_rule_results(self) -> None:
        summary = run_eval_cases.build_summary(
            [
                {
                    "case_id": "CASE-2",
                    "expected_risk_level": "low",
                    "predicted_risk_level": "low",
                    "pass_risk_level": True,
                    "rule_based_risk": "unknown",
                    "matched_rules": [],
                }
            ]
        )

        self.assertEqual(summary["rule_unknown_count"], 1)
        self.assertEqual(summary["rule_agree_with_expected_count"], 0)
        self.assertEqual(summary["rule_agree_with_llm_count"], 0)


if __name__ == "__main__":
    unittest.main()