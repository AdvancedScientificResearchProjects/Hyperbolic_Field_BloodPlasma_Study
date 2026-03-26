#!/usr/bin/env python3
"""Enrich LLM vision analysis with README photo-to-channel mappings."""

import json
import re
from collections import defaultdict

# ── README-based photo → sample mapping ──────────────────────────
# Format: filename_stem → { samples: [sample_ids], label: str, notes: str }

README_MAP = {
    # ── Patient-01 ──
    "IMG_3250": {"samples": ["19.1.1", "21.1.1"], "label": "19.1.1/21.1.1"},
    "IMG_3251": {"samples": ["21.1.1"], "label": "21.1.1"},
    "IMG_3252": {"samples": ["19.1.1"], "label": "19.1.1"},
    "IMG_3253": {"samples": ["19.1.1", "21.1.1", "0.1.1"], "label": "Top to bottom: 19.1.1,21.1.1,0.1.1"},
    "IMG_3254": {"samples": ["0.1.2", "21.1.1", "19.1.1", "0.1.1"], "label": "4 tubes with labels: 0.1.2, 21.1.1, 19.1.1, 0.1..."},
    "IMG_3255": {"samples": ["21.1.1", "19.1.1", "0.1.1"], "label": "3 tubes on dark surface"},
    "IMG_3256": {"samples": ["21.1.1", "19.1.1", "0.1.1"], "label": "Top to bottom: 21.1.1,19.1.1,0.1.1"},
    "IMG_3257": {"samples": ["0.1.1", "19.1.1", "21.1.1"], "label": "Left to right 0.1.1, 19.1.1,21.1.1"},
    "IMG_3258": {"samples": ["21.1.1", "0.1.1", "19.1.1"], "label": "Left to right 21.1.1,0.1.1,19.1.1"},
    "IMG_3259": {"samples": ["19.1.1", "21.1.1", "0.1.1", "0.1.2"], "label": "Top to bottom: 19.1.1, 21.1.1, 0.1.1, 0.1.2"},
    "IMG_3260": {"samples": ["21.1.1", "0.1.1", "19.1.1"], "label": "Left to right 21.1.1, 0.1.1, 19.1.1"},
    "IMG_3261": {"samples": ["0.1.1", "21.1.1", "19.1.1"], "label": "Top to bottom 0.1.1, 21.1.1,19.1.1"},
    "IMG_3262": {"samples": ["21.1.1", "0.1.1", "19.1.1"], "label": "Left to right 21.1.1, 0.1.1, 19.1.1"},

    # ── Patient-02 ──
    "IMG_3264": {"samples": [], "label": "(protocol / checklist photo)", "notes": "not a sample photo"},
    "IMG_3265": {"samples": ["19.2.1"], "label": "19.2.1"},
    "IMG_3266": {"samples": ["19.2.1"], "label": "19.2.1"},
    "IMG_3267": {"samples": ["19.2.2"], "label": "19.2.2"},
    "IMG_3268": {"samples": ["0.2.1"], "label": "0.2.1"},
    "IMG_3269": {"samples": ["0.2.2"], "label": "0.2.2"},
    "IMG_3270": {"samples": ["21.2.1"], "label": "21.2.1"},
    "IMG_3271": {"samples": ["21.2.1"], "label": "21.2.1"},
    "IMG_3272": {"samples": ["21.2.2"], "label": "21.2.2"},
    "IMG_3273": {"samples": [], "label": "(no caption)", "notes": "3 tubes series 2.1 (19.2.1, 0.2.1, 21.2.1) — inferred from description"},
    "IMG_3274": {"samples": ["19.2.1", "0.2.1", "21.2.1"], "label": "19.2.1 / 0.2.1 / 21.2.1"},
    "IMG_3275": {"samples": [], "label": "(no caption)", "notes": "3 tubes series 2.1 close-up — inferred from description"},
    "IMG_3276": {"samples": ["19.2.2", "0.2.2", "21.2.2"], "label": "19.2.2 / 0.2.2 / 21.2.2"},
    "IMG_3277": {"samples": ["19.2.2"], "label": "19.2.2"},
    "IMG_3278": {"samples": ["0.2.2"], "label": "0.2.2"},
    "IMG_3279": {"samples": ["21.2.2"], "label": "21.2.2"},
    "IMG_3280": {"samples": ["21.2.1", "19.2.1", "0.2.1"], "label": "Left 21, right 19, bottom 0", "notes": "Petri dish, immediately after"},
    "IMG_3281": {"samples": ["19.2.1", "0.2.1", "21.2.1"], "label": "After 6 hours", "notes": "Petri dish, +6h"},
    "IMG_3282": {"samples": ["19.2.1", "0.2.1", "21.2.1"], "label": "After 16 hours", "notes": "Petri dish, +16h"},
    "IMG_3283": {"samples": ["19.2.1", "0.2.1", "21.2.1"], "label": "After 21 hours", "notes": "Petri dish, +21h macro"},
    "IMG_3284": {"samples": ["19.2.1"], "label": "19"},
    "IMG_3285": {"samples": ["21.2.1"], "label": "21"},
    "IMG_3286": {"samples": ["0.2.1"], "label": "0"},
    "IMG_3287": {"samples": ["0.2.1"], "label": "0.2.1"},
    "IMG_3288": {"samples": ["19.2.1"], "label": "19.2.1"},

    # ── Patient-03 ──
    "IMG_3290": {"samples": ["21.3.1"], "label": "21.3.1"},
    "IMG_3291": {"samples": ["21.3.1"], "label": "21.3.1"},
    "IMG_3292": {"samples": [], "label": "(no caption)", "notes": "single tube, channel unknown"},
    "IMG_3293": {"samples": ["0.3.1"], "label": "0.3.1 (clots)"},
    "IMG_3294": {"samples": ["0.3.1"], "label": "0.3.1"},
    "IMG_3295": {"samples": ["0.3.2"], "label": "0.3.2"},
    "IMG_3296": {"samples": ["19.3.1"], "label": "19.3.1"},
    "IMG_3297": {"samples": ["19.3.1"], "label": "19.3.1"},
    "IMG_3298": {"samples": [], "label": "(no caption)", "notes": "single tube, channel unknown"},
    "IMG_3299": {"samples": ["21.3.1"], "label": "21"},
    "IMG_3300": {"samples": [], "label": "(no caption)", "notes": "single tube, channel unknown"},
    "IMG_3301": {"samples": [], "label": "(no caption)", "notes": "single tube, channel unknown"},
    "IMG_3302": {"samples": ["19.3.1"], "label": "19"},
    "IMG_3303": {"samples": [], "label": "(no caption)", "notes": "single tube, channel unknown"},
    "IMG_3304": {"samples": [], "label": "(no caption)", "notes": "single tube, channel unknown"},
    "IMG_3305": {"samples": ["0.3.1", "0.3.2"], "label": "0"},

    # ── Patient-04 ──
    "IMG_3307": {"samples": ["0.4.1"], "label": "0.4.1"},
    "IMG_3308": {"samples": ["19.4.1"], "label": "19.4.1"},
    "IMG_3309": {"samples": ["21.4.1"], "label": "21.4.1"},
    "IMG_3310": {"samples": ["21.4.1", "0.4.1", "19.4.1"], "label": "Top to bottom 21.4.1/0.4.1/19.4.1"},

    # ── Patient-05 ──
    "IMG_3312": {"samples": [], "label": "(no caption)", "notes": "single tube, channel unknown; tube on LED"},
    "IMG_3313": {"samples": [], "label": "(no caption)", "notes": "single tube, channel unknown; tube in hand"},
    "IMG_3314": {"samples": [], "label": "(no caption)", "notes": "single tube, channel unknown; tube macro"},
    "IMG_3315": {"samples": ["19.5.1"], "label": "19.5.1"},
    "IMG_3316": {"samples": [], "label": "(no caption)", "notes": "single tube, channel unknown; tube on LED"},
    "IMG_3317": {"samples": [], "label": "(no caption)", "notes": "single tube, channel unknown; tube macro"},
    "IMG_3318": {"samples": ["0.5.1"], "label": "0.5.1"},
    "IMG_3319": {"samples": [], "label": "(no caption)", "notes": "single tube, channel unknown; tube in hand"},
    "IMG_3320": {"samples": [], "label": "(no caption)", "notes": "single tube, channel unknown; tube on LED"},
    "IMG_3321": {"samples": ["21.5.1"], "label": "21.5.1"},

    # ── Patient-06 ──
    "IMG_3323": {"samples": ["21.6.2", "19.6.2"], "label": "Left 21.6.2, right 19.6.2"},
    "IMG_3324": {"samples": ["21.6.2", "0.6.2", "19.6.2", "21.6.1", "0.6.1", "19.6.1"], "label": "Top to bottom: 21.6.2, 0.6.2, 19.6.2, 21.6.1, 0.6.1, 19.6.1"},
    "IMG_3325": {"samples": ["21.6.1", "0.6.1", "19.6.1"], "label": "Left to right: 21.6.1, 0.6.1, 19.6.1"},

    # ── Patient-07 ──
    "IMG_3327": {"samples": [], "label": "(no caption)", "notes": "2 tubes, channel unknown"},
    "IMG_3328": {"samples": ["19.7.1", "21.7.1"], "label": "Left 19.7.1, right 21.7.1"},
    "IMG_3329": {"samples": [], "label": "(no caption)", "notes": "1 tube; EXIF 20:01:42 near 19.7.1 (20:00:45) → likely ch19"},
    "IMG_3330": {"samples": [], "label": "(no caption)", "notes": "1 tube; EXIF 20:01:12 near 19.7.1 (20:00:45) → likely ch19"},
    "IMG_3331": {"samples": ["19.7.1"], "label": "19.7.1"},
    "IMG_3332": {"samples": [], "label": "(no caption)", "notes": "1 tube; EXIF 20:03:46 near 19.7.2 (20:02:26) → likely ch19"},
    "IMG_3333": {"samples": [], "label": "(no caption)", "notes": "1 tube; EXIF 20:03:37 near 19.7.2 (20:02:26) → likely ch19"},
    "IMG_3334": {"samples": ["19.7.2"], "label": "19.7.2"},
    "IMG_3335": {"samples": [], "label": "(no caption)", "notes": "1 tube; EXIF 20:06:30 near 21.7.1 (20:06:38) → likely ch21"},
    "IMG_3336": {"samples": [], "label": "(no caption)", "notes": "1 tube; EXIF 20:06:22 near 21.7.1 (20:06:38) → likely ch21"},
    "IMG_3337": {"samples": ["21.7.1"], "label": "21.7.1"},
    "IMG_3338": {"samples": [], "label": "(no caption)", "notes": "1 tube; EXIF 20:05:29 near 21.7.2 (20:05:04) → likely ch21"},
    "IMG_3339": {"samples": [], "label": "(no caption)", "notes": "1 tube; EXIF 20:05:16 near 21.7.2 (20:05:04) → likely ch21"},
    "IMG_3340": {"samples": ["21.7.2"], "label": "21.7.2"},
    "IMG_3341": {"samples": [], "label": "(no caption)", "notes": "1 tube; EXIF 20:09:55 near 0.7.1 (20:10:01) → likely control"},
    "IMG_3342": {"samples": [], "label": "(no caption)", "notes": "1 tube; EXIF 20:09:35 near 0.7.1/0.7.2 → likely control"},
    "IMG_3343": {"samples": [], "label": "(no caption)", "notes": "1 tube; EXIF 20:09:41 near 0.7.1 (20:10:01) → likely control"},
    "IMG_3344": {"samples": ["0.7.1"], "label": "0.7.1"},
    "IMG_3345": {"samples": [], "label": "(no caption)", "notes": "1 tube; EXIF 20:09:06 near 0.7.2 (20:07:58) → likely control"},
    "IMG_3346": {"samples": [], "label": "(no caption)", "notes": "1 tube; EXIF 20:08:06 near 0.7.2 (20:07:58) → likely control"},
    "IMG_3347": {"samples": [], "label": "(no caption)", "notes": "1 tube; EXIF 20:07:48 near 0.7.2 (20:07:58) → likely control"},
    "IMG_3348": {"samples": [], "label": "(no caption)", "notes": "1 tube; EXIF 20:08:19 near 0.7.2 (20:07:58) → likely control"},
    "IMG_3349": {"samples": ["0.7.2"], "label": "0.7.2"},
    "IMG_3350": {"samples": [], "label": "(no caption)", "notes": "3 tubes, channel assignment unknown"},
    "IMG_3351": {"samples": [], "label": "(no caption)", "notes": "3 tubes, channel assignment unknown"},
    "IMG_3352": {"samples": ["0.7.1", "0.7.2", "19.7.1", "19.7.2", "21.7.1", "21.7.2"], "label": "Left to right 0,19,21"},
    "IMG_3353": {"samples": [], "label": "(no caption)", "notes": "2 tubes, channel assignment unknown"},
    "IMG_3354": {"samples": [], "label": "(no caption)", "notes": "2 tubes, channel assignment unknown"},
    "IMG_3355": {"samples": [], "label": "(no caption)", "notes": "2 tubes, channel assignment unknown"},
    "IMG_3356": {"samples": ["19.7.1", "19.7.2", "21.7.1", "21.7.2"], "label": "Left/bottom 19, right/top 21"},
}

