#!/usr/bin/env python3
"""Multi-tube comparative analysis: single photo with multiple tubes.

Sends photos showing 2+ tubes (with caption identifying channels) to LLM
providers and asks to compare coagulation between channels.

Usage:
    python -m scripts.llm_analysis.run_multi_tube --blinded
    python -m scripts.llm_analysis.run_multi_tube --providers mistral,perplexity
    python -m scripts.llm_analysis.run_multi_tube --dry-run
    python -m scripts.llm_analysis.run_multi_tube --include-partial
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
    parser = argparse.ArgumentParser(description="Multi-tube LLM analysis")
    parser.add_argument("--providers", help="Comma-separated provider names")
    parser.add_argument("--patients", help="Comma-separated patient IDs")
    parser.add_argument("--output-dir", help="Output directory (auto-set based on --blinded)")
    parser.add_argument("--delay", type=float, default=5.0,
                        help="Delay between sets (default: 5.0)")
    parser.add_argument("--timeout", type=int, help="Per-provider timeout override")
    parser.add_argument("--resume", action="store_true", help="Skip already-processed sets")
    parser.add_argument("--dry-run", action="store_true", help="List sets without calling APIs")
    parser.add_argument("--max-sets", type=int, help="Max sets (for testing)")
    parser.add_argument("--include-partial", action="store_true",
                        help="Include 2-channel photos (e.g. ch19+ch21 without control)")
    parser.add_argument("--blinded", action="store_true",
                        help="Use blinded prompt (no experiment context, neutral A/B/C labels)")
    return parser.parse_args()


def _set_key(mt_set) -> str:
    return f"{mt_set.patient}_{mt_set.photo.filename}"


def _load_progress(progress_path: Path) -> set[str]:
    if progress_path.exists():
        return set(json.loads(progress_path.read_text()))
    return set()


def _save_progress(progress_path: Path, done: set[str]):
    progress_path.write_text(json.dumps(sorted(done), indent=2))


def main():
    _load_env()
    args = parse_args()

    from scripts.llm_analysis.data import (
        load_photos, build_multi_tube_sets, blind_caption, BLIND_MAP,
    )
    from scripts.llm_analysis.providers import init_providers, call_provider
    from scripts.llm_analysis.prompts import (
        MULTI_TUBE_PROMPT_TEMPLATE, MULTI_TUBE_PROMPT_BLINDED_TEMPLATE,
    )
    from scripts.llm_analysis.parsing import (
        extract_comparative_structured, extract_blinded_structured,
    )
    from scripts.llm_analysis.imaging import load_photo_b64

    # Output dir
    if args.output_dir:
        output_subdir = args.output_dir
    elif args.blinded:
        output_subdir = "results/multi_tube_blinded"
    else:
        output_subdir = "results/multi_tube"

    if args.blinded:
        logger.info("BLINDED mode: channels mapped to %s", BLIND_MAP)

    # Init providers
    filter_names = args.providers.split(",") if args.providers else None
    models = init_providers(filter_names)
    if not models:
        logger.error("No providers available. Check API keys.")
        sys.exit(1)
    logger.info("Active providers: %s", list(models.keys()))

    # Load photos and build multi-tube sets
    patient_filter = args.patients.split(",") if args.patients else None
    photos = load_photos(patient_filter)
    mt_sets = build_multi_tube_sets(
        photos,
        require_all_channels=not args.include_partial,
    )

    if not mt_sets:
        logger.error("No multi-tube sets found. Use --include-partial for 2-channel photos.")
        sys.exit(1)

    # Dry run
    if args.dry_run:
        for s in mt_sets:
            caption_display = blind_caption(s.caption) if args.blinded else s.caption
            print(f"  Patient {s.patient}: {s.photo.filename} "
                  f"channels={s.channels} caption=\"{caption_display}\"")
        print(f"\nTotal: {len(mt_sets)} sets, {len(models)} providers"
              f" ({'BLINDED' if args.blinded else 'unblinded'})")
        return

    # Output setup
    project_root = Path(__file__).resolve().parent.parent.parent
    output_dir = project_root / output_subdir
    output_dir.mkdir(parents=True, exist_ok=True)
    progress_path = output_dir / ".progress.json"

    # Resume
    done_keys = _load_progress(progress_path) if args.resume else set()
    if done_keys:
        logger.info("Resuming: %d sets already processed", len(done_keys))

    # Filter
    todo = [s for s in mt_sets if _set_key(s) not in done_keys]
    if args.max_sets:
        todo = todo[: args.max_sets]
    logger.info("Processing %d multi-tube sets", len(todo))

    # Results collector
    all_results = []
    results_path = output_dir / "results.json"

    if args.resume and results_path.exists():
        existing = json.loads(results_path.read_text())
        all_results = existing.get("comparisons", [])

    # Select prompt and parser
    prompt_template = (MULTI_TUBE_PROMPT_BLINDED_TEMPLATE if args.blinded
                       else MULTI_TUBE_PROMPT_TEMPLATE)
    parse_fn = (extract_blinded_structured if args.blinded
                else extract_comparative_structured)

    async def run():
        for i, mt_set in enumerate(todo):
            # Blind the caption if needed
            caption = blind_caption(mt_set.caption) if args.blinded else mt_set.caption

            logger.info("[%d/%d] Patient %s: %s (%s) — \"%s\"",
                        i + 1, len(todo), mt_set.patient,
                        mt_set.photo.filename,
                        ",".join(mt_set.channels),
                        caption)

            # Load image
            b64 = load_photo_b64(mt_set.photo.jpg_path)

            # Build prompt
            prompt = prompt_template.format(caption=caption)

            # Build message with single image
            message = HumanMessage(content=[
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{b64}",
                }},
            ])

            # Fan-out to all providers
            tasks = [
                call_provider(name, model, message, args.timeout)
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
                }
                if result.get("analysis"):
                    entry["raw"] = result["analysis"]
                    entry["structured"] = parse_fn(result["analysis"])
                else:
                    entry["raw"] = None
                    entry["structured"] = None

                providers_data[name] = entry

                status = "OK" if entry.get("error") is None else entry["error"]
                logger.info("  %s: %s (%dms)", name, status, entry["latency_ms"])

            comparison_result = {
                "patient": mt_set.patient,
                "mode": "multi_tube_blinded" if args.blinded else "multi_tube",
                "blinded": args.blinded,
                "blind_map": BLIND_MAP if args.blinded else None,
                "photo": {
                    "filename": mt_set.photo.filename,
                    "sample_ids": mt_set.photo.samples_shown,
                    "caption_original": mt_set.caption,
                    "caption_sent": caption,
                    "channels": mt_set.channels,
                    "sample_count": mt_set.photo.sample_count,
                },
                "providers": providers_data,
            }
            all_results.append(comparison_result)

            # Update progress
            done_keys.add(_set_key(mt_set))
            _save_progress(progress_path, done_keys)

            # Save incrementally
            output = {
                "metadata": {
                    "generated": datetime.now(timezone.utc).isoformat(),
                    "mode": "multi_tube_blinded" if args.blinded else "multi_tube",
                    "blinded": args.blinded,
                    "blind_map": BLIND_MAP if args.blinded else None,
                    "providers": list(models.keys()),
                    "total_comparisons": len(all_results),
                },
                "comparisons": all_results,
            }
            results_path.write_text(
                json.dumps(output, indent=2, ensure_ascii=False)
            )

            if i < len(todo) - 1 and args.delay > 0:
                await asyncio.sleep(args.delay)

    asyncio.run(run())

    succeeded = sum(1 for r in all_results
                    if any(p.get("error") is None
                           for p in r["providers"].values()))
    logger.info("Done: %d/%d multi-tube comparisons succeeded",
                succeeded, len(all_results))
    logger.info("Results: %s", results_path)


if __name__ == "__main__":
    main()
