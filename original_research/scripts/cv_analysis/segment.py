#!/usr/bin/env python3
"""Standalone SAM-2 + CV segment analysis for blood plasma photos.

Produces JSON metrics + overlay image showing detected mask and clots.

Usage:
    python segment.py photo.jpg                          # default params
    python segment.py photo.jpg -p '{"min_clot_area_px": 1000}'
    python segment.py photo.jpg -o overlay.png           # custom overlay path
    python segment.py photo.jpg --json result.json       # custom JSON path
"""

import argparse
import io
import json
import logging
import os
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image
from skimage.feature import graycomatrix, graycoprops

logger = logging.getLogger(__name__)

# ── Configuration ──

SAM2_MODEL = "facebook/sam2.1-hiera-tiny"
SAM2_MAX_SIZE = int(os.getenv("SAM2_MAX_SIZE", "1024"))
ML_DEVICE = os.getenv("ML_DEVICE", "auto").lower()

_GLCM_LEVELS = 64
_COLOR_BANDS = 5


@dataclass
class SegmentParams:
    clot_dark_factor: float = 0.60
    clot_min_bright: int = 15
    clot_max_ratio: float = 0.015
    clot_max_plasma_ratio: float = 0.25
    clot_bright_floor: float = 0.45
    clot_min_saturation: int = 15
    clot_min_circularity: float = 0.05
    clot_min_solidity: float = 0.40
    clot_max_hue_dev: int = 25
    min_clot_area_px: int = 500
    sediment_bottom_frac: float = 0.70
    mask_shrink_margin: int = 20
    plasma_hsv_lower: tuple[int, int, int] = (12, 35, 60)
    plasma_hsv_upper: tuple[int, int, int] = (50, 255, 230)
    sam2_iou_thresh: float = 0.92
    sam2_stability_thresh: float = 0.97


# ── SAM-2 model (lazy singleton) ──

_sam2_pipeline = None
_sam2_available = None


def _resolve_device() -> str:
    if ML_DEVICE == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    return ML_DEVICE


def _load_sam2():
    global _sam2_pipeline, _sam2_available
    if _sam2_available is not None:
        return
    try:
        from transformers import pipeline as hf_pipeline

        device = _resolve_device()
        _sam2_pipeline = hf_pipeline(
            "mask-generation",
            model=SAM2_MODEL,
            device=device,
        )
        _sam2_available = True
        logger.info("SAM-2 loaded on %s", device)
    except Exception as e:
        _sam2_available = False
        logger.error("SAM-2 load failed: %s", e)


def _resize_for_sam2(image: Image.Image) -> Image.Image:
    w, h = image.size
    long_edge = max(w, h)
    if long_edge <= SAM2_MAX_SIZE:
        return image
    scale = SAM2_MAX_SIZE / long_edge
    return image.resize((int(w * scale), int(h * scale)), Image.LANCZOS)


def run_sam2_raw(
    image: Image.Image,
    pred_iou_thresh: float = 0.92,
    stability_score_thresh: float = 0.97,
) -> list[tuple[dict, np.ndarray]] | None:
    _load_sam2()
    if not _sam2_available:
        return None

    device = _resolve_device()
    ppb = 64 if device == "cuda" else 16
    image = _resize_for_sam2(image)

    try:
        with torch.inference_mode():
            outputs = _sam2_pipeline(
                image,
                points_per_batch=ppb,
                pred_iou_thresh=pred_iou_thresh,
                stability_score_thresh=stability_score_thresh,
            )
    finally:
        if device == "cuda":
            torch.cuda.empty_cache()

    raw_masks = outputs.get("masks", [])
    raw_scores = outputs.get("scores", [])
    if hasattr(raw_scores, "tolist"):
        raw_scores = raw_scores.tolist()

    results = []
    for i, mask in enumerate(raw_masks):
        mask_arr = np.array(mask, dtype=np.uint8) if not isinstance(mask, np.ndarray) else mask.astype(np.uint8)
        mask_arr = (mask_arr > 0).astype(np.uint8) * 255
        area = int((mask_arr > 0).sum())
        total = mask_arr.size
        score = raw_scores[i] if i < len(raw_scores) else 0.0
        info = {
            "mask_index": i,
            "area_pixels": area,
            "area_ratio": round(area / total, 4) if total > 0 else 0.0,
            "iou_score": round(float(score), 4),
        }
        results.append((info, mask_arr))

    results.sort(key=lambda x: x[0]["area_pixels"], reverse=True)
    return results


