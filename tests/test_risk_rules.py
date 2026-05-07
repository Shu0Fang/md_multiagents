import unittest

from md_multiagents.tools.risk_rules import assess_risk_rules


class RiskRulesTestCase(unittest.TestCase):
    def test_dlb_maps_to_high(self) -> None:
        result = assess_risk_rules("患者认知波动明显，反复视幻觉，伴帕金森样表现和跌倒。")
        self.assertEqual(result["rule_based_risk"], "high")
        self.assertIn("dlb_high", result["matched_rules"])

    def test_nph_maps_to_high(self) -> None:
        result = assess_risk_rules("近半年步态障碍，尿失禁，认知下降明显。")
        self.assertEqual(result["rule_based_risk"], "high")
        self.assertIn("nph_high", result["matched_rules"])

    def test_contradiction_maps_to_insufficient(self) -> None:
        result = assess_risk_rules("一方面反复迷路、不会使用煤气灶，另一方面又写独居、管理财务、复杂工具性日常生活能力完全正常。")
        self.assertEqual(result["rule_based_risk"], "insufficient")
        self.assertIn("history_conflict_insufficient", result["matched_rules"])

    def test_hypothyroid_pattern_maps_to_low(self) -> None:
        result = assess_risk_rules("乏力、怕冷、便秘，同时诉记忆下降。")
        self.assertEqual(result["rule_based_risk"], "low")
        self.assertIn("hypothyroid_low", result["matched_rules"])

    def test_medication_pattern_maps_to_low(self) -> None:
        result = assess_risk_rules("长期服用阿普唑仑和镇静药，停药后好转，且无红旗。")
        self.assertEqual(result["rule_based_risk"], "low")
        self.assertIn("medication_low", result["matched_rules"])

    def test_moca_boundary_pattern_maps_to_medium(self) -> None:
        result = assess_risk_rules("自述 MoCA 25，持续约1年记忆下降，家属观察到反复忘事，日常生活功能基本保留。")
        self.assertEqual(result["rule_based_risk"], "medium")
        self.assertIn("moca_25_medium", result["matched_rules"])

    def test_mild_forgetfulness_pattern_maps_to_low(self) -> None:
        result = assess_risk_rules("仅偶发轻微健忘和偶发找词困难，功能保留，无红旗。")
        self.assertEqual(result["rule_based_risk"], "low")
        self.assertIn("mild_forgetfulness_low", result["matched_rules"])

    def test_empty_text_maps_to_unknown(self) -> None:
        result = assess_risk_rules("")
        self.assertEqual(result["rule_based_risk"], "unknown")
        self.assertEqual(result["matched_rules"], [])


if __name__ == "__main__":
    unittest.main()