"""Lightweight rule-based risk helper for AD evaluation.

This module is intentionally independent from the LLM workflow.
It only provides a coarse heuristic signal that can be used for
debugging, triage, or comparison against model outputs.
"""

from __future__ import annotations

import argparse
from typing import Any


HIGH = "high"
MEDIUM = "medium"
LOW = "low"
INSUFFICIENT = "insufficient"
UNKNOWN = "unknown"


def _normalize_text(text: str | None) -> str:
    if not text:
        return ""
    normalized = text.lower()
    normalized = normalized.replace("\u3000", " ")
    for char in ("\n", "\r", "\t"):
        normalized = normalized.replace(char, " ")
    return normalized


def _contains_any(text: str, patterns: list[str]) -> bool:
    return any(pattern in text for pattern in patterns)


def _has_hypothyroid_pattern(text: str) -> bool:
    core_symptoms = ["乏力", "怕冷", "便秘"]
    memory_cues = ["记忆下降", "记性差", "记忆变差", "记忆不好"]
    return all(pattern in text for pattern in core_symptoms) and _contains_any(text, memory_cues)


def _has_mild_forgetfulness_pattern(text: str) -> bool:
    mild_cues = ["偶发轻微健忘", "偶尔忘事", "偶发找词困难", "主观记忆变慢", "偶尔想不起来"]
    preserved_function_cues = ["功能保留", "日常生活功能完全保留", "生活自理", "独立生活", "可独立", "adl正常"]
    no_red_flag_cues = ["无红旗", "无定向障碍", "无迷路", "无功能下降", "无神经系统体征", "无行为精神症状"]
    return _contains_any(text, mild_cues) and _contains_any(text, preserved_function_cues) and _contains_any(text, no_red_flag_cues)


def _has_dl_b_pattern(text: str) -> bool:
    fluctuation_cues = ["波动性认知", "认知波动", "时好时坏", "忽好忽坏"]
    hallucination_cues = ["幻视", "视幻觉", "反复视幻觉"]
    parkinson_cues = ["帕金森", "帕金森样", "运动迟缓", "动作迟缓", "肌强直", "震颤", "跌倒", "反复跌倒"]
    rbd_cues = ["rbd", "rem睡眠行为障碍", "rem 睡眠行为障碍", "梦中拳打脚踢", "梦境行为异常"]
    return _contains_any(text, fluctuation_cues) and _contains_any(text, hallucination_cues) and (
        _contains_any(text, parkinson_cues) or _contains_any(text, rbd_cues)
    )


def _has_nph_pattern(text: str) -> bool:
    gait_cues = ["步态障碍", "步态异常", "走路不稳", "磁性步态", "拖步", "小碎步"]
    urinary_cues = ["尿急", "尿失禁", "尿频", "尿潴留", "夜尿"]
    cognition_cues = ["认知下降", "记忆下降", "认知变差", "痴呆", "健忘"]
    return _contains_any(text, gait_cues) and _contains_any(text, urinary_cues) and _contains_any(text, cognition_cues)


def _has_contradiction_pattern(text: str) -> bool:
    impairment_cues = [
        "明显生活功能下降",
        "不会使用煤气灶",
        "反复迷路",
        "需要照顾",
        "不能独立",
        "生活不能自理",
        "adl下降",
        "iadl下降",
    ]
    independence_cues = [
        "独居",
        "管理财务",
        "复杂工具性日常生活能力完全正常",
        "复杂工具性日常生活正常",
        "日常生活完全正常",
        "独立生活",
        "仍可独立",
    ]
    return _contains_any(text, impairment_cues) and _contains_any(text, independence_cues)


def _has_medication_pattern(text: str) -> bool:
    medication_cues = [
        "苯二氮",
        "苯二氮平",
        "地西泮",
        "阿普唑仑",
        "劳拉西泮",
        "艾司唑仑",
        "氯硝西泮",
        "唑吡坦",
        "佐匹克隆",
        "安眠药",
        "镇静药",
        "镇静",
        "抗胆碱",
        "苯海拉明",
        "阿米替林",
    ]
    improvement_cues = ["停药后好转", "减停后改善", "停用后改善", "停药改善", "减药后改善"]
    return _contains_any(text, medication_cues) and _contains_any(text, improvement_cues)


