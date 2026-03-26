#!/usr/bin/env python3
"""Run DINOv2 + SigLIP2 + MedSigLIP + BiomedCLIP on all patient photos.

Saves per-photo JSON results and a combined summary
for comparison with SAM-2 segmentation results.

Usage:
  python3 scripts/cv_analysis/run_ml_models.py          # use cache
  python3 scripts/cv_analysis/run_ml_models.py --force   # re-run all
"""

import argparse
import json
import time
from collections import Counter
from pathlib import Path

from ml_models import (
    run_dinov2,
    run_siglip2,
    run_medsiglip,
    run_biomedclip,
    COAGULATION_LABEL_MAP,
)
from PIL import Image

PROJECT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT / "data"
CV_RESULTS_DIR = Path(__file__).resolve().parent / "results"
OUTPUT_DIR = Path(__file__).resolve().parent / "ml_results"
OUTPUT_DIR.mkdir(exist_ok=True)


def find_all_photos() -> list[tuple[str, str, Path]]:
    """Return (patient, filename, path) for all jpg photos."""
    photos = []
    for patient_dir in sorted(DATA_DIR.glob("patient-*")):
        patient = patient_dir.name.split("-")[1]
        jpg_dir = patient_dir / "photos" / "jpg"
        if not jpg_dir.exists():
            continue
        for f in sorted(jpg_dir.iterdir()):
            if f.suffix.lower() in (".jpg", ".jpeg"):
                photos.append((patient, f.stem, f))
    return photos


def analyze_photo(patient: str, filename: str, photo_path: Path) -> dict:
    """Run all 4 models on a single photo."""
    img = Image.open(photo_path).convert("RGB")

    result = {
        "filename": filename,
        "patient": patient,
        "dinov2": None,
        "siglip2": None,
        "medsiglip": None,
        "biomedclip": None,
        "errors": {},
    }

    models = [
        ("dinov2", run_dinov2),
        ("siglip2", run_siglip2),
        ("medsiglip", run_medsiglip),
        ("biomedclip", run_biomedclip),
    ]

    for name, fn in models:
        try:
            out = fn(img)
            if name == "dinov2" and out:
                emb = out["embedding"]
                result[name] = {
                    "embedding_norm": round(sum(x**2 for x in emb) ** 0.5, 4),
                    "embedding_first10": [round(x, 4) for x in emb[:10]],
                }
            elif out:
                result[name] = out
        except Exception as e:
            result["errors"][name] = str(e)

    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Re-run all, ignore cache")
    args = parser.parse_args()

    photos = find_all_photos()
    print(f"Found {len(photos)} photos" + (" (--force: ignoring cache)" if args.force else ""))

    # Load visual assessment results for comparison
    cv_results = {}
    for f in CV_RESULTS_DIR.glob("*.json"):
        try:
            r = json.loads(f.read_text())
            cv_results[r["filename"]] = r
        except Exception:
            pass

    all_results = []
    for i, (patient, filename, path) in enumerate(photos):
        out_file = OUTPUT_DIR / f"{filename}.json"
        if out_file.exists() and not args.force:
            print(f"  [{i+1}/{len(photos)}] {filename} — cached")
            all_results.append(json.loads(out_file.read_text()))
            continue

        t0 = time.time()
        result = analyze_photo(patient, filename, path)
        dt = time.time() - t0

        # Add visual assessment data for comparison
        cv = cv_results.get(filename, {})
        result["visual_assessment"] = {
            "expected_clots": cv.get("visual_assessment", {}).get("expected_clots"),
            "match": cv.get("match"),
            "needs_manual_review": cv.get("needs_manual_review"),
        }

        out_file.write_text(json.dumps(result, indent=2, ensure_ascii=False))
        all_results.append(result)

        # Summary line
        siglip_top = result.get("siglip2", {}).get("top_label", "?")[:30] if result.get("siglip2") else "FAIL"
        medsiglip_top = result.get("medsiglip", {}).get("top_label", "?")[:30] if result.get("medsiglip") else "FAIL"
        biomed_top = result.get("biomedclip", {}).get("top_label", "?")[:30] if result.get("biomedclip") else "FAIL"
        print(f"  [{i+1}/{len(photos)}] {filename} (p{patient}) {dt:.1f}s | SigLIP:{siglip_top} | MedSigLIP:{medsiglip_top} | BiomedCLIP:{biomed_top}")

    # Save combined results
    combined_file = OUTPUT_DIR / "all_results.json"
    combined_file.write_text(json.dumps(all_results, indent=2, ensure_ascii=False))

    # Print summary
    print(f"\n{'='*70}")
    print(f"SUMMARY: {len(all_results)} photos processed\n")

    for model_name in ("siglip2", "medsiglip", "biomedclip"):
        labels = Counter()
        fails = 0
        for r in all_results:
            if r.get(model_name):
                labels[r[model_name]["top_label"]] += 1
            else:
                fails += 1
        print(f"{model_name} top labels ({fails} failures):")
        for label, count in labels.most_common():
            print(f"  {count:3d}  {label}")
        print()

    # Compare: each model's clot detection vs visual assessment
    for model_name in ("siglip2", "medsiglip", "biomedclip"):
        agree = disagree = 0
        for r in all_results:
            cv_clots = r.get("visual_assessment", {}).get("expected_clots")
            if cv_clots is None:
                continue
            cv_has = cv_clots > 0
            model_data = r.get(model_name)
            if not model_data:
                continue
            clot_score = max(
                (lbl["score"] for lbl in model_data.get("labels", []) if "clot" in lbl["label"]),
                default=0,
            )
            model_has = clot_score > 0.15  # softmax threshold
            if cv_has == model_has:
                agree += 1
            else:
                disagree += 1
        total = agree + disagree
        if total:
            print(f"{model_name} vs visual assessment agreement: {agree}/{total} ({agree/total*100:.1f}%)")

    print(f"\nResults saved to: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
