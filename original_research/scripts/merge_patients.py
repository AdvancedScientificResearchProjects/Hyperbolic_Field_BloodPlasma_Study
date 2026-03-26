#!/usr/bin/env python3
"""Merge all 7 patient analysis.json files into processed/{lang}/all_patients.json."""

import argparse
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PATIENT_IDS = [f"{i:02d}" for i in range(1, 8)]

METADATA = {
    "ru": {
        "project": "HyperbolicField-BloodPlasma-Study",
        "description": "Воздействие гиперболических полевых излучателей на плазму крови",
        "sample_id_format": "{channel}.{patient}.{number}",
        "sample_types": {
            "0": "контроль (без воздействия)",
            "19": "канал 19",
            "21": "канал 21",
        },
        "camera": "iPhone 16 Pro Max",
        "timezone": "+02:00",
    },
    "en": {
        "project": "HyperbolicField-BloodPlasma-Study",
        "description": "Blood plasma exposure to hyperbolic field emitters",
        "sample_id_format": "{channel}.{patient}.{number}",
        "sample_types": {
            "0": "control (no exposure)",
            "19": "channel 19",
            "21": "channel 21",
        },
        "camera": "iPhone 16 Pro Max",
        "timezone": "+02:00",
    },
}


def main():
    parser = argparse.ArgumentParser(description="Merge patient analysis.json files")
    parser.add_argument("--lang", choices=["en", "ru"], default="ru", help="Language version (default: ru)")
    args = parser.parse_args()

    lang = args.lang
    output_path = BASE / "processed" / lang / "all_patients.json"

    # Start with top-level metadata for the chosen language
    result = dict(METADATA[lang])

    # Read all analysis.json files
    patients = []
    for pid in PATIENT_IDS:
        path = BASE / "data" / f"patient-{pid}" / lang / "analysis.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["patient_id"] == pid, f"patient_id mismatch in {path}"
        patients.append(data)

    result["patients"] = patients

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Summary
    total_photos = 0
    with_desc = 0
    for patient in patients:
        for photo in patient.get("photos", []):
            total_photos += 1
            if "visual_description" in photo:
                with_desc += 1

    print(f"Lang: {lang}")
    print(f"Patients: {len(patients)}")
    print(f"Total photos: {total_photos}")
    print(f"With visual_description: {with_desc}")
    print(f"Without visual_description: {total_photos - with_desc}")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
