"""Extract structured JSON from free-text LLM responses.

Adapted from asrp.science-llm/app/images/parsing.py.
"""

import json
import logging
import re

logger = logging.getLogger(__name__)

_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*\n?(.*?)\n?\s*```", re.DOTALL)

STAGE_NORMALIZE = {
    "none": "none",
    "no_clots": "none",
    "no_fibrin": "none",
    "early_fibrin": "early_fibrin",
    "early_fibrin_formation": "early_fibrin",
    "early": "early_fibrin",
    "partial_clot": "partial_clot",
    "partial": "partial_clot",
    "partially_formed": "partial_clot",
    "full_coagulation": "full_coagulation",
    "full": "full_coagulation",
    "mature": "full_coagulation",
    "lysis": "lysis",
    "fibrinolysis": "lysis",
    "dissolving": "lysis",
}


def extract_json(text: str) -> dict | None:
    """Extract and parse the first JSON object from LLM response text."""
    raw = _find_json_string(text)
    if raw is None:
        return None
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def extract_single_structured(text: str) -> dict | None:
    """Extract single-photo structured analysis from response text."""
    data = extract_json(text)
    if data is None:
        return None
    return _normalize_single(data)


def extract_comparative_structured(text: str) -> dict | None:
    """Extract comparative analysis from response text."""
    data = extract_json(text)
    if data is None:
        return None
    return _normalize_comparative(data)


def _find_json_string(text: str) -> str | None:
    match = _JSON_BLOCK_RE.search(text)
    if match:
        return match.group(1).strip()

    brace_start = text.find("{")
    if brace_start == -1:
        return None

    depth = 0
    for i in range(brace_start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[brace_start : i + 1]
    return None


def _normalize_stage(val: str | None) -> str | None:
    if not val or not isinstance(val, str):
        return val
    raw = val.strip().lower().replace(" ", "_").replace("-", "_")
    return STAGE_NORMALIZE.get(raw, raw)


def _normalize_plasma(plasma_data: dict) -> dict:
    result = {}
    for key in ("color", "transparency", "notes"):
        v = plasma_data.get(key)
        if isinstance(v, str) and v.strip() and v.strip().lower() != "null":
            result[key] = v.strip()
    v = plasma_data.get("clots")
    if isinstance(v, bool):
        result["clots"] = v
    elif isinstance(v, str):
        result["clots"] = v.strip().lower() in ("true", "yes", "1")
    v = plasma_data.get("clot_stage")
    if isinstance(v, str) and v.strip() and v.strip().lower() != "null":
        result["clot_stage"] = _normalize_stage(v)
    return result


def _normalize_single(data: dict) -> dict | None:
    result = {}

    for key in ("scene", "view"):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            result[key] = val.strip()

    val = data.get("sample_count")
    if isinstance(val, int):
        result["sample_count"] = val
    elif isinstance(val, str) and val.isdigit():
        result["sample_count"] = int(val)

    plasma_data = data.get("plasma")
    if isinstance(plasma_data, dict):
        plasma = _normalize_plasma(plasma_data)
        if plasma:
            result["plasma"] = plasma

    return result if result else None


def _normalize_comparative(data: dict) -> dict | None:
    result = {}

    for channel in ("control", "ch19", "ch21"):
        ch_data = data.get(channel)
        if isinstance(ch_data, dict):
            result[channel] = _normalize_plasma(ch_data)

    for key in ("most_coagulated", "least_coagulated", "overall_difference", "comparison_notes"):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            result[key] = val.strip()

    return result if result else None


# Blinded label → real channel
_BLIND_TO_CHANNEL = {
    "sample_a": "control", "a": "control",
    "sample_b": "ch19", "b": "ch19",
    "sample_c": "ch21", "c": "ch21",
}


def extract_blinded_structured(text: str) -> dict | None:
    """Extract blinded analysis and remap A/B/C → control/ch19/ch21."""
    data = extract_json(text)
    if data is None:
        return None
    return _normalize_blinded(data)


def _normalize_blinded(data: dict) -> dict | None:
    result = {}

    # Remap sample_a/b/c → control/ch19/ch21
    for blind_key, real_key in (
        ("sample_a", "control"), ("sample_b", "ch19"), ("sample_c", "ch21"),
    ):
        ch_data = data.get(blind_key)
        if isinstance(ch_data, dict):
            result[real_key] = _normalize_plasma(ch_data)

    # Remap most/least_coagulated values
    for key in ("most_coagulated", "least_coagulated"):
        val = data.get(key)
        if isinstance(val, str):
            normalized = val.strip().lower().replace(" ", "_")
            result[key] = _BLIND_TO_CHANNEL.get(normalized, val.strip())

    for key in ("overall_difference", "comparison_notes"):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            result[key] = val.strip()

    return result if result else None