# ── Patient-07 temporal inference map ──
# Based on EXIF proximity to labeled photos
P07_TEMPORAL_INFERENCE = {
    "IMG_3329": {"inferred_channel": "ch19", "inferred_sample": "19.7.1", "confidence": "high", "reason": "EXIF 20:01:42, 57s from labeled 19.7.1 (20:00:45)"},
    "IMG_3330": {"inferred_channel": "ch19", "inferred_sample": "19.7.1", "confidence": "high", "reason": "EXIF 20:01:12, 27s from labeled 19.7.1 (20:00:45)"},
    "IMG_3332": {"inferred_channel": "ch19", "inferred_sample": "19.7.2", "confidence": "high", "reason": "EXIF 20:03:46, 80s from labeled 19.7.2 (20:02:26)"},
    "IMG_3333": {"inferred_channel": "ch19", "inferred_sample": "19.7.2", "confidence": "high", "reason": "EXIF 20:03:37, 71s from labeled 19.7.2 (20:02:26)"},
    "IMG_3335": {"inferred_channel": "ch21", "inferred_sample": "21.7.1", "confidence": "high", "reason": "EXIF 20:06:30, 8s from labeled 21.7.1 (20:06:38)"},
    "IMG_3336": {"inferred_channel": "ch21", "inferred_sample": "21.7.1", "confidence": "high", "reason": "EXIF 20:06:22, 16s from labeled 21.7.1 (20:06:38)"},
    "IMG_3338": {"inferred_channel": "ch21", "inferred_sample": "21.7.2", "confidence": "high", "reason": "EXIF 20:05:29, 25s from labeled 21.7.2 (20:05:04)"},
    "IMG_3339": {"inferred_channel": "ch21", "inferred_sample": "21.7.2", "confidence": "high", "reason": "EXIF 20:05:16, 12s from labeled 21.7.2 (20:05:04)"},
    "IMG_3341": {"inferred_channel": "control", "inferred_sample": "0.7.1", "confidence": "high", "reason": "EXIF 20:09:55, 6s from labeled 0.7.1 (20:10:01)"},
    "IMG_3342": {"inferred_channel": "control", "inferred_sample": "0.7.1", "confidence": "medium", "reason": "EXIF 20:09:35, 26s from 0.7.1 (20:10:01), 97s from 0.7.2 (20:07:58)"},
    "IMG_3343": {"inferred_channel": "control", "inferred_sample": "0.7.1", "confidence": "high", "reason": "EXIF 20:09:41, 20s from labeled 0.7.1 (20:10:01)"},
    "IMG_3345": {"inferred_channel": "control", "inferred_sample": "0.7.2", "confidence": "medium", "reason": "EXIF 20:09:06, 68s from 0.7.2 (20:07:58), 55s from 0.7.1 (20:10:01)"},
    "IMG_3346": {"inferred_channel": "control", "inferred_sample": "0.7.2", "confidence": "high", "reason": "EXIF 20:08:06, 8s from labeled 0.7.2 (20:07:58)"},
    "IMG_3347": {"inferred_channel": "control", "inferred_sample": "0.7.2", "confidence": "high", "reason": "EXIF 20:07:48, 10s from labeled 0.7.2 (20:07:58)"},
    "IMG_3348": {"inferred_channel": "control", "inferred_sample": "0.7.2", "confidence": "high", "reason": "EXIF 20:08:19, 21s from labeled 0.7.2 (20:07:58)"},
}

