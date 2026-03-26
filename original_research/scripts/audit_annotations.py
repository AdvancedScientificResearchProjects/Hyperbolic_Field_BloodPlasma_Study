"""Data quality audit for all_patients.json annotations."""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "processed" / "en" / "all_patients.json"
DATA_DIR = BASE_DIR / "data"

TIMESTAMP_FMT = "%Y-%m-%d %H:%M:%S"
MAX_NEIGHBOR_DELTA_MIN = 30


def load_data() -> dict:
    with open(DATA_FILE) as f:
        return json.load(f)


def parse_sample_id(sample_id: str) -> tuple[str, str, str]:
    """Return (channel, patient, number) from '{channel}.{patient}.{number}'.

    Also handles 2-part IDs like '0.7' -> ('0', '7', '').
    """
    parts = sample_id.split(".")
    if len(parts) == 3:
        return parts[0], parts[1], parts[2]
    if len(parts) == 2:
        return parts[0], parts[1], ""
    return ("", "", "")


def check_sample_patient_consistency(data: dict) -> list[str]:
    """Check 1: every sample_id patient field matches the photo's patient_id."""
    issues: list[str] = []
    format_issues: list[str] = []
    for patient in data["patients"]:
        pid = patient["patient_id"]
        pid_int = str(int(pid))  # "01" -> "1", "05" -> "5"
        for photo in patient["photos"]:
            for sid in photo.get("samples_shown", []):
                ch, sample_patient, num = parse_sample_id(sid)
                if not num:
                    format_issues.append(
                        f"  Patient {pid}, {photo['filename']}: "
                        f"sample '{sid}' has non-standard format (missing number part)"
                    )
                    continue
                if sample_patient != pid and sample_patient != pid_int:
                    issues.append(
                        f"  Patient {pid}, {photo['filename']}: "
                        f"sample '{sid}' has patient={sample_patient}, expected {pid}"
                    )
    return issues + format_issues


def check_timestamp_ordering(data: dict) -> list[str]:
    """Check 2: within each patient+pdf_part group, consecutive pages have timestamps within 30 min."""
    issues: list[str] = []
    for patient in data["patients"]:
        pid = patient["patient_id"]
        groups: dict[str, list[dict]] = defaultdict(list)
        for photo in patient["photos"]:
            part_key = str(photo.get("pdf_part", "none"))
            groups[part_key].append(photo)

        for part_key, photos in groups.items():
            sorted_photos = sorted(photos, key=lambda p: p.get("pdf_page", 0))
            for i in range(1, len(sorted_photos)):
                prev = sorted_photos[i - 1]
                curr = sorted_photos[i]
                try:
                    if not prev.get("exif_datetime") or not curr.get("exif_datetime"):
                        continue
                    t_prev = datetime.strptime(prev["exif_datetime"], TIMESTAMP_FMT)
                    t_curr = datetime.strptime(curr["exif_datetime"], TIMESTAMP_FMT)
                except (ValueError, KeyError):
                    continue
                delta = abs((t_curr - t_prev).total_seconds()) / 60.0
                if delta > MAX_NEIGHBOR_DELTA_MIN:
                    part_label = f" (pdf_part={part_key})" if part_key != "none" else ""
                    issues.append(
                        f"  Patient {pid}{part_label}: "
                        f"page {prev.get('pdf_page')}->{curr.get('pdf_page')} "
                        f"({prev['filename']}->{curr['filename']}) "
                        f"delta={delta:.0f} min"
                    )
    return issues