# ── Plasma mask selection ──

def _find_plasma_mask(
    img_bgr: np.ndarray,
    sam2_masks: list[tuple[dict, np.ndarray]],
    params: SegmentParams,
) -> tuple[np.ndarray | None, dict | None]:
    img_h, img_w = img_bgr.shape[:2]
    hsv_img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    best_mask, best_info, best_score = None, None, -1

    for info, mask_arr in sam2_masks:
        if mask_arr.shape[:2] != (img_h, img_w):
            mask_arr = cv2.resize(mask_arr, (img_w, img_h), interpolation=cv2.INTER_NEAREST)
        if int((mask_arr > 0).sum()) < 1000:
            continue

        hsv_roi = hsv_img[mask_arr > 0]
        h_mean = float(hsv_roi[:, 0].mean())
        s_mean = float(hsv_roi[:, 1].mean())
        v_mean = float(hsv_roi[:, 2].mean())

        if not (8 <= h_mean <= 65 and s_mean > 20 and 15 <= v_mean <= 240):
            continue

        area_ratio = info["area_ratio"]
        score = area_ratio * (s_mean / 255) * min(v_mean, 255 - v_mean) / 128
        if score > best_score:
            best_score = score
            best_mask = mask_arr
            best_info = info

    if best_mask is None:
        best_mask, best_info = _hsv_plasma_fallback(img_bgr, params)

    if best_mask is not None:
        best_mask = _refine_mask_hsv(img_bgr, best_mask, params)
        if best_mask is None or int((best_mask > 0).sum()) < 1000:
            return None, None
        if best_info is not None:
            area = int((best_mask > 0).sum())
            best_info["area_pixels"] = area
            best_info["area_ratio"] = round(area / (img_h * img_w), 4)

    return best_mask, best_info


def _hsv_plasma_fallback(
    img_bgr: np.ndarray, params: SegmentParams,
) -> tuple[np.ndarray | None, dict | None]:
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    img_h, img_w = img_bgr.shape[:2]
    lower = np.array(params.plasma_hsv_lower)
    upper = np.array(params.plasma_hsv_upper)
    mask = cv2.inRange(hsv, lower, upper)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

    area = int((mask > 0).sum())
    if area < 1000:
        return None, None

    info = {
        "mask_index": -1,
        "area_pixels": area,
        "area_ratio": round(area / (img_h * img_w), 4),
        "iou_score": 0.0,
        "backend": "hsv_fallback",
    }
    return mask, info


def _keep_largest_component(mask: np.ndarray) -> np.ndarray | None:
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if num_labels < 2:
        return mask
    areas = stats[1:, cv2.CC_STAT_AREA]
    largest_label = int(areas.argmax()) + 1
    result = np.zeros_like(mask)
    result[labels == largest_label] = 255
    return result


def _refine_mask_hsv(
    img_bgr: np.ndarray, mask: np.ndarray, params: SegmentParams,
) -> np.ndarray | None:
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    lower = np.array(params.plasma_hsv_lower)
    upper = np.array(params.plasma_hsv_upper)
    plasma_px = cv2.inRange(hsv, lower, upper)
    refined = cv2.bitwise_and(mask, plasma_px)

    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    refined = cv2.morphologyEx(refined, cv2.MORPH_CLOSE, kernel_close, iterations=2)
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    refined = cv2.morphologyEx(refined, cv2.MORPH_OPEN, kernel_open, iterations=2)

    refined = _keep_largest_component(refined)
    if refined is None or int((refined > 0).sum()) < 1000:
        return None
    return refined