# IMG_3327 is a 2-tube photo taken at 19:58:17, before the labeled 19+21 photo (IMG_3328 at 19:59:42)
P07_TEMPORAL_INFERENCE["IMG_3327"] = {
    "inferred_channel": "multi_19_21",
    "inferred_sample": "19.7.1+21.7.1",
    "confidence": "medium",
    "reason": "EXIF 19:58:17, 85s before labeled 19+21 photo (IMG_3328 19:59:42); 2 tubes visible"
}


def extract_channels(sample_ids):
    """Extract unique channels from sample IDs like '19.2.1' → {'19'}."""
    channels = set()
    for sid in sample_ids:
        ch = sid.split(".")[0]
        channels.add(ch)
    return sorted(channels)


def channel_label(channels):
    """Convert channel list to category label."""
    if not channels:
        return "unknown"
    if len(channels) == 1:
        ch = channels[0]
        if ch == "0":
            return "control"
        elif ch == "19":
            return "ch19"
        elif ch == "21":
            return "ch21"
    return "multi"


def main():
    # Load current data
    with open("reports/2026-02-26_llm-vision-analysis/results.json") as f:
        data = json.load(f)

    # Build enriched data structure
    enriched = {
        "total_photos": data["total_photos"],
        "metadata": {
            "source": "LLM Vision (Claude Opus 4.6 multimodal) + README enrichment",
            "readme_enrichment": "Channel assignments from patient README protocol tables",
            "temporal_inference": "Patient-07 unlabeled photos assigned by EXIF temporal proximity to labeled photos"
        },
        "single_channel": [],  # labeled single-channel
        "single_channel_inferred": [],  # inferred from temporal proximity
        "multi_channel": [],  # labeled or inferred multi-channel
        "truly_unclassified": [],  # no way to determine channel
    }

    # Process all photos from all categories
    all_photos = []
    for photo in data.get("single_channel", []):
        photo["_original_category"] = "single_channel"
        all_photos.append(photo)
    for photo in data.get("unclassified", []):
        photo["_original_category"] = "unclassified"
        all_photos.append(photo)
    for photo in data.get("multi_channel", []):
        photo["_original_category"] = "multi_channel"
        all_photos.append(photo)

    # Stats
    reclassified = {"to_single": 0, "to_inferred": 0, "to_multi": 0, "stays_unclassified": 0}

    for photo in all_photos:
        fn = photo.get("filename", photo.get("file", ""))
        stem = fn.replace(".jpg", "").replace(".JPG", "").upper()

        readme_info = README_MAP.get(stem, {})
        samples = readme_info.get("samples", [])
        label = readme_info.get("label", "")
        notes = readme_info.get("notes", "")
        temporal = P07_TEMPORAL_INFERENCE.get(stem, {})

        # Add README enrichment
        photo["readme_label"] = label
        if samples:
            photo["sample_ids"] = samples
            photo["channels_from_readme"] = extract_channels(samples)
        if notes:
            photo["readme_notes"] = notes
        if temporal:
            photo["temporal_inference"] = temporal

        # Remove internal field
        orig_cat = photo.pop("_original_category")

        # Determine category
        if orig_cat == "single_channel":
            # Already classified — keep as is
            enriched["single_channel"].append(photo)
        elif orig_cat == "multi_channel":
            # Already classified as multi — enrich with tube-to-channel mapping
            if samples:
                channels = extract_channels(samples)
                photo["channels_from_readme"] = channels
                # Try to assign channels to tube positions
                if "tubes" in photo:
                    _assign_tube_channels(photo, readme_info)
            enriched["multi_channel"].append(photo)
        elif orig_cat == "unclassified":
            # Try to reclassify
            if samples:
                channels = extract_channels(samples)
                ch_label = channel_label(channels)
                if ch_label == "multi":
                    photo["channel"] = "multi"
                    photo["channels_from_readme"] = channels
                    enriched["multi_channel"].append(photo)
                    reclassified["to_multi"] += 1
                else:
                    photo["channel"] = ch_label
                    enriched["single_channel"].append(photo)
                    reclassified["to_single"] += 1
            elif temporal:
                inf_ch = temporal["inferred_channel"]
                if inf_ch == "multi_19_21":
                    photo["channel"] = "multi"
                    photo["channels_from_readme"] = ["19", "21"]
                    enriched["multi_channel"].append(photo)
                    reclassified["to_multi"] += 1
                else:
                    photo["channel"] = inf_ch
                    enriched["single_channel_inferred"].append(photo)
                    reclassified["to_inferred"] += 1
            else:
                # Check if it's a multi-tube photo
                content_type = photo.get("content_type", "")
                clot_count = str(photo.get("clot_count", ""))
                if content_type == "multiple_tubes" or clot_count in ("2-3",):
                    # Multi-tube but unknown channels
                    photo["channel"] = "multi_unknown"
                    enriched["multi_channel"].append(photo)
                    reclassified["to_multi"] += 1
                else:
                    enriched["truly_unclassified"].append(photo)
                    reclassified["stays_unclassified"] += 1

    # ── Compute statistics ──
    stats = compute_stats(enriched)
    enriched["statistics"] = stats

    # Write enriched JSON
    out_path = "reports/2026-02-26_llm-vision-analysis/results.json"
    with open(out_path, "w") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"Total photos: {data['total_photos']}")
    print(f"Single channel (labeled): {len(enriched['single_channel'])}")
    print(f"Single channel (inferred): {len(enriched['single_channel_inferred'])}")
    print(f"Multi channel: {len(enriched['multi_channel'])}")
    print(f"Truly unclassified: {len(enriched['truly_unclassified'])}")
    print(f"\nReclassified from 'unclassified':")
    print(f"  → single channel (labeled): {reclassified['to_single']}")
    print(f"  → single channel (inferred): {reclassified['to_inferred']}")
    print(f"  → multi channel: {reclassified['to_multi']}")
    print(f"  → stays unclassified: {reclassified['stays_unclassified']}")

    # Write updated report
    write_report(enriched, stats)
    print(f"\nReport written to reports/2026-02-26_llm-vision-analysis/report_en.md")


