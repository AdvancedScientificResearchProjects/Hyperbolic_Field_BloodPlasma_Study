#!/usr/bin/env python3
"""Comparative blood plasma analysis: control vs ch19 vs ch21.

Sends 3 photos (one per channel) from the same patient to each provider
in a single request and asks to compare coagulation differences.

Usage:
    python -m scripts.llm_analysis.run_comparative
    python -m scripts.llm_analysis.run_comparative --providers openai,google
    python -m scripts.llm_analysis.run_comparative --patients 02,03 --max-sets 3
    python -m scripts.llm_analysis.run_comparative --dry-run
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.messages import HumanMessage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def _load_env():
    from dotenv import load_dotenv
    project_root = Path(__file__).resolve().parent.parent.parent
    asrp_root = project_root.parent / "asrp.science-llm"
    if (asrp_root / ".env").exists():
        load_dotenv(asrp_root / ".env")
    if (project_root / ".env").exists():
        load_dotenv(project_root / ".env", override=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Comparative LLM analysis")
    parser.add_argument("--providers", help="Comma-separated provider names")
    parser.add_argument("--patients", help="Comma-separated patient IDs")
    parser.add_argument("--output-dir", default="results/comparative",
                        help="Output directory (default: results/comparative)")
    parser.add_argument("--delay", type=float, default=5.0,
                        help="Delay between comparison sets (default: 5.0)")
    parser.add_argument("--timeout", type=int, help="Per-provider timeout override")
    parser.add_argument("--resume", action="store_true", help="Skip already-processed sets")
    parser.add_argument("--dry-run", action="store_true", help="List sets without calling APIs")
    parser.add_argument("--max-sets", type=int, help="Max comparison sets (for testing)")
    parser.add_argument("--blinded", action="store_true",
                        help="Use blinded prompt (neutral A/B/C labels, no experiment context)")
    return parser.parse_args()


def _load_progress(progress_path: Path) -> set[str]:
    if progress_path.exists():
        return set(json.loads(progress_path.read_text()))
    return set()


def _save_progress(progress_path: Path, done: set[str]):
    progress_path.write_text(json.dumps(sorted(done), indent=2))


def _set_key(comp_set) -> str:
    return f"{comp_set.patient}_{comp_set.control.filename}_{comp_set.ch19.filename}_{comp_set.ch21.filename}"


def _build_multi_image_message(comp_set, prompt: str, b64_map: dict) -> HumanMessage:
    """Build a HumanMessage with 3 images for comparative analysis."""
    return HumanMessage(content=[
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_map['control']}"}},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_map['ch19']}"}},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_map['ch21']}"}},
    ])


async def _call_with_fallback(name, model, comp_set, b64_map, prompt, single_prompt, timeout):
    """Try multi-image call; fall back to 3 single + text comparison."""
    from scripts.llm_analysis.providers import call_provider
    from scripts.llm_analysis.prompts import COMPARATIVE_FALLBACK_TEMPLATE

    message = _build_multi_image_message(comp_set, prompt, b64_map)
    result = await call_provider(name, model, message, timeout)

    if result.get("error") and "image" in result.get("error", "").lower():
        logger.info("  %s: multi-image failed, using fallback", name)
        return await _fallback_sequential(
            name, model, b64_map, single_prompt, timeout
        )
    return result


async def _fallback_sequential(name, model, b64_map, single_prompt, timeout):
    """Fallback: 3 single-image calls + text comparison."""
    from scripts.llm_analysis.providers import call_provider
    from scripts.llm_analysis.prompts import COMPARATIVE_FALLBACK_TEMPLATE
    from scripts.llm_analysis.imaging import build_image_content

    descriptions = {}
    total_latency = 0

    for label in ("control", "ch19", "ch21"):
        msg = HumanMessage(content=[
            {"type": "text", "text": single_prompt},
            build_image_content(b64_map[label]),
        ])
        result = await call_provider(name, model, msg, timeout)
        total_latency += result.get("latency_ms", 0)

        if result.get("error"):
            return {
                "provider": name,
                "error": f"Fallback failed on {label}: {result['error']}",
                "latency_ms": total_latency,
                "fallback": True,
            }
        descriptions[label] = result["analysis"]

    # Text-only comparison
    comparison_prompt = COMPARATIVE_FALLBACK_TEMPLATE.format(
        control_description=descriptions["control"],
        ch19_description=descriptions["ch19"],
        ch21_description=descriptions["ch21"],
    )
    comp_msg = HumanMessage(content=[{"type": "text", "text": comparison_prompt}])
    comp_result = await call_provider(name, model, comp_msg, timeout)
    total_latency += comp_result.get("latency_ms", 0)

    if comp_result.get("error"):
        return {
            "provider": name,
            "error": f"Fallback comparison failed: {comp_result['error']}",
            "latency_ms": total_latency,
            "fallback": True,
        }

    return {
        "provider": name,
        "analysis": comp_result["analysis"],
        "latency_ms": total_latency,
        "fallback": True,
        "individual_descriptions": descriptions,
    }


def main():
    _load_env()
    args = parse_args()

    from scripts.llm_analysis.data import load_photos, build_comparison_sets, BLIND_MAP
    from scripts.llm_analysis.providers import init_providers
    from scripts.llm_analysis.prompts import (
        COMPARATIVE_PROMPT, SINGLE_PROMPT,
        COMPARATIVE_PROMPT_BLINDED,
    )
    from scripts.llm_analysis.parsing import (
        extract_comparative_structured, extract_blinded_structured,
    )
    from scripts.llm_analysis.imaging import load_photo_b64

    if args.blinded:
        logger.info("BLINDED mode: channels mapped to %s", BLIND_MAP)

    # Init providers
    filter_names = args.providers.split(",") if args.providers else None
    models = init_providers(filter_names)
    if not models:
        logger.error("No providers available. Check API keys.")
        sys.exit(1)
    logger.info("Active providers: %s", list(models.keys()))

    # Load photos and build comparison sets
    patient_filter = args.patients.split(",") if args.patients else None
    photos = load_photos(patient_filter)
    comp_sets = build_comparison_sets(photos)

    if not comp_sets:
        logger.error("No comparison sets available (need patients with all 3 channels).")
        sys.exit(1)

    # Dry run
    if args.dry_run:
        for s in comp_sets:
            print(f"  Patient {s.patient}: "
                  f"ctrl={s.control.filename} ({s.control.samples_shown}), "
                  f"ch19={s.ch19.filename} ({s.ch19.samples_shown}), "
                  f"ch21={s.ch21.filename} ({s.ch21.samples_shown})")
        print(f"\nTotal: {len(comp_sets)} sets, {len(models)} providers")
        return

    # Select prompt and parser based on blinded mode
    if args.blinded:
        comparative_prompt = COMPARATIVE_PROMPT_BLINDED
        parse_fn = extract_blinded_structured
    else:
        comparative_prompt = COMPARATIVE_PROMPT
        parse_fn = extract_comparative_structured

    # Output setup
    project_root = Path(__file__).resolve().parent.parent.parent
    if args.output_dir != "results/comparative":
        output_subdir = args.output_dir
    elif args.blinded:
        output_subdir = "results/comparative_blinded"
    else:
        output_subdir = args.output_dir
    output_dir = project_root / output_subdir
    output_dir.mkdir(parents=True, exist_ok=True)
    progress_path = output_dir / ".progress.json"

    # Resume
    done_keys = _load_progress(progress_path) if args.resume else set()
    if done_keys:
        logger.info("Resuming: %d sets already processed", len(done_keys))

    # Filter
    todo = [s for s in comp_sets if _set_key(s) not in done_keys]
    if args.max_sets:
        todo = todo[: args.max_sets]
    logger.info("Processing %d comparison sets", len(todo))

    # Results collector
    all_results = []
    results_path = output_dir / "results.json"

    if args.resume and results_path.exists():
        existing = json.loads(results_path.read_text())
        all_results = existing.get("comparisons", [])

    async def run():
        for i, comp_set in enumerate(todo):
            logger.info("[%d/%d] Patient %s: ctrl=%s ch19=%s ch21=%s",
                        i + 1, len(todo), comp_set.patient,
                        comp_set.control.filename, comp_set.ch19.filename,
                        comp_set.ch21.filename)

            # Load images
            b64_map = {
                "control": load_photo_b64(comp_set.control.jpg_path),
                "ch19": load_photo_b64(comp_set.ch19.jpg_path),
                "ch21": load_photo_b64(comp_set.ch21.jpg_path),
            }

            # Fan-out to all providers
            tasks = [
                _call_with_fallback(
                    name, model, comp_set, b64_map,
                    comparative_prompt, SINGLE_PROMPT, args.timeout,
                )
                for name, model in models.items()
            ]
            raw_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Build provider results
            providers_data = {}
            for result in raw_results:
                if isinstance(result, Exception):
                    logger.error("Unexpected error: %s", result)
                    continue

                name = result["provider"]
                entry = {
                    "latency_ms": result.get("latency_ms", 0),
                    "error": result.get("error"),
                    "fallback": result.get("fallback", False),
                }
                if result.get("analysis"):
                    entry["raw"] = result["analysis"]
                    entry["structured"] = parse_fn(result["analysis"])
                else:
                    entry["raw"] = None
                    entry["structured"] = None

                providers_data[name] = entry

                status = "OK" if entry.get("error") is None else entry["error"]
                fb = " [fallback]" if entry.get("fallback") else ""
                logger.info("  %s: %s (%dms)%s", name, status, entry["latency_ms"], fb)

            comparison_result = {
                "patient": comp_set.patient,
                "blinded": args.blinded,
                "blind_map": BLIND_MAP if args.blinded else None,
                "photos": {
                    "control": {
                        "filename": comp_set.control.filename,
                        "sample_ids": comp_set.control.samples_shown,
                    },
                    "ch19": {
                        "filename": comp_set.ch19.filename,
                        "sample_ids": comp_set.ch19.samples_shown,
                    },
                    "ch21": {
                        "filename": comp_set.ch21.filename,
                        "sample_ids": comp_set.ch21.samples_shown,
                    },
                },
                "providers": providers_data,
            }
            all_results.append(comparison_result)

            # Update progress
            done_keys.add(_set_key(comp_set))
            _save_progress(progress_path, done_keys)

            # Save incrementally
            mode = "comparative_blinded" if args.blinded else "comparative"
            output = {
                "metadata": {
                    "generated": datetime.now(timezone.utc).isoformat(),
                    "mode": mode,
                    "blinded": args.blinded,
                    "blind_map": BLIND_MAP if args.blinded else None,
                    "providers": list(models.keys()),
                    "total_comparisons": len(all_results),
                },
                "comparisons": all_results,
            }
            results_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))

            if i < len(todo) - 1 and args.delay > 0:
                await asyncio.sleep(args.delay)

    asyncio.run(run())

    succeeded = sum(1 for r in all_results
                    if any(p.get("error") is None for p in r["providers"].values()))
    logger.info("Done: %d/%d comparisons succeeded", succeeded, len(all_results))
    logger.info("Results: %s", results_path)


if __name__ == "__main__":
    main()
