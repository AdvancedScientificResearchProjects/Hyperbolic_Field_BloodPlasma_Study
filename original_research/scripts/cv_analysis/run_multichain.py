#!/usr/bin/env python3
"""Multi-chain pipeline: SAM-2 segmentation → DINOv2/SigLIP2 on cropped plasma.

Hypothesis: removing tube/background/label from the image should give
cleaner features for channel classification.

Pipeline:
  1. SAM-2 segments plasma region (mask)
  2. Crop bounding box of plasma mask
  3. DINOv2-large extracts embeddings from crop
  4. SigLIP2-SO400M zero-shot on crop
  5. Linear probe on DINOv2 embeddings (5-fold CV)
  6. Compare with full-photo results
"""

import json
import time
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict, StratifiedKFold
from sklearn.preprocessing import StandardScaler

PROJECT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT / "data"
OUTPUT_DIR = Path(__file__).resolve().parent / "ml_results_v3_multichain"
OUTPUT_DIR.mkdir(exist_ok=True)

PLASMA_LABELS = [
    "clear transparent blood plasma",
    "turbid cloudy blood plasma",
    "blood plasma with fibrin clots",
    "blood plasma with sediment",
    "hemolyzed blood plasma",
    "normal blood plasma sample",
    "blood plasma with no fibrin formation",
    "blood plasma with early fibrin strand formation",
    "blood plasma with partially formed fibrin clot",
    "blood plasma with dense mature fibrin clot",
    "blood plasma showing fibrinolysis with dissolving clot",
]

CH_NAMES = {0: "control", 19: "ch19", 21: "ch21"}
device = "cuda" if torch.cuda.is_available() else "cpu"


def load_photos_with_channels():
    """Load all photos and map to channels."""
    data = json.loads((PROJECT / "processed/en/all_patients.json").read_text())
    photos = []
    for p in data["patients"]:
        patient = p["patient_id"]
        for photo in p["photos"]:
            fn = photo["filename"].replace(".HEIC", "").replace(".heic", "").replace(".JPG", "").replace(".jpg", "")
            samples = photo.get("samples_shown", [])
            channel = None
            if len(samples) == 1:
                try:
                    channel = int(samples[0].split(".")[0])
                except ValueError:
                    pass

            jpg_path = DATA_DIR / f"patient-{patient}" / "photos" / "jpg" / f"{fn}.jpg"
            if not jpg_path.exists():
                jpg_path = DATA_DIR / f"patient-{patient}" / "photos" / "jpg" / f"{fn}.jpeg"
            if jpg_path.exists():
                photos.append({
                    "filename": fn,
                    "patient": patient,
                    "channel": channel,
                    "path": jpg_path,
                })
    return photos


def segment_plasma_crop(img_pil: Image.Image) -> Image.Image | None:
    """Use HSV-based plasma segmentation to crop just the plasma region.

    SAM-2 is slow and heavy. Since we already know plasma is yellowish,
    HSV thresholding gives a good enough mask for cropping.
    """
    img_bgr = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    # Plasma HSV range (yellowish liquid)
    lower = np.array([12, 35, 60])
    upper = np.array([50, 255, 230])
    mask = cv2.inRange(hsv, lower, upper)

    # Morphological cleanup
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=3)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)

    # Keep largest component
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if num_labels < 2:
        return None
    areas = stats[1:, cv2.CC_STAT_AREA]
    largest = int(areas.argmax()) + 1
    mask = np.zeros_like(mask)
    mask[labels == largest] = 255

    area = int((mask > 0).sum())
    if area < 5000:
        return None

    # Crop bounding box with small padding
    ys, xs = np.where(mask > 0)
    pad = 20
    y1 = max(0, ys.min() - pad)
    y2 = min(img_bgr.shape[0], ys.max() + pad)
    x1 = max(0, xs.min() - pad)
    x2 = min(img_bgr.shape[1], xs.max() + pad)

    crop = img_bgr[y1:y2, x1:x2]
    crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
    return Image.fromarray(crop_rgb)


