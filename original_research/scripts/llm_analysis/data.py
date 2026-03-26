"""Load experiment data and group photos by channel/patient."""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ALL_PATIENTS_JSON = PROJECT_ROOT / "processed" / "en" / "all_patients.json"

CHANNEL_NAMES = {"0": "control", "19": "ch19_acceleration", "21": "ch21_deceleration"}

# Blinding: map real channels to neutral labels.
# The mapping is fixed so we can decode results after analysis.
BLIND_MAP = {"0": "A", "19": "B", "21": "C"}
BLIND_REVERSE = {v: k for k, v in BLIND_MAP.items()}  # A→0, B→19, C→21


@dataclass
class PhotoInfo:
    filename: str  # IMG_3250 (stem, no extension)
    patient: str  # "01"
    jpg_path: Path
    samples_shown: list[str] = field(default_factory=list)
    channel: str = "unknown"  # "0", "19", "21", "multi"
    channels: list[str] = field(default_factory=list)
    pdf_caption: str | None = None
    sample_count: int = 1


@dataclass
class ComparisonSet:
    patient: str
    control: PhotoInfo
    ch19: PhotoInfo
    ch21: PhotoInfo


@dataclass
class MultiTubeSet:
    patient: str
    photo: PhotoInfo
    caption: str
    channels: list[str]  # ["0", "19", "21"]


import re


def blind_caption(caption: str) -> str:
    """Replace channel numbers (0, 19, 21) and sample IDs with neutral A/B/C labels.

    Examples:
        "Left to right 0, 19, 21" → "Left to right A, B, C"
        "19.2.1 / 0.2.1 / 21.2.1" → "B / A / C"
        "Top to bottom: 21.4.1/0.4.1/19.4.1" → "Top to bottom: C/A/B"
    """
    result = caption
    # Replace full sample IDs first (e.g., "19.2.1" → "B")
    result = re.sub(r'\b19\.\d+\.\d+\b', 'B', result)
    result = re.sub(r'\b21\.\d+\.\d+\b', 'C', result)
    result = re.sub(r'\b0\.\d+\.\d+\b', 'A', result)
    # Replace standalone channel numbers (e.g., "0, 19, 21")
    # Avoid replacing numbers in time context like "After 21 hours"
    result = re.sub(r'(?<![Aa]fter )\b19\b', 'B', result)
    result = re.sub(r'(?<![Aa]fter )\b21\b', 'C', result)
    # "0" only when standalone (not "0.6.1" which is already replaced)
    result = re.sub(r'(?<!\d)0(?!\d|\.)', 'A', result)
    return result


def _resolve_jpg(patient_id: str, raw_filename: str) -> Path | None:
    stem = Path(raw_filename).stem
    jpg_dir = DATA_DIR / f"patient-{patient_id}" / "photos" / "jpg"
    for ext in (".jpg", ".JPG", ".jpeg"):
        candidate = jpg_dir / (stem + ext)
        if candidate.exists():
            return candidate
    return None


def _extract_channels(samples_shown: list[str]) -> list[str]:
    channels = set()
    for sample_id in samples_shown:
        ch = sample_id.split(".")[0]
        channels.add(ch)
    return sorted(channels)


def load_photos(patient_filter: list[str] | None = None) -> list[PhotoInfo]:
    """Load all photos from all_patients.json."""
    with open(ALL_PATIENTS_JSON) as f:
        data = json.load(f)

    photos: list[PhotoInfo] = []
    for patient in data["patients"]:
        pid = patient["patient_id"]
        if patient_filter and pid not in patient_filter:
            continue

        for photo in patient.get("photos", []):
            raw_filename = photo["filename"]
            jpg_path = _resolve_jpg(pid, raw_filename)
            if jpg_path is None:
                logger.warning("JPG not found: patient-%s %s", pid, raw_filename)
                continue

            samples = photo.get("samples_shown", [])
            channels = _extract_channels(samples)

            if len(channels) == 1:
                channel = channels[0]
            elif len(channels) > 1:
                channel = "multi"
            else:
                channel = "unknown"

            caption = photo.get("pdf_caption")
            vis = photo.get("visual_description", {})
            sc = vis.get("sample_count", 1) if isinstance(vis, dict) else 1

            photos.append(PhotoInfo(
                filename=Path(raw_filename).stem,
                patient=pid,
                jpg_path=jpg_path,
                samples_shown=samples,
                channel=channel,
                channels=channels,
                pdf_caption=caption,
                sample_count=sc if isinstance(sc, int) else 1,
            ))

    logger.info("Loaded %d photos (%d patients)", len(photos),
                len({p.patient for p in photos}))
    return photos


