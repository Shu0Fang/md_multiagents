import argparse
import json
import re
import traceback
from pathlib import Path
from typing import Any, Dict, Optional

from md_multiagents.crew import MdMultiagentsCrew


TESTS_PATH = Path("tests") / "ad_eval_cases.json"
DEFAULT_RESULTS_PATH = Path("tests") / "eval_results.json"


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


def run_all_cases(case_id: Optional[str] = None, limit: Optional[int] = None, output: Optional[str] = None, repeat: int = 1):
    if not TESTS_PATH.exists():
        print(f"Test file not found: {TESTS_PATH}")
        return

    with TESTS_PATH.open("r", encoding="utf-8") as f:
        cases = json.load(f)

    # filter by case_id if provided
    if case_id:
        cases = [c for c in cases if (c.get("case_id") or c.get("id")) == case_id]
        if not cases:
            print(f"No test case found with case_id={case_id}")
            return

    # apply limit
    if limit is not None and isinstance(limit, int):
        cases = cases[:limit]

    results_path = Path(output) if output else DEFAULT_RESULTS_PATH

    results = []
    for case in cases:
        case_id_val = case.get("case_id") or case.get("id")
        patient_record = case.get("patient_record", "")
        expected = case.get("expected_risk_level")

        print(f"[CASE_START] case_id={case_id_val}")

        entry: Dict[str, Any] = {
            "case_id": case_id_val,
            "expected_risk_level": expected,
            "predicted_risk_level": None,
            "pass_risk_level": False,
            "raw_output": None,
            "error": None,
        }

        try:
            # allow repeating runs for the same case to measure variability
            repeat_count = int(repeat) if isinstance(repeat, int) and repeat > 0 else 1
            runs = []
            preds = []
            parse_errors = []

            for attempt in range(repeat_count):
                try:
                    print(f"[CASE_RUN] case_id={case_id_val} attempt={attempt+1}/{repeat_count}")
                    # Build a fresh crew per attempt to avoid cross-case/context leakage.
                    crew = MdMultiagentsCrew().crew()
                    output = crew.kickoff(inputs={"patient_record": patient_record})
                    parsed = safe_extract_output(output)
                    raw_out = parsed.get("raw")

                    # try to extract structured risk from parsed json or raw
                    predicted = extract_risk_level(parsed.get("json"), raw_out or "")
                    if predicted is None and isinstance(raw_out, str):
                        raw_obj = parse_json_from_raw_text(raw_out)
                        if isinstance(raw_obj, dict):
                            predicted = raw_obj.get("risk_level")

                    pred_norm = normalize_risk_level(predicted)

                    runs.append({
                        "attempt": attempt + 1,
                        "predicted_raw": predicted,
                        "predicted": pred_norm,
                        "raw_output": raw_out,
                        "error": None,
                    })
                    preds.append(pred_norm)
                except Exception:
                    runs.append({
                        "attempt": attempt + 1,
                        "predicted_raw": None,
                        "predicted": None,
                        "raw_output": None,
                        "error": traceback.format_exc(),
                    })

            # populate summary fields
            entry["runs"] = runs
            entry["predicted_risk_levels"] = preds
            entry["predicted_risk_level"] = preds[0] if preds else None

            exp_norm = normalize_risk_level(expected)
            # consider pass only if all runs match expected (None-safe)
            entry["pass_risk_level"] = bool(preds and exp_norm is not None and all(p == exp_norm for p in preds))

            # collect parse-level errors
            if not preds or any(p is None for p in preds):
                parse_errors.append("predicted_risk_level is None for one or more runs after normalization")
            if parse_errors:
                entry["error"] = "; ".join(parse_errors)

        except Exception:
            entry["error"] = traceback.format_exc()

        results.append(entry)
        print(json.dumps({"case_id": case_id_val, "predicted": entry["predicted_risk_level"], "pass": entry["pass_risk_level"]}, ensure_ascii=False))

    # save results
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with results_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Saved results to {results_path}")


def _parse_args():
    p = argparse.ArgumentParser(description="Run AD eval cases (batch) with optional filters to reduce API usage.")
    p.add_argument("--case-id", dest="case_id", help="Run only the case with this case_id")
    p.add_argument("--limit", dest="limit", type=int, help="Limit to first N cases")
    p.add_argument("--output", dest="output", help="Output results file path (default: tests/eval_results.json)")
    p.add_argument("--repeat", dest="repeat", type=int, default=1, help="Repeat each case N times to measure output variability")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_all_cases(case_id=args.case_id, limit=args.limit, output=args.output, repeat=args.repeat)