def _has_moca_medium_pattern(text: str) -> bool:
    moca_cues = ["moca 25", "moca25", "mo ca 25"]
    mmse_boundary_cues = ["mmse边界异常", "mmse 轻度异常", "mmse轻度异常", "mmse 边界异常", "mmse偏低", "mmse 稍低"]
    duration_cues = ["持续约1年", "持续 1 年", "1年", "一年", "更久"]
    memory_decline_cues = ["记忆下降", "记忆变差", "持续记忆下降", "反复忘事", "忘放东西"]
    function_preserved_cues = ["功能保留", "日常生活基本保留", "日常生活功能基本保留", "生活自理", "独立生活", "仍可独立"]
    boundary_match = _contains_any(text, moca_cues) or _contains_any(text, mmse_boundary_cues)
    return boundary_match and _contains_any(text, duration_cues) and _contains_any(text, memory_decline_cues) and _contains_any(
        text, function_preserved_cues
    )


def assess_risk_rules(patient_record: str) -> dict[str, Any]:
    """Return a coarse rule-based risk label and the matched rule names."""
    text = _normalize_text(patient_record)

    if not text.strip():
        return {"rule_based_risk": UNKNOWN, "matched_rules": []}

    matched_rules: list[str] = []

    if _has_dl_b_pattern(text):
        matched_rules.append("dlb_high")

    if _has_nph_pattern(text):
        matched_rules.append("nph_high")

    if _has_contradiction_pattern(text):
        matched_rules.append("history_conflict_insufficient")

    if _has_moca_medium_pattern(text):
        matched_rules.append("moca_25_medium")

    if _has_hypothyroid_pattern(text):
        matched_rules.append("hypothyroid_low")

    if _has_medication_pattern(text):
        matched_rules.append("medication_low")

    if _has_mild_forgetfulness_pattern(text):
        matched_rules.append("mild_forgetfulness_low")

    if "dlb_high" in matched_rules or "nph_high" in matched_rules:
        return {"rule_based_risk": HIGH, "matched_rules": matched_rules}

    if "history_conflict_insufficient" in matched_rules:
        return {"rule_based_risk": INSUFFICIENT, "matched_rules": matched_rules}

    if "moca_25_medium" in matched_rules:
        return {"rule_based_risk": MEDIUM, "matched_rules": matched_rules}

    if "hypothyroid_low" in matched_rules or "medication_low" in matched_rules or "mild_forgetfulness_low" in matched_rules:
        return {"rule_based_risk": LOW, "matched_rules": matched_rules}

    return {"rule_based_risk": UNKNOWN, "matched_rules": matched_rules}


def _demo_cases() -> list[tuple[str, str]]:
    return [
        (
            "DLB example",
            "患者认知波动明显，反复视幻觉，伴帕金森样表现和跌倒。",
        ),
        (
            "NPH example",
            "近半年步态障碍，尿失禁，认知下降明显。",
        ),
        (
            "Contradiction example",
            "一方面反复迷路、不会使用煤气灶，另一方面又写独居、管理财务、复杂工具性日常生活能力完全正常。",
        ),
        (
            "Hypothyroid example",
            "乏力、怕冷、便秘，同时诉记忆下降。",
        ),
        (
            "Medication example",
            "长期服用阿普唑仑和镇静药，停药后好转，且无红旗。",
        ),
        (
            "MoCA example",
            "自述 MoCA 25，持续约1年记忆下降，家属观察到反复忘事，日常生活功能基本保留。",
        ),
        (
            "Mild forgetfulness example",
            "仅偶发轻微健忘和偶发找词困难，功能保留，无红旗。",
        ),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run lightweight AD risk rules on sample text.")
    parser.add_argument("patient_record", nargs="?", help="Patient record text to evaluate.")
    parser.add_argument("--demo", action="store_true", help="Print built-in demo cases.")
    args = parser.parse_args(argv)

    if args.demo:
        for name, sample in _demo_cases():
            result = assess_risk_rules(sample)
            print(f"[{name}] {result}")
        return 0

    if not args.patient_record:
        parser.print_help()
        return 1

    result = assess_risk_rules(args.patient_record)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())