def check_channel_assignment(data: dict) -> list[str]:
    """Check 3: unlabeled photos (no pdf_caption) should match the channel of the next labeled photo."""
    issues: list[str] = []
    for patient in data["patients"]:
        pid = patient["patient_id"]
        groups: dict[str, list[dict]] = defaultdict(list)
        for photo in patient["photos"]:
            part_key = str(photo.get("pdf_part", "none"))
            groups[part_key].append(photo)

        for part_key, photos in groups.items():
            sorted_photos = sorted(photos, key=lambda p: p.get("pdf_page", 0))
            for i, photo in enumerate(sorted_photos):
                if photo.get("pdf_caption") is not None:
                    continue
                if not photo.get("samples_shown"):
                    continue

                # Find next photo with pdf_caption
                next_labeled = None
                for j in range(i + 1, len(sorted_photos)):
                    if sorted_photos[j].get("pdf_caption") is not None:
                        next_labeled = sorted_photos[j]
                        break

                if next_labeled is None:
                    continue

                # Extract channels from both
                unlabeled_channels = set()
                for sid in photo["samples_shown"]:
                    ch, _, _ = parse_sample_id(sid)
                    unlabeled_channels.add(ch)

                labeled_channels = set()
                for sid in next_labeled.get("samples_shown", []):
                    ch, _, _ = parse_sample_id(sid)
                    labeled_channels.add(ch)

                if not unlabeled_channels.issubset(labeled_channels):
                    part_label = f" (pdf_part={part_key})" if part_key != "none" else ""
                    issues.append(
                        f"  Patient {pid}{part_label}: unlabeled {photo['filename']} "
                        f"(page {photo.get('pdf_page')}) channels={unlabeled_channels} "
                        f"vs next labeled {next_labeled['filename']} "
                        f"(page {next_labeled.get('pdf_page')}) channels={labeled_channels}"
                    )
    return issues


def check_duplicate_filenames(data: dict) -> list[str]:
    """Check 4: no filename should appear in more than one patient."""
    issues: list[str] = []
    filename_to_patients: dict[str, list[str]] = defaultdict(list)
    for patient in data["patients"]:
        pid = patient["patient_id"]
        for photo in patient["photos"]:
            filename_to_patients[photo["filename"]].append(pid)

    for fname, pids in sorted(filename_to_patients.items()):
        if len(pids) > 1:
            issues.append(f"  {fname} appears in patients: {', '.join(pids)}")
    return issues


def check_jpg_existence(data: dict) -> list[str]:
    """Check 5: JPG files exist for each photo."""
    issues: list[str] = []
    for patient in data["patients"]:
        pid = patient["patient_id"]
        jpg_dir = DATA_DIR / f"patient-{pid}" / "photos" / "jpg"
        for photo in patient["photos"]:
            fname = photo["filename"]
            jpg_name = Path(fname).stem + ".jpg"
            jpg_path = jpg_dir / jpg_name
            if not jpg_path.exists():
                issues.append(f"  Patient {pid}: missing {jpg_path.relative_to(BASE_DIR)}")
    return issues


def check_sample_count_consistency(data: dict) -> list[str]:
    """Check 6: sample_count==1 but multiple channels in samples_shown is suspicious."""
    issues: list[str] = []
    for patient in data["patients"]:
        pid = patient["patient_id"]
        for photo in patient["photos"]:
            vd = photo.get("visual_description", {})
            sample_count = vd.get("sample_count")
            samples = photo.get("samples_shown", [])
            if sample_count is not None and len(samples) > 0:
                channels = set()
                for sid in samples:
                    ch, _, _ = parse_sample_id(sid)
                    channels.add(ch)
                if sample_count == 1 and len(channels) > 1:
                    issues.append(
                        f"  Patient {pid}, {photo['filename']}: "
                        f"sample_count=1 but channels={channels} "
                        f"(samples_shown={samples})"
                    )
                if sample_count == 1 and len(samples) > 1 and len(channels) == 1:
                    issues.append(
                        f"  Patient {pid}, {photo['filename']}: "
                        f"sample_count=1 but {len(samples)} samples shown "
                        f"(same channel, possible multi-tube): {samples}"
                    )
    return issues


