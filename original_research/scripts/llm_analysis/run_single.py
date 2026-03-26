#!/usr/bin/env python3
"""Single-photo blood plasma analysis through multiple LLM providers.

Sends each photo to all active Vision API providers in parallel,
extracts structured JSON, and saves consolidated results.

Usage:
    python -m scripts.llm_analysis.run_single                      # all photos
    python -m scripts.llm_analysis.run_single --providers openai,google
    python -m scripts.llm_analysis.run_single --patients 01,02 --max-photos 5
    python -m scripts.llm_analysis.run_single --dry-run
    python -m scripts.llm_analysis.run_single --resume
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
    parser = argparse.ArgumentParser(description="Single-photo LLM analysis")
    parser.add_argument("--providers", help="Comma-separated provider names")
    parser.add_argument("--patients", help="Comma-separated patient IDs (e.g. 01,02)")
    parser.add_argument("--output-dir", default="results/single",
                        help="Output directory (default: results/single)")
    parser.add_argument("--delay", type=float, default=2.0,
                        help="Delay between photos in seconds (default: 2.0)")
    parser.add_argument("--timeout", type=int, help="Per-provider timeout override")
    parser.add_argument("--resume", action="store_true", help="Skip already-processed photos")
    parser.add_argument("--dry-run", action="store_true", help="List photos without calling APIs")
    parser.add_argument("--max-photos", type=int, help="Max photos to process (for testing)")
    return parser.parse_args()


def _load_progress(progress_path: Path) -> set[str]:
    if progress_path.exists():
        return set(json.loads(progress_path.read_text()))
    return set()


def _save_progress(progress_path: Path, done: set[str]):
    progress_path.write_text(json.dumps(sorted(done), indent=2))


async def analyze_photo(photo, models, prompt, timeout):
    from scripts.llm_analysis.imaging import load_photo_b64, build_image_content
    from scripts.llm_analysis.providers import call_provider

    b64 = load_photo_b64(photo.jpg_path)
    image_content = build_image_content(b64)
    message = HumanMessage(content=[
        {"type": "text", "text": prompt},
        image_content,
    ])

    tasks = [
        call_provider(name, model, message, timeout)
        for name, model in models.items()
    ]
    return await asyncio.gather(*tasks, return_exceptions=True)


def main():
    _load_env()
    args = parse_args()

    from scripts.llm_analysis.data import load_photos, group_by_channel, CHANNEL_NAMES
    from scripts.llm_analysis.providers import init_providers
    from scripts.llm_analysis.prompts import SINGLE_PROMPT
    from scripts.llm_analysis.parsing import extract_single_structured

    # Init providers
    filter_names = args.providers.split(",") if args.providers else None
    models = init_providers(filter_names)
    if not models:
        logger.error("No providers available. Check API keys.")
        sys.exit(1)
    logger.info("Active providers: %s", list(models.keys()))

    # Load photos
    patient_filter = args.patients.split(",") if args.patients else None
    photos = load_photos(patient_filter)
    if not photos:
        logger.error("No photos found.")
        sys.exit(1)

    # Channel stats
    groups = group_by_channel(photos)
    for ch, items in sorted(groups.items()):
        name = CHANNEL_NAMES.get(ch, ch)
        logger.info("  %s: %d photos", name, len(items))

    # Dry run
    if args.dry_run:
        for photo in photos:
            ch_name = CHANNEL_NAMES.get(photo.channel, photo.channel)
            print(f"  patient-{photo.patient}: {photo.filename} [{ch_name}] "
                  f"samples={photo.samples_shown}")
        print(f"\nTotal: {len(photos)} photos, {len(models)} providers")
        return

    # Output setup
    project_root = Path(__file__).resolve().parent.parent.parent
    output_dir = project_root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    progress_path = output_dir / ".progress.json"

    # Resume
    done_keys = _load_progress(progress_path) if args.resume else set()
    if done_keys:
        logger.info("Resuming: %d photos already processed", len(done_keys))

    # Filter
    todo = [p for p in photos if p.filename not in done_keys]
    if args.max_photos:
        todo = todo[: args.max_photos]
    logger.info("Processing %d photos", len(todo))

    # Results collector
    all_results = []
    results_path = output_dir / "results.json"

    # Load existing results for resume
    if args.resume and results_path.exists():
        existing = json.loads(results_path.read_text())
        all_results = existing.get("photos", [])

    async def run():
        for i, photo in enumerate(todo):
            ch_name = CHANNEL_NAMES.get(photo.channel, photo.channel)
            logger.info("[%d/%d] patient-%s %s (%s)",
                        i + 1, len(todo), photo.patient, photo.filename, ch_name)

            raw_results = await analyze_photo(photo, models, SINGLE_PROMPT, args.timeout)

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
                    entry["structured"] = extract_single_structured(result["analysis"])
                else:
                    entry["raw"] = None
                    entry["structured"] = None

                providers_data[name] = entry

                status = "OK" if entry.get("error") is None else entry["error"]
                logger.info("  %s: %s (%dms)", name, status, entry["latency_ms"])

            photo_result = {
                "filename": photo.filename,
                "patient": photo.patient,
                "channel": photo.channel,
                "channels": photo.channels,
                "samples_shown": photo.samples_shown,
                "providers": providers_data,
            }
            all_results.append(photo_result)

            # Update progress
            done_keys.add(photo.filename)
            _save_progress(progress_path, done_keys)

            # Save results incrementally
            output = {
                "metadata": {
                    "generated": datetime.now(timezone.utc).isoformat(),
                    "mode": "single_photo",
                    "providers": list(models.keys()),
                    "total_photos": len(all_results),
                },
                "photos": all_results,
            }
            results_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))

            # Delay between photos
            if i < len(todo) - 1 and args.delay > 0:
                await asyncio.sleep(args.delay)

    asyncio.run(run())

    succeeded = sum(1 for r in all_results
                    if any(p.get("error") is None for p in r["providers"].values()))
    logger.info("Done: %d/%d photos succeeded", succeeded, len(all_results))
    logger.info("Results: %s", results_path)


if __name__ == "__main__":
    main()