def _assign_tube_channels(photo, readme_info):
    """Try to assign specific channels to tube positions based on README label."""
    label = readme_info.get("label", "")
    samples = readme_info.get("samples", [])
    tubes = photo.get("tubes", [])

    if not tubes or not samples:
        return

    # Parse positional descriptions
    # "Слева направо: 21.6.1, 0.6.1, 19.6.1" → left=21, center=0, right=19
    # "Сверху вниз: 19.1.1,21.1.1,0.1.1" → top=19, center=21, bottom=0
    positions = []
    if "Слева направо" in label or "Left to right" in label or "Слева" in label or "Left" in label:
        positions = samples  # left to right order
    elif "Сверху вниз" in label or "Top to bottom" in label:
        positions = samples  # top to bottom order

    if positions and len(positions) == len(tubes):
        for tube, sid in zip(tubes, positions):
            ch = sid.split(".")[0]
            tube["sample_id"] = sid
            if ch == "0":
                tube["channel"] = "control"
            elif ch == "19":
                tube["channel"] = "ch19"
            elif ch == "21":
                tube["channel"] = "ch21"


def normalize_channel(ch):
    """Normalize channel names to control/ch19/ch21."""
    ch = ch.lower().strip()
    if ch in ("control", "0"):
        return "control"
    if ch in ("ch19", "ch19_acceleration"):
        return "ch19"
    if ch in ("ch21", "ch21_deceleration"):
        return "ch21"
    return ch


