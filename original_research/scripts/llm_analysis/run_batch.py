#!/usr/bin/env python3
"""Batch patient-level analysis: send ALL triplets at once for statistical comparison.

Instead of 3 photos from 1 patient, sends N triplets (3×N photos) from multiple patients
and asks the LLM to evaluate the pattern across the entire dataset.
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts.llm_analysis.data import (
    BLIND_MAP,
    build_comparison_sets,
    load_photos,
)
from scripts.llm_analysis.imaging import build_image_content, load_photo_b64
from scripts.llm_analysis.prompts import BATCH_PROMPT_BLINDED, BATCH_PROMPT_UNBLINDED
from scripts.llm_analysis.providers import call_provider, init_providers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def select_best_triplet(comp_sets, patient):
    """Pick one representative triplet per patient (first available)."""
    for cs in comp_sets:
        if cs.patient == patient:
            return cs
    return None


def build_batch_message(comp_sets, patients, blinded):
    """Build a single HumanMessage with all triplets' images + prompt."""
    triplets = []
    for pat in patients:
        cs = select_best_triplet(comp_sets, pat)
        if cs:
            triplets.append(cs)

    content_parts = []
    image_list_lines = []

    for idx, cs in enumerate(triplets):
        if blinded:
            pat_label = f"Patient {idx + 1}"
            labels = ["Sample A", "Sample B", "Sample C"]
        else:
            pat_label = f"P{cs.patient}"
            labels = [
                f"CONTROL ({cs.control.filename})",
                f"CH19 ({cs.ch19.filename})",
                f"CH21 ({cs.ch21.filename})",
            ]

        image_list_lines.append(f"\n**{pat_label}** (3 images):")
        for i, (photo, label) in enumerate(
            zip([cs.control, cs.ch19, cs.ch21], labels)
        ):
            img_num = idx * 3 + i + 1
            image_list_lines.append(f"  - Image {img_num}: {label}")
            b64 = load_photo_b64(photo.jpg_path)
            content_parts.append(build_image_content(b64))

    image_list_str = "\n".join(image_list_lines)

    prompt_template = BATCH_PROMPT_BLINDED if blinded else BATCH_PROMPT_UNBLINDED
    prompt_text = prompt_template.format(
        n_triplets=len(triplets),
        n_patients=len(triplets),
        image_list=image_list_str,
    )

    # Text first, then all images
    final_content = [{"type": "text", "text": prompt_text}] + content_parts

    return HumanMessage(content=final_content), triplets


async def run_batch(providers_filter, output_dir, blinded, timeout_override):
    photos = load_photos()
    comp_sets = build_comparison_sets(photos)
    logger.info("Built %d comparison sets", len(comp_sets))

    # Get unique patients with comparisons
    patients = sorted(set(cs.patient for cs in comp_sets))
    logger.info("Patients with triplets: %s", patients)

    models = init_providers(providers_filter)
    if not models:
        logger.error("No providers available")
        return
    logger.info("Active providers: %s", list(models.keys()))

    message, triplets = build_batch_message(comp_sets, patients, blinded)
    n_images = len(triplets) * 3
    logger.info(
        "Batch: %d patients, %d triplets, %d images, blinded=%s",
        len(patients), len(triplets), n_images, blinded,
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    for name, model in models.items():
        logger.info("Calling %s with %d images...", name, n_images)
        result = await call_provider(name, model, message, timeout_override)
        latency = result.get("latency_ms", 0)

        if "error" in result:
            logger.error("  %s: %s (%dms)", name, result["error"], latency)
        else:
            logger.info("  %s: OK (%dms)", name, latency)

        output = {
            "metadata": {
                "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "mode": "batch_blinded" if blinded else "batch",
                "blinded": blinded,
                "blind_map": BLIND_MAP if blinded else None,
                "provider": name,
                "n_patients": len(triplets),
                "n_images": n_images,
                "patients": [cs.patient for cs in triplets],
            },
            "triplets": [
                {
                    "patient": cs.patient,
                    "control": cs.control.filename,
                    "ch19": cs.ch19.filename,
                    "ch21": cs.ch21.filename,
                }
                for cs in triplets
            ],
            "result": {
                "provider": name,
                "latency_ms": latency,
                "error": result.get("error"),
                "raw": result.get("analysis"),
            },
        }

        out_path = output_dir / f"batch_{name}.json"
        out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
        logger.info("  Saved: %s", out_path)


def parse_args():
    parser = argparse.ArgumentParser(description="Batch patient-level analysis")
    parser.add_argument("--providers", help="Comma-separated provider names")
    parser.add_argument(
        "--output-dir",
        default="results/batch",
        help="Output directory (relative to project root)",
    )
    parser.add_argument("--blinded", action="store_true")
    parser.add_argument("--timeout", type=int, default=600, help="Timeout per provider (seconds)")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    output_dir = PROJECT_ROOT / args.output_dir
    providers = args.providers.split(",") if args.providers else None

    asyncio.run(run_batch(providers, output_dir, args.blinded, args.timeout))
