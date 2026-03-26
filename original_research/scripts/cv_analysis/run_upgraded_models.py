#!/usr/bin/env python3
"""Run upgraded models: SigLIP2-SO400M (zero-shot) + DINOv2-large (linear probe).

Compares results by channel (control / ch19 / ch21).
"""

import json
import time
from collections import Counter, defaultdict
from pathlib import Path

import torch
from PIL import Image

PROJECT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT / "data"
OUTPUT_DIR = Path(__file__).resolve().parent / "ml_results_v2"
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
                clots = photo.get("visual_description", {}).get("plasma", {}).get("clots", False)
                photos.append({
                    "filename": fn,
                    "patient": patient,
                    "channel": channel,
                    "path": jpg_path,
                    "has_clots": clots,
                })
    return photos


def run_siglip2_so400m(photos):
    """Zero-shot classification with SigLIP2-SO400M-384."""
    print("\n" + "=" * 65)
    print("  SigLIP2-SO400M-patch14-384 (400M params, 384px)")
    print("=" * 65)

    from transformers import AutoModel, AutoProcessor

    processor = AutoProcessor.from_pretrained("google/siglip2-so400m-patch14-384")
    model = AutoModel.from_pretrained(
        "google/siglip2-so400m-patch14-384",
        torch_dtype=torch.bfloat16,
    ).to(device).eval()

    results = []
    texts = [f"A photo of {label}" for label in PLASMA_LABELS]

    for i, p in enumerate(photos):
        img = Image.open(p["path"]).convert("RGB")
        inputs = processor(text=texts, images=img, padding="max_length", max_length=64, return_tensors="pt")
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


