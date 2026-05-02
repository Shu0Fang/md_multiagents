import json
import re
import traceback
from pathlib import Path
from typing import Any, Dict

from md_multiagents.crew import MdMultiagentsCrew


TESTS_PATH = Path("tests") / "ad_eval_cases.json"
RESULTS_PATH = Path("tests") / "eval_results.json"


_PUNCTUATION_TO_STRIP = "\"'`：:，,。.;；!！?？()（）[]{}"


def normalize_risk_level(value: Any) -> str | None:
    """Normalize risk level strings across zh/en formats for stable comparison."""
    if value is None:
        return None

    text = str(value).strip().strip(_PUNCTUATION_TO_STRIP).lower()
    text = re.sub(r"\s+", "", text)

    mapping = {
        "低": "low",
        "low": "low",
        "中": "medium",
        "中等": "medium",
        "medium": "medium",
        "moderate": "medium",
        "高": "high",
        "high": "high",
        "信息不足": "insufficient",
        "不足": "insufficient",
        "insufficient": "insufficient",
    }
    return mapping.get(text, text or None)


def parse_json_from_raw_text(raw_text: str) -> Dict[str, Any] | None:
    """Parse JSON from raw text, supporting fenced code blocks and embedded object text."""
    if not isinstance(raw_text, str) or not raw_text.strip():
        return None

    text = raw_text.strip()

    # direct JSON parse
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    # markdown fenced JSON block
    fence_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text, re.IGNORECASE)
    if fence_match:
        try:
            obj = json.loads(fence_match.group(1))
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass

    # fallback: first JSON-looking object substring
    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last != -1 and first < last:
        candidate = text[first : last + 1]
        try:
            obj = json.loads(candidate)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass

    return None


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

    # 2) Try to parse raw as JSON (with robust fallback)
    try:
        parsed = parse_json_from_raw_text(result["raw"]) if isinstance(result["raw"], str) else None
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

            parse_errors = []

            # 1) structured result first
            predicted = extract_risk_level(parsed.get("json"), parsed.get("raw") or "")

            # 2) explicitly try extracting risk_level from raw_output JSON
            if predicted is None and isinstance(entry["raw_output"], str):
                raw_obj = parse_json_from_raw_text(entry["raw_output"])
                if isinstance(raw_obj, dict):
                    predicted = raw_obj.get("risk_level")
                else:
                    parse_errors.append("Unable to parse raw_output as JSON for risk_level extraction")

            exp_norm = normalize_risk_level(expected)
            pred_norm = normalize_risk_level(predicted)

            entry["predicted_risk_level"] = pred_norm
            # decide pass if both are not None and equal (allow simple synonyms)
            entry["pass_risk_level"] = bool(pred_norm is not None and exp_norm is not None and pred_norm == exp_norm)

            if pred_norm is None:
                parse_errors.append("predicted_risk_level is None after normalization")
            if parse_errors:
                entry["error"] = "; ".join(parse_errors)

        except Exception:
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