# ── Mask operations ──

def _shrink_mask(mask: np.ndarray, margin_px: int) -> np.ndarray:
    dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
    interior = (dist >= margin_px).astype(np.uint8) * 255
    if int((interior > 0).sum()) < 2000:
        k = max(3, margin_px // 2)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
        return cv2.erode(mask, kernel, iterations=1)
    return interior


# ── Metrics ──

def _compute_plasma_metrics(img_bgr: np.ndarray, mask: np.ndarray) -> dict:
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    gray_roi = gray[mask > 0]
    hsv_img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    brightness_mean = float(gray_roi.mean())
    brightness_std = float(gray_roi.std())
    rgb = img_bgr[mask > 0][:, ::-1]
    rgb_mean = rgb.mean(axis=0).tolist()
    hsv_mean = hsv_img[mask > 0].mean(axis=0).tolist()

    hist, _ = np.histogram(gray_roi, bins=256, range=(0, 256))
    hist = hist[hist > 0]
    probs = hist / hist.sum()
    entropy = float(-np.sum(probs * np.log2(probs)))

    ys, xs = np.where(mask > 0)
    gray_crop = gray[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    mask_crop = mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1]

    glcm_contrast = glcm_homogeneity = glcm_energy = glcm_correlation = 0.0
    if gray_crop.shape[0] > 1 and gray_crop.shape[1] > 1:
        quantized = (gray_crop // (256 // _GLCM_LEVELS)).astype(np.uint8)
        quantized[mask_crop == 0] = 0
        try:
            glcm = graycomatrix(
                quantized, distances=[1],
                angles=[0, np.pi / 4, np.pi / 2, 3 * np.pi / 4],
                levels=_GLCM_LEVELS, symmetric=True, normed=True,
            )
            glcm_contrast = float(graycoprops(glcm, "contrast").mean())
            glcm_homogeneity = float(graycoprops(glcm, "homogeneity").mean())
            glcm_energy = float(graycoprops(glcm, "energy").mean())
            glcm_correlation = float(graycoprops(glcm, "correlation").mean())
        except Exception:
            pass

    edges = cv2.Canny(gray, 50, 150)
    roi_count = int((mask > 0).sum())
    edge_density = float(np.count_nonzero(edges[mask > 0]) / roi_count)

    return {
        "area_pixels": roi_count,
        "area_ratio": round(roi_count / mask.size, 4),
        "brightness_mean": round(brightness_mean, 2),
        "brightness_std": round(brightness_std, 2),
        "entropy": round(entropy, 4),
        "glcm_contrast": round(glcm_contrast, 4),
        "glcm_homogeneity": round(glcm_homogeneity, 4),
        "glcm_energy": round(glcm_energy, 4),
        "glcm_correlation": round(glcm_correlation, 4),
        "edge_density": round(edge_density, 4),
        "rgb_mean": [round(v, 1) for v in rgb_mean],
        "hsv_mean": [round(v, 1) for v in hsv_mean],
    }


# ── Clot detection ──

def _detect_clots(
    img_bgr: np.ndarray, plasma_mask: np.ndarray, params: SegmentParams,
) -> list[dict]:
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    mean_bright = float(gray[plasma_mask > 0].mean())

    threshold = mean_bright * params.clot_dark_factor
    dark_mask = np.zeros_like(plasma_mask)
    dark_mask[(gray < threshold) & (plasma_mask > 0)] = 255

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    dark_mask = cv2.morphologyEx(dark_mask, cv2.MORPH_OPEN, kernel, iterations=2)
    dark_mask = cv2.morphologyEx(dark_mask, cv2.MORPH_CLOSE, kernel, iterations=1)

    contours, _ = cv2.findContours(dark_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    clots = []
    img_h, img_w = img_bgr.shape[:2]
    total_px = img_h * img_w
    max_clot_px = total_px * params.clot_max_ratio
    plasma_px = int((plasma_mask > 0).sum())
    max_clot_plasma_px = plasma_px * params.clot_max_plasma_ratio
    hsv_img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    brightness_floor = mean_bright * params.clot_bright_floor
    plasma_h_values = hsv_img[plasma_mask > 0][:, 0]
    plasma_h_median = float(np.median(plasma_h_values))

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < params.min_clot_area_px or area > max_clot_px:
            continue
        if area > max_clot_plasma_px:
            continue

        perimeter = cv2.arcLength(cnt, True)
        if perimeter > 0:
            circularity = 4 * np.pi * area / (perimeter ** 2)
            if circularity < params.clot_min_circularity:
                continue

        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        if hull_area > 0:
            solidity = area / hull_area
            if solidity < params.clot_min_solidity:
                continue

        cnt_mask = np.zeros((img_h, img_w), dtype=np.uint8)
        cv2.drawContours(cnt_mask, [cnt], -1, 255, -1)

        clot_gray = gray[cnt_mask > 0]
        clot_brightness = float(clot_gray.mean())
        if clot_brightness < params.clot_min_bright:
            continue
        if clot_brightness < brightness_floor:
            continue

        clot_rgb = img_bgr[cnt_mask > 0][:, ::-1]
        clot_hsv = hsv_img[cnt_mask > 0]

        clot_s_mean = float(clot_hsv[:, 1].mean())
        if clot_s_mean < params.clot_min_saturation:
            continue

        clot_h_mean = float(clot_hsv[:, 0].mean())
        if abs(clot_h_mean - plasma_h_median) > params.clot_max_hue_dev:
            continue

        M = cv2.moments(cnt)
        cx = M["m10"] / M["m00"] / img_w if M["m00"] > 0 else 0.5
        cy = M["m01"] / M["m00"] / img_h if M["m00"] > 0 else 0.5
        x, y, w, h = cv2.boundingRect(cnt)

        clots.append({
            "index": len(clots),
            "area_pixels": int(area),
            "area_ratio": round(area / total_px, 6),
            "brightness_mean": round(float(clot_gray.mean()), 1),
            "rgb_mean": [round(float(v), 1) for v in clot_rgb.mean(axis=0)],
            "hsv_mean": [round(float(v), 1) for v in clot_hsv.mean(axis=0)],
            "centroid": {"x": round(cx, 3), "y": round(cy, 3)},
            "bbox": {"x": int(x), "y": int(y), "w": int(w), "h": int(h)},
        })

    clots.sort(key=lambda c: c["area_pixels"], reverse=True)
    return clots


# ── Sediment & gradient ──

def _detect_sediment(
    img_bgr: np.ndarray, plasma_mask: np.ndarray, params: SegmentParams,
) -> dict | None:
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    ys, xs = np.where(plasma_mask > 0)
    if len(ys) == 0:
        return None

    y_min, y_max = int(ys.min()), int(ys.max())
    plasma_height = y_max - y_min
    if plasma_height < 10:
        return None

    bottom_cutoff = y_min + int(plasma_height * params.sediment_bottom_frac)
    bottom_mask = np.zeros_like(plasma_mask)
    bottom_mask[bottom_cutoff:, :] = plasma_mask[bottom_cutoff:, :]
    top_mask = np.zeros_like(plasma_mask)
    top_mask[:bottom_cutoff, :] = plasma_mask[:bottom_cutoff, :]

    bottom_count = int((bottom_mask > 0).sum())
    top_count = int((top_mask > 0).sum())
    if bottom_count < 100 or top_count < 100:
        return None

    bottom_bright = float(gray[bottom_mask > 0].mean())
    top_bright = float(gray[top_mask > 0].mean())
    brightness_diff = top_bright - bottom_bright
    if brightness_diff < 3:
        return None

    hsv_img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    bottom_rgb = img_bgr[bottom_mask > 0][:, ::-1].mean(axis=0).tolist()
    bottom_hsv = hsv_img[bottom_mask > 0].mean(axis=0).tolist()

    img_h, img_w = img_bgr.shape[:2]
    return {
        "area_pixels": bottom_count,
        "area_ratio": round(bottom_count / (img_h * img_w), 4),
        "brightness_mean": round(bottom_bright, 1),
        "brightness_diff_from_top": round(brightness_diff, 1),
        "rgb_mean": [round(v, 1) for v in bottom_rgb],
        "hsv_mean": [round(v, 1) for v in bottom_hsv],
        "zone_start_y": round(bottom_cutoff / img_h, 3),
    }


def _color_gradient(img_bgr: np.ndarray, plasma_mask: np.ndarray) -> list[dict]:
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    hsv_img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    ys = np.where(plasma_mask > 0)[0]
    if len(ys) == 0:
        return []

    y_min, y_max = int(ys.min()), int(ys.max())
    plasma_height = y_max - y_min
    if plasma_height < _COLOR_BANDS * 2:
        return []

    band_height = plasma_height // _COLOR_BANDS
    bands = []
    for i in range(_COLOR_BANDS):
        band_y_start = y_min + i * band_height
        band_y_end = band_y_start + band_height if i < _COLOR_BANDS - 1 else y_max

        band_mask = np.zeros_like(plasma_mask)
        band_mask[band_y_start:band_y_end, :] = plasma_mask[band_y_start:band_y_end, :]
        count = int((band_mask > 0).sum())
        if count < 10:
            continue

        band_gray = gray[band_mask > 0]
        band_rgb = img_bgr[band_mask > 0][:, ::-1]
        band_hsv = hsv_img[band_mask > 0]
        bands.append({
            "band": i,
            "position": round((i + 0.5) / _COLOR_BANDS, 2),
            "brightness": round(float(band_gray.mean()), 1),
            "rgb_mean": [round(float(v), 1) for v in band_rgb.mean(axis=0)],
            "hsv_mean": [round(float(v), 1) for v in band_hsv.mean(axis=0)],
        })
    return bands


# ── Overlay generation ──

def draw_overlay(
    img_bgr: np.ndarray,
    plasma_mask: np.ndarray,
    clots: list[dict],
    sediment: dict | None = None,
) -> np.ndarray:
    """Draw analysis overlay on image: plasma mask (green), clot bboxes (red), sediment zone (blue)."""
    overlay = img_bgr.copy()

    # Plasma mask — semi-transparent green
    green = np.zeros_like(overlay)
    green[:, :, 1] = 255
    mask_bool = plasma_mask > 0
    overlay[mask_bool] = cv2.addWeighted(overlay, 0.7, green, 0.3, 0)[mask_bool]

    # Plasma mask contour — bright green
    contours, _ = cv2.findContours(plasma_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(overlay, contours, -1, (0, 255, 0), 2)

    # Clots — red bbox + index label
    for clot in clots:
        bb = clot["bbox"]
        x, y, w, h = bb["x"], bb["y"], bb["w"], bb["h"]
        cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 0, 255), 2)
        label = f"#{clot['index']} ({clot['area_pixels']}px)"
        cv2.putText(overlay, label, (x, y - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

    # Sediment zone — blue line
    if sediment and "zone_start_y" in sediment:
        img_h = overlay.shape[0]
        zone_y = int(sediment["zone_start_y"] * img_h)
        cv2.line(overlay, (0, zone_y), (overlay.shape[1], zone_y), (255, 100, 0), 2)
        cv2.putText(overlay, "sediment zone", (10, zone_y - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 100, 0), 1)

    # Legend
    h = overlay.shape[0]
    cv2.putText(overlay, f"clots: {len(clots)}", (10, h - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    return overlay


# ── Main pipeline ──

def analyze(
    image_path: str,
    params: SegmentParams | None = None,
    overlay_path: str | None = None,
) -> dict | None:
    """Run full segment analysis on an image file.

    Returns metrics dict and saves overlay image if overlay_path is given.
    """
    if params is None:
        params = SegmentParams()

    img_pil = Image.open(image_path).convert("RGB")
    raw_results = run_sam2_raw(
        img_pil,
        pred_iou_thresh=params.sam2_iou_thresh,
        stability_score_thresh=params.sam2_stability_thresh,
    )
    if raw_results is None:
        logger.error("SAM-2 unavailable")
        return None

    img_bgr = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    img_h, img_w = img_bgr.shape[:2]

    plasma_mask, plasma_info = _find_plasma_mask(img_bgr, raw_results, params)
    if plasma_mask is None:
        return {"error": "no_plasma_mask", "image_size": {"width": img_w, "height": img_h}}

    if plasma_mask.shape[:2] != (img_h, img_w):
        plasma_mask = cv2.resize(plasma_mask, (img_w, img_h), interpolation=cv2.INTER_NEAREST)

    plasma_metrics = _compute_plasma_metrics(img_bgr, plasma_mask)
    plasma_mask_interior = _shrink_mask(plasma_mask, params.mask_shrink_margin)
    clots = _detect_clots(img_bgr, plasma_mask_interior, params)
    sediment = _detect_sediment(img_bgr, plasma_mask, params)
    gradient = _color_gradient(img_bgr, plasma_mask)

    clot_summary = None
    if clots:
        areas = [c["area_pixels"] for c in clots]
        clot_summary = {
            "count": len(clots),
            "total_area_pixels": sum(areas),
            "total_area_ratio": round(sum(c["area_ratio"] for c in clots), 6),
            "avg_area_pixels": round(float(np.mean(areas)), 0),
            "max_area_pixels": max(areas),
            "avg_brightness": round(float(np.mean([c["brightness_mean"] for c in clots])), 1),
        }

    # Generate and save overlay
    if overlay_path:
        overlay_img = draw_overlay(img_bgr, plasma_mask, clots, sediment)
        Path(overlay_path).parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(overlay_path, overlay_img)
        logger.info("Overlay saved: %s", overlay_path)

    return {
        "plasma": plasma_metrics,
        "clots": clots,
        "clot_summary": clot_summary,
        "sediment": sediment,
        "color_gradient": gradient,
        "image_size": {"width": img_w, "height": img_h},
    }


# ── CLI ──

def main():
    parser = argparse.ArgumentParser(description="SAM-2 + CV segment analysis for blood plasma")
    parser.add_argument("image", help="Path to JPEG photo")
    parser.add_argument("-p", "--params", default="{}", help="JSON string with custom params")
    parser.add_argument("-o", "--overlay", default=None, help="Output overlay image path")
    parser.add_argument("--json", dest="json_out", default=None, help="Output JSON path")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"ERROR: File not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    # Parse custom params
    params = SegmentParams()
    custom = json.loads(args.params)
    for k, v in custom.items():
        if hasattr(params, k):
            setattr(params, k, v)

    # Default overlay path: overlays/FILENAME_overlay.png
    overlay_path = args.overlay
    if overlay_path is None:
        overlay_dir = Path(__file__).parent / "overlays"
        overlay_path = str(overlay_dir / f"{image_path.stem}_overlay.png")

    result = analyze(str(image_path), params, overlay_path)

    if result is None:
        print("ERROR: Analysis failed (SAM-2 unavailable)", file=sys.stderr)
        sys.exit(1)

    # Output JSON
    json_str = json.dumps(result, indent=2, ensure_ascii=False)
    if args.json_out:
        Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_out).write_text(json_str)
        print(f"JSON saved: {args.json_out}")
    else:
        print(json_str)

    clot_count = result.get("clot_summary", {}).get("count", 0) if result.get("clot_summary") else 0
    print(f"\nOverlay saved: {overlay_path}", file=sys.stderr)
    print(f"Clots detected: {clot_count}", file=sys.stderr)


if __name__ == "__main__":
    main()