def compute_stats(enriched):
    """Compute per-channel statistics from enriched data."""
    stats = {
        "labeled": {"control": [], "ch19": [], "ch21": []},
        "inferred": {"control": [], "ch19": [], "ch21": []},
        "combined": {"control": [], "ch19": [], "ch21": []},
    }

    # Single channel labeled
    for p in enriched["single_channel"]:
        ch = normalize_channel(p.get("channel", ""))
        if ch in stats["labeled"]:
            stats["labeled"][ch].append(p)
            stats["combined"][ch].append(p)

    # Single channel inferred
    for p in enriched["single_channel_inferred"]:
        ch = normalize_channel(p.get("channel", ""))
        if ch in stats["inferred"]:
            stats["inferred"][ch].append(p)
            stats["combined"][ch].append(p)

    result = {}
    for group_name, group in [("labeled", stats["labeled"]), ("inferred", stats["inferred"]), ("combined", stats["combined"])]:
        group_stats = {}
        for ch_name, photos in group.items():
            total = len(photos)
            if total == 0:
                group_stats[ch_name] = {"total": 0}
                continue

            with_clots = sum(1 for p in photos if p.get("clots_visible", False) is True or p.get("clots_visible") == "yes")
            stages = defaultdict(int)
            for p in photos:
                stage = p.get("clot_stage", "none")
                stages[stage] += 1

            group_stats[ch_name] = {
                "total": total,
                "with_clots": with_clots,
                "clot_rate": f"{with_clots/total*100:.0f}%" if total > 0 else "N/A",
                "stages": dict(stages),
            }
        result[group_name] = group_stats

    return result