def run_dinov2_large_probe(photos):
    """Extract DINOv2-large embeddings and train linear probe."""
    print("\n" + "=" * 65)
    print("  DINOv2-large (307M params) + Linear Probe")
    print("=" * 65)

    from transformers import AutoImageProcessor, AutoModel

    processor = AutoImageProcessor.from_pretrained("facebook/dinov2-large")
    model = AutoModel.from_pretrained(
        "facebook/dinov2-large",
        torch_dtype=torch.bfloat16,
    ).to(device).eval()

    # Extract embeddings
    embeddings = []
    for i, p in enumerate(photos):
        img = Image.open(p["path"]).convert("RGB")
        inputs = processor(images=img, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.inference_mode():
            outputs = model(**inputs)
        emb = outputs.last_hidden_state[:, 0, :].squeeze().cpu().float()
        embeddings.append(emb)
        if (i + 1) % 20 == 0 or i == 0:
            print(f"  Embedding [{i+1}/{len(photos)}] {p['filename']}")

    del model, processor
    torch.cuda.empty_cache()

    X = torch.stack(embeddings).numpy()

    # Split: single-channel photos with known labels
    labeled_idx = [i for i, p in enumerate(photos) if p["channel"] in (0, 19, 21)]
    if len(labeled_idx) < 10:
        print("  Not enough labeled data for probe")
        return None

    # Labels: 0=control, 1=ch19, 2=ch21
    label_map = {0: 0, 19: 1, 21: 2}
    X_labeled = X[[i for i in labeled_idx]]
    y_labeled = [label_map[photos[i]["channel"]] for i in labeled_idx]

    # Leave-one-out cross-validation for fair evaluation
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_predict, LeaveOneOut, StratifiedKFold
    import numpy as np

    y = np.array(y_labeled)

    # Use 5-fold stratified CV (LOO is too slow for 67 samples with LR)
    clf = LogisticRegression(max_iter=1000, C=1.0)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    y_pred = cross_val_predict(clf, X_labeled, y, cv=cv)

    # Results by channel
    print(f"\n  5-Fold CV results (n={len(y)}):")
    acc = (y_pred == y).mean()
    print(f"  Overall accuracy: {acc:.1%}")

    for ch_val, ch_name in enumerate(["control", "ch19", "ch21"]):
        mask = y == ch_val
        ch_acc = (y_pred[mask] == y[mask]).mean()
        n = mask.sum()
        print(f"  {ch_name:10s}: {ch_acc:.1%} ({(y_pred[mask] == ch_val).sum()}/{n})")

    # Confusion: what gets predicted as what
    print(f"\n  Confusion (true → predicted):")
    for true_val, true_name in enumerate(["control", "ch19", "ch21"]):
        row = []
        for pred_val, pred_name in enumerate(["control", "ch19", "ch21"]):
            count = ((y == true_val) & (y_pred == pred_val)).sum()
            row.append(f"{pred_name}={count}")
        print(f"    {true_name:10s}: {', '.join(row)}")

    # Train final model on all data for predictions
    clf_final = LogisticRegression(max_iter=1000, C=1.0)
    clf_final.fit(X_labeled, y)

    # Predict probabilities for all photos
    probs = clf_final.predict_proba(X)
    results = []
    for i, p in enumerate(photos):
        pred = int(probs[i].argmax())
        pred_name = ["control", "ch19", "ch21"][pred]
        results.append({
            "filename": p["filename"],
            "channel": p["channel"],
            "predicted": pred_name,
            "prob_control": round(float(probs[i][0]), 4),
            "prob_ch19": round(float(probs[i][1]), 4),
            "prob_ch21": round(float(probs[i][2]), 4),
        })

    return results


def channel_analysis(results, model_name, score_key="coag_score"):
    """Print channel breakdown like the LLM report."""
    print(f"\n  Channel Analysis ({model_name}):")

    ch_scores = defaultdict(list)
    ch_labels = defaultdict(Counter)
    for r in results:
        ch = r.get("channel")
        if ch is None:
            continue
        ch_name = CH_NAMES.get(ch, f"ch{ch}")
        if score_key in r:
            ch_scores[ch_name].append(r[score_key])
        if "top_label" in r:
            ch_labels[ch_name][r["top_label"]] += 1

    if ch_labels:
        for ch_name in ("control", "ch19", "ch21"):
            labels = ch_labels.get(ch_name, Counter())
            total = sum(labels.values())
            if total == 0:
                continue
            print(f"\n    {ch_name} ({total} photos):")
            for label, count in labels.most_common(4):
                print(f"      {count:3d} ({count/total*100:5.1f}%)  {label}")

    if ch_scores:
        print(f"\n    Coagulation scores by channel:")
        for ch_name in ("control", "ch19", "ch21"):
            scores = ch_scores.get(ch_name, [])
            if scores:
                avg = sum(scores) / len(scores)
                print(f"    {ch_name:<10} n={len(scores):3d}  avg={avg:.4f}  min={min(scores):.4f}  max={max(scores):.4f}")


def main():
    photos = load_photos_with_channels()
    print(f"Loaded {len(photos)} photos")
    single = sum(1 for p in photos if p["channel"] is not None)
    print(f"Single-channel: {single} (ctrl={sum(1 for p in photos if p['channel']==0)}, ch19={sum(1 for p in photos if p['channel']==19)}, ch21={sum(1 for p in photos if p['channel']==21)})")

    # 1. SigLIP2-SO400M
    t0 = time.time()
    siglip_results = run_siglip2_so400m(photos)
    print(f"  Done in {time.time()-t0:.1f}s")
    channel_analysis(siglip_results, "SigLIP2-SO400M")

    # Save
    (OUTPUT_DIR / "siglip2_so400m.json").write_text(json.dumps(siglip_results, indent=2))

    # 2. DINOv2-large probe
    t0 = time.time()
    dino_results = run_dinov2_large_probe(photos)
    print(f"  Done in {time.time()-t0:.1f}s")

    if dino_results:
        (OUTPUT_DIR / "dinov2_large_probe.json").write_text(json.dumps(dino_results, indent=2))

        # Channel analysis for probe
        print(f"\n  DINOv2-large Probe — Predicted channel distribution:")
        ch_pred = defaultdict(Counter)
        for r in dino_results:
            ch = r.get("channel")
            if ch is None:
                continue
            ch_name = CH_NAMES.get(ch, f"ch{ch}")
            ch_pred[ch_name][r["predicted"]] += 1

        for ch_name in ("control", "ch19", "ch21"):
            preds = ch_pred.get(ch_name, Counter())
            total = sum(preds.values())
            if total == 0:
                continue
            parts = [f"{pred}={count}" for pred, count in preds.most_common()]
            print(f"    True {ch_name:10s} (n={total}): {', '.join(parts)}")

    print(f"\nResults saved to: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
