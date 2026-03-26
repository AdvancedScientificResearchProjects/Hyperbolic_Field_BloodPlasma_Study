#!/usr/bin/env python3
"""Direct Gemini API calls without langchain retries.

Avoids langchain's automatic retry mechanism which burns quota (5+ retries per call).
Makes exactly 1 API call per set, with manual delay between sets.
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.environ.get("GOOGLE_API_KEY", "")
BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


def encode_photo(photo_path: Path) -> str:
    """Encode photo at original resolution — let the API handle resizing."""
    return base64.b64encode(photo_path.read_bytes()).decode()


def call_gemini(model: str, prompt: str, image_b64_list: list[str]) -> dict:
    """Single Gemini API call. No retries."""
    parts = [{"text": prompt}]
    for b64 in image_b64_list:
        parts.append({"inline_data": {"mime_type": "image/jpeg", "data": b64}})

    data = json.dumps({"contents": [{"parts": parts}]}).encode()
    url = f"{BASE_URL}/models/{model}:generateContent?key={API_KEY}"

    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    start = time.monotonic()
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        result = json.loads(resp.read())
        elapsed = int((time.monotonic() - start) * 1000)

        if "candidates" in result:
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            return {"ok": True, "text": text, "latency_ms": elapsed}
        else:
            return {"ok": False, "error": str(result), "latency_ms": elapsed}
    except urllib.error.HTTPError as e:
        elapsed = int((time.monotonic() - start) * 1000)
        body = e.read().decode()
        if "RESOURCE_EXHAUSTED" in body:
            return {"ok": False, "error": "QUOTA_EXHAUSTED", "latency_ms": elapsed}
        return {"ok": False, "error": f"HTTP {e.code}: {body[:200]}", "latency_ms": elapsed}
    except Exception as e:
        elapsed = int((time.monotonic() - start) * 1000)
        return {"ok": False, "error": str(e), "latency_ms": elapsed}


def load_comparative_prompt(blinded: bool) -> str:
    """Load prompt from the existing prompts module."""
    sys.path.insert(0, str(PROJECT_ROOT))
    from scripts.llm_analysis.prompts import COMPARATIVE_PROMPT, COMPARATIVE_PROMPT_BLINDED
    return COMPARATIVE_PROMPT_BLINDED if blinded else COMPARATIVE_PROMPT


def load_multi_tube_prompt(blinded: bool) -> str:
    sys.path.insert(0, str(PROJECT_ROOT))
    from scripts.llm_analysis.prompts import MULTI_TUBE_PROMPT_TEMPLATE, MULTI_TUBE_PROMPT_BLINDED_TEMPLATE
    return MULTI_TUBE_PROMPT_BLINDED_TEMPLATE if blinded else MULTI_TUBE_PROMPT_TEMPLATE


def run_comparative(model: str, output_dir: Path, blinded: bool, delay: int, resume: bool):
    sys.path.insert(0, str(PROJECT_ROOT))
    from scripts.llm_analysis.data import load_photos, build_comparison_sets, BLIND_MAP
    from scripts.llm_analysis.parsing import extract_comparative_structured, extract_blinded_structured

    prompt = load_comparative_prompt(blinded)
    parse_fn = extract_blinded_structured if blinded else extract_comparative_structured

    photos = load_photos()
    comp_sets = build_comparison_sets(photos)
    print(f"Built {len(comp_sets)} comparison sets")

    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = output_dir / "results.json"
    progress_path = output_dir / ".progress.json"

    done_keys = set()
    all_results = []
    if resume and results_path.exists():
        existing = json.loads(results_path.read_text())
        all_results = existing.get("comparisons", [])
        if progress_path.exists():
            done_keys = set(json.loads(progress_path.read_text()))
        print(f"Resuming: {len(done_keys)} done, {len(all_results)} results")

    for i, cs in enumerate(comp_sets):
        key = f"{cs.patient}_{cs.control.filename}_{cs.ch19.filename}_{cs.ch21.filename}"
        if key in done_keys:
            continue

        print(f"[{i+1}/{len(comp_sets)}] Patient {cs.patient}: "
              f"ctrl={cs.control.filename} ch19={cs.ch19.filename} ch21={cs.ch21.filename}")

        images = [
            encode_photo(cs.control.jpg_path),
            encode_photo(cs.ch19.jpg_path),
            encode_photo(cs.ch21.jpg_path),
        ]

        result = call_gemini(model, prompt, images)
        print(f"  {result['latency_ms']}ms - {'OK' if result['ok'] else result['error']}")

        entry = {
            "patient": cs.patient,
            "blinded": blinded,
            "blind_map": BLIND_MAP if blinded else None,
            "photos": {
                "control": {"filename": cs.control.filename, "sample_ids": cs.control.samples_shown},
                "ch19": {"filename": cs.ch19.filename, "sample_ids": cs.ch19.samples_shown},
                "ch21": {"filename": cs.ch21.filename, "sample_ids": cs.ch21.samples_shown},
            },
            "providers": {
                "google": {
                    "latency_ms": result["latency_ms"],
                    "error": None if result["ok"] else result["error"],
                    "raw": result.get("text"),
                    "structured": parse_fn(result["text"]) if result["ok"] else None,
                    "fallback": False,
                }
            },
        }
        all_results.append(entry)
        done_keys.add(key)

        # Save incrementally
        mode = "comparative_blinded" if blinded else "comparative"
        output = {
            "metadata": {
                "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "mode": mode,
                "blinded": blinded,
                "blind_map": BLIND_MAP if blinded else None,
                "providers": ["google"],
                "total_comparisons": len(all_results),
                "model": model,
            },
            "comparisons": all_results,
        }
        results_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
        progress_path.write_text(json.dumps(sorted(done_keys), indent=2))

        if not result["ok"] and result.get("error") == "QUOTA_EXHAUSTED":
            print("QUOTA EXHAUSTED — stopping")
            break

        time.sleep(delay)

    ok = sum(1 for r in all_results if r["providers"]["google"]["error"] is None)
    print(f"\nDone: {ok}/{len(all_results)} OK")


def run_multi_tube(model: str, output_dir: Path, blinded: bool, delay: int, resume: bool):
    sys.path.insert(0, str(PROJECT_ROOT))
    from scripts.llm_analysis.data import load_photos, build_multi_tube_sets, blind_caption, BLIND_MAP
    from scripts.llm_analysis.parsing import extract_comparative_structured, extract_blinded_structured

    prompt = load_multi_tube_prompt(blinded)
    parse_fn = extract_blinded_structured if blinded else extract_comparative_structured

    photos = load_photos()
    mt_sets = build_multi_tube_sets(photos)
    print(f"Built {len(mt_sets)} multi-tube sets")

    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = output_dir / "results.json"
    progress_path = output_dir / ".progress.json"

    done_keys = set()
    all_results = []
    if resume and results_path.exists():
        existing = json.loads(results_path.read_text())
        all_results = existing.get("comparisons", [])
        if progress_path.exists():
            done_keys = set(json.loads(progress_path.read_text()))
        print(f"Resuming: {len(done_keys)} done")

    for i, mts in enumerate(mt_sets):
        key = f"{mts.patient}_{mts.photo.filename}"
        if key in done_keys:
            continue

        caption = blind_caption(mts.caption) if blinded else mts.caption
        print(f"[{i+1}/{len(mt_sets)}] Patient {mts.patient}: "
              f"{mts.photo.filename} — \"{caption}\"")

        images = [encode_photo(mts.photo.jpg_path)]

        formatted_prompt = prompt.format(caption=caption)

        result = call_gemini(model, formatted_prompt, images)
        print(f"  {result['latency_ms']}ms - {'OK' if result['ok'] else result['error']}")

        entry = {
            "patient": mts.patient,
            "blinded": blinded,
            "blind_map": BLIND_MAP if blinded else None,
            "photo": {
                "filename": mts.photo.filename,
                "channels": mts.photo.channels,
                "arrangement": caption,
            },
            "providers": {
                "google": {
                    "latency_ms": result["latency_ms"],
                    "error": None if result["ok"] else result["error"],
                    "raw": result.get("text"),
                    "structured": parse_fn(result["text"]) if result["ok"] else None,
                    "fallback": False,
                }
            },
        }
        all_results.append(entry)
        done_keys.add(key)

        mode = "multi_tube_blinded" if blinded else "multi_tube"
        output = {
            "metadata": {
                "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "mode": mode,
                "blinded": blinded,
                "blind_map": BLIND_MAP if blinded else None,
                "providers": ["google"],
                "total_comparisons": len(all_results),
                "model": model,
            },
            "comparisons": all_results,
        }
        results_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
        progress_path.write_text(json.dumps(sorted(done_keys), indent=2))

        if result.get("error") == "QUOTA_EXHAUSTED":
            print("QUOTA EXHAUSTED — stopping")
            break

        time.sleep(delay)

    ok = sum(1 for r in all_results if r["providers"]["google"]["error"] is None)
    print(f"\nDone: {ok}/{len(all_results)} OK")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Direct Gemini API calls")
    parser.add_argument("--mode", required=True, choices=["comparative", "multi_tube"])
    parser.add_argument("--model", default="gemini-2.5-flash-lite")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--blinded", action="store_true")
    parser.add_argument("--delay", type=int, default=5)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    output_dir = PROJECT_ROOT / args.output_dir

    if args.mode == "comparative":
        run_comparative(args.model, output_dir, args.blinded, args.delay, args.resume)
    else:
        run_multi_tube(args.model, output_dir, args.blinded, args.delay, args.resume)