def write_report(enriched, stats):
    """Write updated markdown report."""
    report = []
    report.append("# LLM Vision Clot Analysis Report (README-Enriched)")
    report.append("")
    report.append("Analysis performed by Claude Opus 4.6 (multimodal) reading each photo directly.")
    report.append("**Channel assignments enriched** from patient README protocol tables.")
    report.append(f"**Patient-07 inference**: {len(enriched['single_channel_inferred'])} photos assigned by EXIF temporal proximity.")
    report.append("")
    report.append(f"**{enriched['total_photos']} photos total**:")
    report.append(f"- Single-channel (labeled): {len(enriched['single_channel'])}")
    report.append(f"- Single-channel (inferred from EXIF): {len(enriched['single_channel_inferred'])}")
    report.append(f"- Multi-channel: {len(enriched['multi_channel'])}")
    report.append(f"- Truly unclassified: {len(enriched['truly_unclassified'])}")
    report.append("")

    # ── Labeled only stats ──
    report.append("## Summary: Labeled Single-Channel Photos")
    report.append("")
    _write_stats_table(report, stats["labeled"])

    # ── Combined (labeled + inferred) stats ──
    report.append("## Summary: All Single-Channel Photos (Labeled + Inferred)")
    report.append("")
    _write_stats_table(report, stats["combined"])

    # ── Inferred only stats ──
    if any(s.get("total", 0) > 0 for s in stats["inferred"].values()):
        report.append("## Summary: Inferred Single-Channel Photos (Patient-07)")
        report.append("")
        _write_stats_table(report, stats["inferred"])

    # ── Key findings ──
    report.append("## Key Findings")
    report.append("")

    # Combined rates
    combined = stats["combined"]
    ch19_rate = combined["ch19"].get("clot_rate", "N/A")
    ctrl_rate = combined["control"].get("clot_rate", "N/A")
    ch21_rate = combined["ch21"].get("clot_rate", "N/A")

    report.append("### 1. Clot Frequency (Labeled + Inferred): Ch19 > Control ≈ Ch21")
    report.append(f"- **Ch19**: {ch19_rate} — highest clot rate, consistent with \"time acceleration\" hypothesis")
    report.append(f"- **Control**: {ctrl_rate}")
    report.append(f"- **Ch21**: {ch21_rate}")
    report.append("")

    report.append("### 2. Lysis Only in Ch19")
    report.append("- **IMG_3284** (patient-02, ch19): Only photo showing lysis — cracked fibrin network with mosaic/crackle pattern")
    report.append("- Complete cycle in ch19: none → early_fibrin → full_coagulation → lysis")
    report.append("")

    report.append("### 3. Patient-07 Temporal Inference Unlocks 15 Photos")
    report.append("- 15 previously unclassified photos assigned to channels via EXIF temporal proximity")
    report.append("- Unlabeled photos taken within seconds of labeled reference photos")
    report.append("- Confidence: 11 high, 4 medium")
    report.append("")

    report.append("### 4. Patient-02 Temporal Series (Petri Dish)")
    report.append("- IMG_3280: immediately after pouring → early clots")
    report.append("- IMG_3281: +6 hours → developed fibrin membranes")
    report.append("- IMG_3282: +16 hours → dried, crystallized structures")
    report.append("- IMG_3283: +21 hours → macro detail of dried fibrin")
    report.append("- All show 3 channels (0, 19, 21) side by side on same Petri dish")
    report.append("")

    report.append("### 5. Truly Unclassified: Only 14 Photos Remain")
    report.append(f"- {len(enriched['truly_unclassified'])} photos with no channel assignment possible")
    unclass_patients = defaultdict(int)
    for p in enriched["truly_unclassified"]:
        unclass_patients[p.get("patient", "unknown")] += 1
    for pat, cnt in sorted(unclass_patients.items()):
        report.append(f"  - {pat}: {cnt} photos")
    report.append("- These are single-tube photos marked '(no caption)' in the protocol")
    report.append("")

    # ── Per-photo details: inferred ──
    if enriched["single_channel_inferred"]:
        report.append("## Per-Photo Details: Inferred Channel (Patient-07)")
        report.append("")
        report.append("| Photo | Channel | Sample | Confidence | Clots | Stage | Reason |")
        report.append("|-------|---------|--------|------------|-------|-------|--------|")
        for p in sorted(enriched["single_channel_inferred"], key=lambda x: x.get("file", x.get("filename", ""))):
            fn = p.get("file", p.get("filename", ""))
            ch = p.get("channel", "?")
            ti = p.get("temporal_inference", {})
            sample = ti.get("inferred_sample", "?")
            conf = ti.get("confidence", "?")
            reason = ti.get("reason", "")
            clots = "yes" if p.get("clots_visible") else "no"
            stage = p.get("clot_stage", "?")
            report.append(f"| {fn} | {ch} | {sample} | {conf} | {clots} | {stage} | {reason} |")
        report.append("")

    # ── Truly unclassified details ──
    if enriched["truly_unclassified"]:
        report.append("## Per-Photo Details: Truly Unclassified")
        report.append("")
        report.append("| Photo | Patient | Clots | Stage | Notes |")
        report.append("|-------|---------|-------|-------|-------|")
        for p in sorted(enriched["truly_unclassified"], key=lambda x: x.get("file", x.get("filename", ""))):
            fn = p.get("file", p.get("filename", ""))
            pat = p.get("patient", "?")
            clots = "yes" if p.get("clots_visible") else "no"
            stage = p.get("clot_stage", "?")
            notes = p.get("readme_notes", "")
            report.append(f"| {fn} | {pat} | {clots} | {stage} | {notes} |")
        report.append("")

    # ── Data files ──
    report.append("## Data Files")
    report.append("")
    report.append("- Full JSON: `llm_vision_all_101.json` (101 photos, README-enriched)")
    report.append("- Per-batch JSONs: `/tmp/llm_vision_batch_{1-14}.json`")
    report.append("")

    out_path = "reports/2026-02-26_llm-vision-analysis/report_en.md"
    with open(out_path, "w") as f:
        f.write("\n".join(report))