def run_siglip2_so400m(photos, crops):
    """Zero-shot on cropped plasma."""
    print("\n" + "=" * 65)
    print("  SigLIP2-SO400M on CROPPED PLASMA")
    print("=" * 65)

    from transformers import AutoModel, AutoProcessor

    processor = AutoProcessor.from_pretrained("google/siglip2-so400m-patch14-384")
    model = AutoModel.from_pretrained(
        "google/siglip2-so400m-patch14-384",
        torch_dtype=torch.bfloat16,
    ).to(device).eval()

    results = []
    texts = [f"A photo of {label}" for label in PLASMA_LABELS]

    for i, (p, crop) in enumerate(zip(photos, crops)):
        if crop is None:
            results.append(None)
            continue

        inputs = processor(text=texts, images=crop, padding="max_length", max_length=64, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.inference_mode():
            outputs = model(**inputs)
        scores = outputs.logits_per_image.softmax(dim=-1).squeeze().cpu().float().tolist()

        labeled = sorted(zip(PLASMA_LABELS, scores), key=lambda x: -x[1])
        coag_score = sum(s for l, s in labeled if ("clot" in l) or ("fibrin" in l and "no fibrin" not in l))

        results.append({
            "filename": p["filename"],
            "channel": p["channel"],
            "top_label": labeled[0][0],
            "top_score": round(labeled[0][1], 4),
            "coag_score": round(coag_score, 4),
            "labels": [{"label": l, "score": round(s, 4)} for l, s in labeled[:5]],
        })

        if (i + 1) % 10 == 0 or i == 0:
            print(f"  [{i+1}/{len(photos)}] {p['filename']} → {labeled[0][0][:35]}")

    del model, processor
    torch.cuda.empty_cache()
    return results


def run_dinov2_probe(photos, crops):
    """DINOv2-large on cropped plasma + linear probe."""
    print("\n" + "=" * 65)
    print("  DINOv2-large on CROPPED PLASMA + Linear Probe")
    print("=" * 65)

    from transformers import AutoImageProcessor, AutoModel

    processor = AutoImageProcessor.from_pretrained("facebook/dinov2-large")
    model = AutoModel.from_pretrained(
        "facebook/dinov2-large",
        torch_dtype=torch.bfloat16,
    ).to(device).eval()

    embeddings = []
    valid_idx = []
    for i, (p, crop) in enumerate(zip(photos, crops)):
        if crop is None:
            embeddings.append(None)
            continue

        inputs = processor(images=crop, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.inference_mode():
            outputs = model(**inputs)
        emb = outputs.last_hidden_state[:, 0, :].squeeze().cpu().float()
        embeddings.append(emb)
        valid_idx.append(i)
        if (i + 1) % 20 == 0 or i == 0:
            print(f"  Embedding [{i+1}/{len(photos)}] {p['filename']}")

    del model, processor
    torch.cuda.empty_cache()

    # Probe on labeled single-channel photos
    labeled_idx = [i for i in valid_idx if photos[i]["channel"] in (0, 19, 21)]
    if len(labeled_idx) < 10:
        print("  Not enough labeled data for probe")
        return None

    label_map = {0: 0, 19: 1, 21: 2}
    X_labeled = np.stack([embeddings[i].numpy() for i in labeled_idx])
    y = np.array([label_map[photos[i]["channel"]] for i in labeled_idx])

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_labeled)

    clf = LogisticRegression(max_iter=1000, C=1.0)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    y_pred = cross_val_predict(clf, X_scaled, y, cv=cv)

    print(f"\n  5-Fold CV results (n={len(y)}):")
    acc = (y_pred == y).mean()
    print(f"  Overall accuracy: {acc:.1%}")

    for ch_val, ch_name in enumerate(["control", "ch19", "ch21"]):
        mask = y == ch_val
        ch_acc = (y_pred[mask] == y[mask]).mean()
        n = mask.sum()
        print(f"  {ch_name:10s}: {ch_acc:.1%} ({(y_pred[mask] == ch_val).sum()}/{n})")

    print(f"\n  Confusion (true → predicted):")
    for true_val, true_name in enumerate(["control", "ch19", "ch21"]):
        row = []
        for pred_val, pred_name in enumerate(["control", "ch19", "ch21"]):
            count = ((y == true_val) & (y_pred == pred_val)).sum()
            row.append(f"{pred_name}={count}")
        print(f"    {true_name:10s}: {', '.join(row)}")

    return {
        "accuracy": round(float(acc), 4),
        "n_samples": int(len(y)),
        "per_channel": {
            ch_name: {
                "n": int((y == ch_val).sum()),
                "accuracy": round(float((y_pred[y == ch_val] == ch_val).mean()), 4),
            }
            for ch_val, ch_name in enumerate(["control", "ch19", "ch21"])
        },
    }


def run_sam2_multichain(photos, crops):
    """Full SAM-2 segmentation + DINOv2 on SAM-2 mask crop (not HSV)."""
    print("\n" + "=" * 65)
    print("  SAM-2 segmentation → DINOv2-large (true multi-chain)")
    print("=" * 65)

    # Import segment.py
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from segment import run_sam2_raw, _find_plasma_mask, SegmentParams

    from transformers import AutoImageProcessor, AutoModel

    processor = AutoImageProcessor.from_pretrained("facebook/dinov2-large")
    model = AutoModel.from_pretrained(
        "facebook/dinov2-large",
        torch_dtype=torch.bfloat16,
    ).to(device).eval()

    params = SegmentParams()
    embeddings = []
    valid_idx = []

    for i, p in enumerate(photos):
        img_pil = Image.open(p["path"]).convert("RGB")
        img_bgr = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

        # Resize for SAM-2
        w, h = img_pil.size
        scale = min(1.0, 1024 / max(w, h))
        if scale < 1.0:
            img_small = img_pil.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        else:
            img_small = img_pil

        # Run SAM-2
        sam2_masks = run_sam2_raw(img_small, params.sam2_iou_thresh, params.sam2_stability_thresh)

        if sam2_masks:
            img_small_bgr = cv2.cvtColor(np.array(img_small), cv2.COLOR_RGB2BGR)
            plasma_mask, mask_info = _find_plasma_mask(img_small_bgr, sam2_masks, params)
        else:
            plasma_mask = None

        if plasma_mask is not None:
            # Crop plasma region
            ys, xs = np.where(plasma_mask > 0)
            pad = 10
            y1 = max(0, ys.min() - pad)
            y2 = min(img_small_bgr.shape[0], ys.max() + pad)
            x1 = max(0, xs.min() - pad)
            x2 = min(img_small_bgr.shape[1], xs.max() + pad)
            crop = img_small_bgr[y1:y2, x1:x2]
            crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
            crop_pil = Image.fromarray(crop_rgb)
        else:
            # Fallback to HSV crop
            crop_pil = crops[i] if i < len(crops) else None

        if crop_pil is None:
            embeddings.append(None)
            continue

        inputs = processor(images=crop_pil, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.inference_mode():
            outputs = model(**inputs)
        emb = outputs.last_hidden_state[:, 0, :].squeeze().cpu().float()
        embeddings.append(emb)
        valid_idx.append(i)

        if (i + 1) % 10 == 0 or i == 0:
            src = "SAM-2" if plasma_mask is not None else "HSV"
            print(f"  [{i+1}/{len(photos)}] {p['filename']} ({src})")

    del model, processor
    torch.cuda.empty_cache()

    # Probe
    labeled_idx = [i for i in valid_idx if photos[i]["channel"] in (0, 19, 21)]
    if len(labeled_idx) < 10:
        print("  Not enough labeled data")
        return None

    label_map = {0: 0, 19: 1, 21: 2}
    X_labeled = np.stack([embeddings[i].numpy() for i in labeled_idx])
    y = np.array([label_map[photos[i]["channel"]] for i in labeled_idx])

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_labeled)

    clf = LogisticRegression(max_iter=1000, C=1.0)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    y_pred = cross_val_predict(clf, X_scaled, y, cv=cv)

    acc = (y_pred == y).mean()
    print(f"\n  SAM-2 → DINOv2 probe: {acc:.1%} accuracy (n={len(y)})")

    for ch_val, ch_name in enumerate(["control", "ch19", "ch21"]):
        mask = y == ch_val
        ch_acc = (y_pred[mask] == y[mask]).mean()
        n = mask.sum()
        print(f"  {ch_name:10s}: {ch_acc:.1%} ({(y_pred[mask] == ch_val).sum()}/{n})")

    return {
        "accuracy": round(float(acc), 4),
        "n_samples": int(len(y)),
    }


def channel_analysis(results, model_name):
    """Print channel breakdown."""
    print(f"\n  Channel Analysis ({model_name}):")
    ch_scores = defaultdict(list)
    ch_labels = defaultdict(Counter)

    for r in results:
        if r is None:
            continue
        ch = r.get("channel")
        if ch is None:
            continue
        ch_name = CH_NAMES.get(ch, f"ch{ch}")
        if "coag_score" in r:
            ch_scores[ch_name].append(r["coag_score"])
        if "top_label" in r:
            ch_labels[ch_name][r["top_label"]] += 1

    if ch_scores:
        print(f"\n    Coagulation scores by channel:")
        for ch_name in ("control", "ch19", "ch21"):
            scores = ch_scores.get(ch_name, [])
            if scores:
                avg = sum(scores) / len(scores)
                print(f"    {ch_name:<10} n={len(scores):3d}  avg={avg:.4f}  min={min(scores):.4f}  max={max(scores):.4f}")

    if ch_labels:
        for ch_name in ("control", "ch19", "ch21"):
            labels = ch_labels.get(ch_name, Counter())
            total = sum(labels.values())
            if total == 0:
                continue
            print(f"\n    {ch_name} ({total} photos):")
            for label, count in labels.most_common(4):
                print(f"      {count:3d} ({count/total*100:5.1f}%)  {label}")


def main():
    photos = load_photos_with_channels()
    print(f"Loaded {len(photos)} photos")

    # Step 1: Segment and crop all photos
    print("\n" + "=" * 65)
    print("  Step 1: HSV Plasma Segmentation")
    print("=" * 65)

    crops = []
    success = 0
    for i, p in enumerate(photos):
        img = Image.open(p["path"]).convert("RGB")
        crop = segment_plasma_crop(img)
        crops.append(crop)
        if crop is not None:
            success += 1
        if (i + 1) % 20 == 0 or i == 0:
            status = f"{crop.size[0]}×{crop.size[1]}" if crop else "FAIL"
            print(f"  [{i+1}/{len(photos)}] {p['filename']} → {status}")

    print(f"  Segmented: {success}/{len(photos)} ({success/len(photos)*100:.0f}%)")

    # Step 2: SigLIP2-SO400M on crops
    t0 = time.time()
    siglip_results = run_siglip2_so400m(photos, crops)
    print(f"  Done in {time.time()-t0:.1f}s")
    channel_analysis(siglip_results, "SigLIP2-SO400M (cropped)")

    valid_siglip = [r for r in siglip_results if r is not None]
    (OUTPUT_DIR / "siglip2_so400m_cropped.json").write_text(json.dumps(valid_siglip, indent=2))

    # Step 3: DINOv2-large probe on HSV crops
    t0 = time.time()
    dino_hsv = run_dinov2_probe(photos, crops)
    print(f"  Done in {time.time()-t0:.1f}s")

    if dino_hsv:
        (OUTPUT_DIR / "dinov2_hsv_crop_probe.json").write_text(json.dumps(dino_hsv, indent=2))

    # Step 4: SAM-2 → DINOv2 (true multi-chain)
    t0 = time.time()
    dino_sam2 = run_sam2_multichain(photos, crops)
    print(f"  Done in {time.time()-t0:.1f}s")

    if dino_sam2:
        (OUTPUT_DIR / "dinov2_sam2_crop_probe.json").write_text(json.dumps(dino_sam2, indent=2))

    # Summary
    print("\n" + "=" * 65)
    print("  COMPARISON: Full Photo vs Cropped Plasma")
    print("=" * 65)
    v2_file = Path(__file__).resolve().parent / "ml_results_v2" / "dinov2_large_probe.json"
    if v2_file.exists():
        v2_data = json.loads(v2_file.read_text())
        v2_acc = v2_data.get("accuracy", "N/A")
        print(f"  DINOv2-large full photo:       {v2_acc:.1%} (from v2 run)")
    else:
        print(f"  DINOv2-large full photo:       (v2 results not found)")
    if dino_hsv:
        print(f"  DINOv2-large HSV crop:         {dino_hsv['accuracy']:.1%}")
    if dino_sam2:
        print(f"  DINOv2-large SAM-2 crop:       {dino_sam2['accuracy']:.1%}")
    print(f"  Chance baseline:               33.3%")

    print(f"\nResults saved to: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