def group_by_channel(photos: list[PhotoInfo]) -> dict[str, list[PhotoInfo]]:
    """Group photos by channel. Only single-channel photos are grouped by number."""
    groups: dict[str, list[PhotoInfo]] = {}
    for photo in photos:
        groups.setdefault(photo.channel, []).append(photo)
    return groups


def build_comparison_sets(photos: list[PhotoInfo]) -> list[ComparisonSet]:
    """Build comparison triplets (control, ch19, ch21) per patient.

    Only uses single-channel photos. For patients with multiple photos
    per channel, creates all unique triplets.
    """
    per_patient: dict[str, dict[str, list[PhotoInfo]]] = {}
    for photo in photos:
        if photo.channel in ("multi", "unknown"):
            continue
        per_patient.setdefault(photo.patient, {}).setdefault(photo.channel, []).append(photo)

    sets: list[ComparisonSet] = []
    for pid, ch_map in sorted(per_patient.items()):
        controls = ch_map.get("0", [])
        ch19s = ch_map.get("19", [])
        ch21s = ch_map.get("21", [])

        if not controls or not ch19s or not ch21s:
            logger.info("Patient %s: missing channels (ctrl=%d, ch19=%d, ch21=%d) — skipping",
                        pid, len(controls), len(ch19s), len(ch21s))
            continue

        # Generate triplets: pair up by index, create as many as the smallest group
        count = min(len(controls), len(ch19s), len(ch21s))
        for i in range(count):
            sets.append(ComparisonSet(
                patient=pid,
                control=controls[i],
                ch19=ch19s[i],
                ch21=ch21s[i],
            ))

    logger.info("Built %d comparison sets from %d patients",
                len(sets), len({s.patient for s in sets}))
    return sets


def _caption_has_arrangement(caption: str, samples: list[str]) -> bool:
    """Check if caption contains tube arrangement info (not just timestamps).

    Valid: "Left to right 0, 19, 21", "19.2.1 / 0.2.1 / 21.2.1",
           "Top to bottom: 21.4.1/0.4.1/19.4.1"
    Invalid: "After 6 hours", "After 21 hours", "(no caption)"
    """
    low = caption.lower()
    # Positional keywords
    if any(kw in low for kw in ("left", "right", "top", "bottom",
                                 "слева", "справа", "сверху", "снизу")):
        return True
    # Contains sample IDs (e.g., "19.2.1")
    if any(sid in caption for sid in samples if "." in sid and len(sid) > 3):
        return True
    # Contains slash-separated IDs
    if "/" in caption and any(c.isdigit() for c in caption):
        return True
    return False


def _find_arrangement_from_neighbor(
    photo: PhotoInfo,
    all_multi: list[PhotoInfo],
) -> str | None:
    """For a multi-tube photo without arrangement caption, find arrangement
    from a neighboring photo of the same patient with the same channels."""
    ch_set = set(photo.channels)
    for other in all_multi:
        if other.patient != photo.patient:
            continue
        if other.filename == photo.filename:
            continue
        if set(other.channels) != ch_set:
            continue
        if other.pdf_caption and _caption_has_arrangement(
            other.pdf_caption, other.samples_shown
        ):
            return other.pdf_caption
    return None


def build_multi_tube_sets(
    photos: list[PhotoInfo],
    require_all_channels: bool = True,
) -> list[MultiTubeSet]:
    """Build multi-tube comparison sets from photos showing 2+ tubes.

    Photos with arrangement info in caption are included directly.
    Photos without arrangement (e.g. "After 6 hours") inherit arrangement
    from a neighboring photo of the same patient with the same channels.
    """
    required = {"0", "19", "21"}

    # Collect all multi-channel photos
    multi_photos = [
        p for p in photos
        if p.channel == "multi"
        and p.pdf_caption
        and "protocol" not in (p.pdf_caption or "").lower()
    ]

    sets: list[MultiTubeSet] = []
    for photo in multi_photos:
        ch_set = set(photo.channels)
        if require_all_channels and not required.issubset(ch_set):
            continue

        caption = photo.pdf_caption
        has_arr = _caption_has_arrangement(caption, photo.samples_shown)

        if not has_arr:
            # Try to inherit arrangement from a neighbor
            neighbor_arr = _find_arrangement_from_neighbor(photo, multi_photos)
            if neighbor_arr:
                caption = f"{neighbor_arr} ({caption})"
                logger.info("  %s: inherited arrangement from neighbor → %s",
                            photo.filename, caption)
            else:
                logger.debug("Skipping %s: caption '%s' lacks arrangement info",
                             photo.filename, caption)
                continue

        sets.append(MultiTubeSet(
            patient=photo.patient,
            photo=photo,
            caption=caption,
            channels=photo.channels,
        ))

    logger.info("Built %d multi-tube sets (require_all=%s)",
                len(sets), require_all_channels)
    return sets