def build_comparison_sets(data: dict) -> dict:
    """Check 7: simulate building comparison sets and report summary."""
    stats: dict = {
        "single_channel_triplets": [],
        "multi_tube_sets": [],
        "patients_with_all_channels": 0,
        "per_patient": {},
    }

    for patient in data["patients"]:
        pid = patient["patient_id"]
        channel_photos: dict[str, list[dict]] = defaultdict(list)

        for photo in patient["photos"]:
            vd = photo.get("visual_description", {})
            sample_count = vd.get("sample_count", 0)
            samples = photo.get("samples_shown", [])

            # Multi-tube photos (multiple different channels in one photo)
            channels_in_photo = set()
            for sid in samples:
                ch, _, _ = parse_sample_id(sid)
                channels_in_photo.add(ch)

            if len(channels_in_photo) > 1:
                stats["multi_tube_sets"].append({
                    "patient": pid,
                    "filename": photo["filename"],
                    "channels": sorted(channels_in_photo),
                    "samples": samples,
                })

            # Single-channel photos
            if len(channels_in_photo) == 1 and sample_count == 1:
                ch = list(channels_in_photo)[0]
                channel_photos[ch].append(photo["filename"])

        has_0 = "0" in channel_photos
        has_19 = "19" in channel_photos
        has_21 = "21" in channel_photos
        if has_0 and has_19 and has_21:
            stats["patients_with_all_channels"] += 1
            stats["single_channel_triplets"].append(pid)

        stats["per_patient"][pid] = {
            ch: len(files) for ch, files in sorted(channel_photos.items())
        }

    return stats


def print_section(title: str, issues: list[str], check_num: int) -> None:
    header = f"CHECK {check_num}: {title}"
    print(f"\n{'=' * 70}")
    print(header)
    print("-" * 70)
    if issues:
        print(f"\u274c {len(issues)} issue(s) found:")
        for issue in issues:
            print(issue)
    else:
        print("\u2705 All checks passed.")


def main() -> None:
    data = load_data()
    total_photos = sum(len(p["photos"]) for p in data["patients"])
    total_patients = len(data["patients"])
    print(f"Audit of {DATA_FILE.relative_to(BASE_DIR)}")
    print(f"Patients: {total_patients}, Photos: {total_photos}")

    # Check 1
    issues1 = check_sample_patient_consistency(data)
    print_section("Sample ID vs patient consistency", issues1, 1)

    # Check 2
    issues2 = check_timestamp_ordering(data)
    print_section("Timestamp ordering within PDF groups", issues2, 2)

    # Check 3
    issues3 = check_channel_assignment(data)
    print_section("Channel assignment consistency (unlabeled photos)", issues3, 3)

    # Check 4
    issues4 = check_duplicate_filenames(data)
    print_section("Duplicate filename detection", issues4, 4)

    # Check 5
    issues5 = check_jpg_existence(data)
    print_section("JPG file existence", issues5, 5)

    # Check 6
    issues6 = check_sample_count_consistency(data)
    print_section("sample_count vs samples_shown consistency", issues6, 6)

    # Check 7
    print(f"\n{'=' * 70}")
    print("CHECK 7: Comparison set validity")
    print("-" * 70)
    stats = build_comparison_sets(data)

    print(f"\nPatients with all 3 channels (0, 19, 21) as single-tube photos: "
          f"{stats['patients_with_all_channels']}/{total_patients}")
    if stats["single_channel_triplets"]:
        print(f"  Triplet-ready patients: {', '.join(stats['single_channel_triplets'])}")

    print(f"\nSingle-channel photo counts per patient:")
    print(f"  {'Patient':<10} {'ch 0':<8} {'ch 19':<8} {'ch 21':<8}")
    print(f"  {'-'*34}")
    for pid, channels in sorted(stats["per_patient"].items()):
        c0 = channels.get("0", 0)
        c19 = channels.get("19", 0)
        c21 = channels.get("21", 0)
        print(f"  {pid:<10} {c0:<8} {c19:<8} {c21:<8}")

    print(f"\nMulti-tube photos (multiple channels in one image): {len(stats['multi_tube_sets'])}")
    for mt in stats["multi_tube_sets"]:
        print(f"  Patient {mt['patient']}: {mt['filename']} "
              f"channels={mt['channels']} samples={mt['samples']}")

    # Summary
    total_issues = len(issues1) + len(issues2) + len(issues3) + len(issues4) + len(issues5) + len(issues6)
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print("-" * 70)
    checks = [
        ("Sample ID vs patient", issues1),
        ("Timestamp ordering", issues2),
        ("Channel assignment", issues3),
        ("Duplicate filenames", issues4),
        ("JPG existence", issues5),
        ("sample_count consistency", issues6),
    ]
    for name, iss in checks:
        icon = "\u2705" if not iss else f"\u26a0\ufe0f  ({len(iss)})"
        print(f"  {name:<35} {icon}")
    print(f"\nTotal issues: {total_issues}")


if __name__ == "__main__":
    main()
