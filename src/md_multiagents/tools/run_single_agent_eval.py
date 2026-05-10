import argparse
import json
import os
import traceback
from pathlib import Path
from typing import Any, Dict, Optional

from crewai import Agent, LLM

from md_multiagents.tools.run_eval_cases import (
    build_summary,
    extract_risk_level,
    normalize_risk_level,
    parse_json_from_raw_text,
    safe_extract_output,
)


DEFAULT_CASES_PATH = Path("tests") / "ad_eval_cases.json"
DEFAULT_RESULTS_PATH = Path("tests") / "eval_results_single_agent.json"
DEFAULT_SUMMARY_PATH = Path("tests") / "eval_summary_single_agent.json"


SINGLE_AGENT_PROMPT = """你是一个用于 AD / 认知下降风险评估的单 agent baseline。

请只基于患者病历原文做判断，不要调用任何工具，不要输出 markdown，不要解释推理过程。
必须输出单个 JSON object，且至少包含以下字段：
- final_judgment
- risk_level
- recommended_tests
- next_steps
- safety_notes

其中 risk_level 只能是 high / medium / low / insufficient 四者之一。
如果证据不足，请明确输出 insufficient。
如果证据不明确但存在中风险线索，请输出 medium。
如果是正常老化或可逆因素较明确且无红旗，请输出 low。
如果存在明确高危红旗，请输出 high。

患者病历原文：
{patient_record}
"""


def _build_llm() -> LLM:
    model_name = os.getenv("MODEL") or os.getenv("OPENAI_MODEL_NAME") or "deepseek-chat"
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_API_BASE") or os.getenv("OPENAI_BASE_URL")

    return LLM(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=0,
    )


def _build_agent() -> Agent:
    return Agent(
        role="AD Risk Baseline Analyst",
        goal="Assess AD / cognitive decline risk from a single patient record using a compact JSON output.",
        backstory=(
            "You are a strict clinical evaluation baseline that follows risk labels exactly and returns JSON only."
        ),
        llm=_build_llm(),
        verbose=False,
        respect_context_window=True,
    )


def _build_prompt(patient_record: str) -> str:
    return SINGLE_AGENT_PROMPT.format(patient_record=patient_record)


def _run_single_case(case: Dict[str, Any]) -> Dict[str, Any]:
    case_id_val = case.get("case_id") or case.get("id")
    patient_record = case.get("patient_record", "")
    expected = case.get("expected_risk_level")

    entry: Dict[str, Any] = {
        "case_id": case_id_val,
        "expected_risk_level": expected,
        "predicted_risk_level": None,
        "pass_risk_level": False,
        "raw_output": None,
        "error": None,
    }

    try:
        agent = _build_agent()
        result = agent.kickoff(_build_prompt(patient_record))
        parsed = safe_extract_output(result)
        raw_out = parsed.get("raw")

        predicted = extract_risk_level(parsed.get("json"), raw_out or "")
        if predicted is None and isinstance(raw_out, str):
            raw_obj = parse_json_from_raw_text(raw_out)
            if isinstance(raw_obj, dict):
                predicted = raw_obj.get("risk_level")

        pred_norm = normalize_risk_level(predicted)
        entry["predicted_risk_level"] = pred_norm
        entry["raw_output"] = raw_out
        entry["pass_risk_level"] = bool(pred_norm is not None and normalize_risk_level(expected) == pred_norm)

        if pred_norm is None:
            entry["error"] = "predicted_risk_level is None after normalization"

    except Exception:
        entry["error"] = traceback.format_exc()

    return entry


def run_all_cases(
    case_id: Optional[str] = None,
    limit: Optional[int] = None,
    output: Optional[str] = None,
    summary_output: Optional[str] = None,
    cases_file: Optional[str] = None,
):
    cases_path = Path(cases_file) if cases_file else DEFAULT_CASES_PATH

    if not cases_path.exists():
        print(f"Test file not found: {cases_path}")
        return

    with cases_path.open("r", encoding="utf-8") as f:
        cases = json.load(f)

    if case_id:
        cases = [c for c in cases if (c.get("case_id") or c.get("id")) == case_id]
        if not cases:
            print(f"No test case found with case_id={case_id}")
            return

    if limit is not None and isinstance(limit, int):
        cases = cases[:limit]

    results_path = Path(output) if output else DEFAULT_RESULTS_PATH
    summary_path = Path(summary_output) if summary_output else DEFAULT_SUMMARY_PATH

    results = []
    for case in cases:
        case_id_val = case.get("case_id") or case.get("id")
        print(f"[CASE_START] case_id={case_id_val}")
        entry = _run_single_case(case)
        results.append(entry)
        print(json.dumps({"case_id": case_id_val, "predicted": entry["predicted_risk_level"], "pass": entry["pass_risk_level"]}, ensure_ascii=False))

    results_path.parent.mkdir(parents=True, exist_ok=True)
    with results_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    summary = build_summary(results)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"Saved results to {results_path}")
    print(f"Saved summary to {summary_path}")
    print(
        f"Summary: total={summary['total']}, passed={summary['passed']}, accuracy={summary['accuracy']:.3f}"
    )


def _parse_args():
    p = argparse.ArgumentParser(description="Run AD eval cases with a single-agent baseline.")
    p.add_argument("--case-id", dest="case_id", help="Run only the case with this case_id")
    p.add_argument("--limit", dest="limit", type=int, help="Limit to first N cases")
    p.add_argument(
        "--cases-file",
        dest="cases_file",
        help="Input cases JSON file path (default: tests/ad_eval_cases.json)",
    )
    p.add_argument("--output", dest="output", help="Output results file path (default: tests/eval_results_single_agent.json)")
    p.add_argument(
        "--summary-output",
        dest="summary_output",
        help="Summary output file path (default: tests/eval_summary_single_agent.json)",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_all_cases(
        case_id=args.case_id,
        limit=args.limit,
        output=args.output,
        summary_output=args.summary_output,
        cases_file=args.cases_file,
    )