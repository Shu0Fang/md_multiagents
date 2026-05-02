import json
import traceback
from pathlib import Path
from typing import Any, Dict

from md_multiagents.crew import MdMultiagentsCrew


TESTS_PATH = Path("tests") / "ad_eval_cases.json"
RESULTS_PATH = Path("tests") / "eval_results.json"


def safe_extract_output(output: Any) -> Dict[str, Any]:
    """Try various ways to turn CrewOutput into a dict and extract raw text."""
    result: Dict[str, Any] = {"raw": None, "json": None}

    # 1) If object has .raw
    try:
        raw = getattr(output, "raw", None)
        if raw is None and hasattr(output, "pydantic"):
            # some Crew outputs expose pydantic models
            raw = getattr(output.pydantic, "json", None)
        if raw is None and hasattr(output, "json_dict"):
            raw = output.json_dict
        if raw is None:
            raw = output
        # convert to string where appropriate
        result["raw"] = raw if isinstance(raw, str) else json.dumps(raw, ensure_ascii=False, default=str)
    except Exception:
        result["raw"] = str(output)

    # 2) Try to parse raw as JSON
    try:
        parsed = json.loads(result["raw"]) if isinstance(result["raw"], str) else None
        result["json"] = parsed
    except Exception:
        result["json"] = None

    return result


def extract_risk_level(parsed_json: Any, raw_text: str) -> Any:
    """Try multiple heuristics to find a risk level in structured or free text output."""
    # Look in structured JSON first
    if isinstance(parsed_json, dict):
        for key in ("risk_level", "risk", "predicted_risk", "final_risk"):
            if key in parsed_json:
                return parsed_json[key]
        # nested search (one level)
        for v in parsed_json.values():
            if isinstance(v, dict):
                for key in ("risk_level", "risk", "predicted_risk", "final_risk"):
                    if key in v:
                        return v[key]

    # Fall back to simple text matching
    if isinstance(raw_text, str):
        low_words = ["低", "low"]
        med_words = ["中", "moderate", "medium"]
        high_words = ["高", "high"]
        if any(w in raw_text for w in high_words):
            return "high"
        if any(w in raw_text for w in med_words):
            return "medium"
        if any(w in raw_text for w in low_words):
            return "low"

    return None


def run_all_cases():
    if not TESTS_PATH.exists():
        print(f"Test file not found: {TESTS_PATH}")
        return

    with TESTS_PATH.open("r", encoding="utf-8") as f:
        cases = json.load(f)

    crew = MdMultiagentsCrew().crew()

    results = []
    for case in cases:
        case_id = case.get("case_id") or case.get("id")
        patient_record = case.get("patient_record", "")
        expected = case.get("expected_risk_level")

        entry: Dict[str, Any] = {
            "case_id": case_id,
            "expected_risk_level": expected,
            "predicted_risk_level": None,
            "pass_risk_level": False,
            "raw_output": None,
            "error": None,
        }

        try:
            output = crew.kickoff(inputs={"patient_record": patient_record})
            parsed = safe_extract_output(output)
            entry["raw_output"] = parsed.get("raw")

            predicted = extract_risk_level(parsed.get("json"), parsed.get("raw") or "")
            # normalize some expected values (中文/英文)
            if isinstance(expected, str):
                exp_norm = expected.strip().lower()
                map_norm = {"低": "low", "中": "medium", "高": "high", "信息不足": "insufficient", "信息不足": "insufficient"}
                exp_norm = map_norm.get(exp_norm, exp_norm)
            else:
                exp_norm = expected

            if isinstance(predicted, str):
                pred_norm = predicted.strip().lower()
            else:
                pred_norm = predicted

            entry["predicted_risk_level"] = pred_norm
            # decide pass if both are not None and equal (allow simple synonyms)
            entry["pass_risk_level"] = bool(pred_norm is not None and exp_norm is not None and pred_norm == exp_norm)

        except Exception as e:
            entry["error"] = traceback.format_exc()

        results.append(entry)
        print(json.dumps({"case_id": case_id, "predicted": entry["predicted_risk_level"], "pass": entry["pass_risk_level"]}, ensure_ascii=False))

    # save results
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS_PATH.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Saved results to {RESULTS_PATH}")


if __name__ == "__main__":
    run_all_cases()