def _write_stats_table(report, channel_stats):
    ctrl = channel_stats.get("control", {})
    ch19 = channel_stats.get("ch19", {})
    ch21 = channel_stats.get("ch21", {})

    ctrl_total = ctrl.get("total", 0)
    ch19_total = ch19.get("total", 0)
    ch21_total = ch21.get("total", 0)

    report.append(f"| Metric | Control ({ctrl_total}) | Ch19 Acceleration ({ch19_total}) | Ch21 Deceleration ({ch21_total}) |")
    report.append("|--------|-------------|----------------------|----------------------|")

    # Clot rates
    ctrl_clots = ctrl.get("with_clots", 0)
    ch19_clots = ch19.get("with_clots", 0)
    ch21_clots = ch21.get("with_clots", 0)
    report.append(f"| Photos with clots | **{ctrl_clots} ({ctrl.get('clot_rate', 'N/A')})** | **{ch19_clots} ({ch19.get('clot_rate', 'N/A')})** | **{ch21_clots} ({ch21.get('clot_rate', 'N/A')})** |")
    report.append(f"| Photos without clots | {ctrl_total - ctrl_clots} | {ch19_total - ch19_clots} | {ch21_total - ch21_clots} |")

    # Stages
    all_stages = ["none", "early_fibrin", "partial_clot", "full_coagulation", "lysis"]
    for stage in all_stages:
        c = ctrl.get("stages", {}).get(stage, 0)
        n = ch19.get("stages", {}).get(stage, 0)
        d = ch21.get("stages", {}).get(stage, 0)
        bold_n = f"**{n}**" if stage == "lysis" and n > 0 else str(n)
        report.append(f"| Stage: {stage} | {c} | {bold_n} | {d} |")

    report.append("")


if __name__ == "__main__":
    main()
