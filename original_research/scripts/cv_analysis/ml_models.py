"""ML vision models for blood plasma image analysis.

- DINOv2-small: self-supervised 384d embeddings
- SigLIP2-base: zero-shot plasma classification
- SAM-2: automatic segmentation (Replicate cloud → local fallback)

Device controlled by ML_DEVICE env var: "cuda", "cpu", or "auto" (default).
"auto" uses CUDA if available, else CPU.
"""

import asyncio
import io
import logging
import os

import torch
from PIL import Image

logger = logging.getLogger(__name__)

# ── Device selection ──

_ML_DEVICE_ENV = os.getenv("ML_DEVICE", "auto").lower()
_SAM2_DEVICE_ENV = os.getenv("SAM2_DEVICE", "").lower()  # override for SAM-2
_SAM2_MAX_SIZE = int(os.getenv("SAM2_MAX_SIZE", "1024"))  # resize long edge


def _resolve_device(env_val: str = "") -> str:
    val = env_val or _ML_DEVICE_ENV
    if val == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    return val


_device = _resolve_device()
_sam2_device = _resolve_device(_SAM2_DEVICE_ENV) if _SAM2_DEVICE_ENV else _device
logger.info("ML device: %s | SAM-2 device: %s", _device, _sam2_device)

# SAM-2 points_per_batch: higher on GPU for speed
_SAM2_POINTS_PER_BATCH = 64 if _sam2_device == "cuda" else 16


# ── DINOv2 (lazy-loaded singleton) ──

_dino_model = None
_dino_processor = None
_dino_available: bool | None = None


def _load_dinov2():
    """Load DINOv2-small model and processor (22M params, 384d output)."""
    global _dino_model, _dino_processor, _dino_available
    if _dino_available is not None:
        return
    try:
        from transformers import AutoImageProcessor, AutoModel

        _dtype = torch.bfloat16 if _device == "cuda" else None
        _dino_processor = AutoImageProcessor.from_pretrained("facebook/dinov2-small")
        _dino_model = AutoModel.from_pretrained(
            "facebook/dinov2-small", dtype=_dtype,
        ).to(_device)
        _dino_model.eval()
        _dino_available = True
        logger.info("DINOv2-small loaded on %s (384d embeddings)", _device)
    except Exception as e:
        _dino_available = False
        logger.warning("DINOv2-small unavailable: %s", type(e).__name__)


def run_dinov2(image: Image.Image) -> dict | None:
    """Extract 384d CLS embedding from image using DINOv2-small.

    Returns {"embedding": [...], "dim": 384} or None if unavailable.
    """
    _load_dinov2()
    if not _dino_available:
        return None

    inputs = _dino_processor(images=image, return_tensors="pt")
    inputs = {k: v.to(_device) for k, v in inputs.items()}
    with torch.inference_mode():
        outputs = _dino_model(**inputs)
    cls = outputs.last_hidden_state[:, 0, :].squeeze().cpu().tolist()
    return {"embedding": cls, "dim": len(cls)}


# ── SigLIP2 (lazy-loaded singleton) ──

_siglip_model = None
_siglip_processor = None
_siglip_available: bool | None = None

PLASMA_LABELS = [
    # Visual state labels
    "clear transparent blood plasma",
    "turbid cloudy blood plasma",
    "blood plasma with fibrin clots",
    "blood plasma with sediment",
    "hemolyzed blood plasma",
    "normal blood plasma sample",
    # Coagulation stage labels
    "blood plasma with no fibrin formation",
    "blood plasma with early fibrin strand formation",
    "blood plasma with partially formed fibrin clot",
    "blood plasma with dense mature fibrin clot",
    "blood plasma showing fibrinolysis with dissolving clot",
]

COAGULATION_LABEL_MAP = {
    "blood plasma with no fibrin formation": "none",
    "blood plasma with early fibrin strand formation": "early_fibrin",
    "blood plasma with partially formed fibrin clot": "partial_clot",
    "blood plasma with dense mature fibrin clot": "full_coagulation",
    "blood plasma showing fibrinolysis with dissolving clot": "lysis",
}


def _load_siglip2():
    """Load SigLIP2-base model and processor (86M params)."""
    global _siglip_model, _siglip_processor, _siglip_available
    if _siglip_available is not None:
        return
    try:
        from transformers import AutoModel, AutoProcessor

        _dtype = torch.bfloat16 if _device == "cuda" else None
        _siglip_processor = AutoProcessor.from_pretrained("google/siglip2-base-patch16-224")
        _siglip_model = AutoModel.from_pretrained(
            "google/siglip2-base-patch16-224", dtype=_dtype,
        ).to(_device)
        _siglip_model.eval()
        _siglip_available = True
        logger.info("SigLIP2-base loaded on %s (zero-shot classification)", _device)
    except Exception as e:
        _siglip_available = False
        logger.warning("SigLIP2-base unavailable: %s", type(e).__name__)


def run_siglip2(image: Image.Image, labels: list[str] | None = None) -> dict | None:
    """Zero-shot classification: scores for each label via sigmoid.

    Returns {"labels": [{"label": ..., "score": ...}], "top_label": ..., "top_score": ...}
    or None if unavailable.
    """
    _load_siglip2()
    if not _siglip_available:
        return None

    use_labels = labels or PLASMA_LABELS
    texts = [f"A photo of {label}" for label in use_labels]
    inputs = _siglip_processor(
        text=texts,
        images=image,
        padding="max_length",
        max_length=64,
        return_tensors="pt",
    )
    inputs = {k: v.to(_device) for k, v in inputs.items()}
    with torch.inference_mode():
        outputs = _siglip_model(**inputs)
    scores = outputs.logits_per_image.softmax(dim=-1).squeeze().cpu().tolist()
    if isinstance(scores, float):
        scores = [scores]
    labeled = sorted(zip(use_labels, scores), key=lambda x: -x[1])
    return {
        "labels": [{"label": label, "score": round(score, 4)} for label, score in labeled],
        "top_label": labeled[0][0],
        "top_score": round(labeled[0][1], 4),
    }


# ── MedSigLIP (lazy-loaded singleton) ──

_medsiglip_model = None
_medsiglip_processor = None
_medsiglip_available: bool | None = None


def _load_medsiglip():
    """Load MedSigLIP-448 (Google, 800M params — 400M vision + 400M text)."""
    global _medsiglip_model, _medsiglip_processor, _medsiglip_available
    if _medsiglip_available is not None:
        return
    try:
        from transformers import AutoModel, AutoProcessor

        _hf_token = os.getenv("HF_TOKEN")
        _medsiglip_processor = AutoProcessor.from_pretrained(
            "google/medsiglip-448", token=_hf_token,
        )
        _medsiglip_model = AutoModel.from_pretrained(
            "google/medsiglip-448", token=_hf_token,
        ).to(_device)
        _medsiglip_model.eval()
        _medsiglip_available = True
        logger.info("MedSigLIP-448 loaded on %s (medical zero-shot)", _device)
    except Exception as e:
        _medsiglip_available = False
        logger.warning("MedSigLIP-448 unavailable: %s", type(e).__name__)


def run_medsiglip(image: Image.Image, labels: list[str] | None = None) -> dict | None:
    """Zero-shot medical classification via MedSigLIP-448 (softmax).

    Returns {"labels": [{"label": ..., "score": ...}], "top_label": ..., "top_score": ...}
    or None if unavailable.
    """
    _load_medsiglip()
    if not _medsiglip_available:
        return None

    use_labels = labels or PLASMA_LABELS
    texts = [f"A photo of {label}" for label in use_labels]
    inputs = _medsiglip_processor(
        text=texts,
        images=image,
        padding="max_length",
        max_length=64,
        return_tensors="pt",
    )
    inputs = {k: v.to(_device) for k, v in inputs.items()}
    with torch.inference_mode():
        outputs = _medsiglip_model(**inputs)
    scores = outputs.logits_per_image.softmax(dim=-1).squeeze().cpu().tolist()
    if isinstance(scores, float):
        scores = [scores]
    labeled = sorted(zip(use_labels, scores), key=lambda x: -x[1])
    return {
        "labels": [{"label": label, "score": round(score, 4)} for label, score in labeled],
        "top_label": labeled[0][0],
        "top_score": round(labeled[0][1], 4),
    }


# ── BiomedCLIP (lazy-loaded singleton) ──

_biomedclip_model = None
_biomedclip_preprocess = None
_biomedclip_tokenizer = None
_biomedclip_available: bool | None = None
_BIOMEDCLIP_CONTEXT_LENGTH = 256
_BIOMEDCLIP_TEMPLATE = "this is a photo of "


def _load_biomedclip():
    """Load BiomedCLIP (Microsoft, ViT-B/16 + PubMedBERT, ~784MB)."""
    global _biomedclip_model, _biomedclip_preprocess, _biomedclip_tokenizer, _biomedclip_available
    if _biomedclip_available is not None:
        return
    try:
        from open_clip import create_model_from_pretrained, get_tokenizer

        _biomedclip_model, _biomedclip_preprocess = create_model_from_pretrained(
            "hf-hub:microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224"
        )
        _biomedclip_tokenizer = get_tokenizer(
            "hf-hub:microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224"
        )
        _biomedclip_model.to(_device)
        _biomedclip_model.eval()
        _biomedclip_available = True
        logger.info("BiomedCLIP loaded on %s (zero-shot biomedical classification)", _device)
    except Exception as e:
        _biomedclip_available = False
        logger.warning("BiomedCLIP unavailable: %s", type(e).__name__)


def run_biomedclip(image: Image.Image, labels: list[str] | None = None) -> dict | None:
    """Zero-shot biomedical classification via BiomedCLIP (softmax).

    Returns {"labels": [{"label": ..., "score": ...}], "top_label": ..., "top_score": ...}
    or None if unavailable.
    """
    _load_biomedclip()
    if not _biomedclip_available:
        return None

    use_labels = labels or PLASMA_LABELS
    texts = _biomedclip_tokenizer(
        [_BIOMEDCLIP_TEMPLATE + label for label in use_labels],
        context_length=_BIOMEDCLIP_CONTEXT_LENGTH,
    ).to(_device)
    image_tensor = _biomedclip_preprocess(image).unsqueeze(0).to(_device)

    with torch.inference_mode():
        image_features, text_features, logit_scale = _biomedclip_model(image_tensor, texts)
        scores = (logit_scale * image_features @ text_features.t()).softmax(dim=-1)

    probs = scores[0].cpu().float().tolist()
    labeled = sorted(zip(use_labels, probs), key=lambda x: -x[1])
    return {
        "labels": [{"label": label, "score": round(score, 4)} for label, score in labeled],
        "top_label": labeled[0][0],
        "top_score": round(labeled[0][1], 4),
    }


# ── SAM-2 (local or Replicate cloud) ──

_sam2_pipeline = None
_sam2_available: bool | None = None


def _load_sam2_local():
    """Load SAM-2.1-hiera-tiny via transformers pipeline (39M params, ~156MB)."""
    global _sam2_pipeline, _sam2_available
    if _sam2_available is not None:
        return
    try:
        from transformers import pipeline as hf_pipeline

        # SAM-2 must stay float32: torchvision NMS doesn't support half-precision
        _sam2_pipeline = hf_pipeline(
            "mask-generation",
            model="facebook/sam2.1-hiera-tiny",
            device=_sam2_device,
        )
        _sam2_available = True
        logger.info("SAM-2.1-hiera-tiny loaded on %s (float32)", _sam2_device)
    except Exception as e:
        _sam2_available = False
        logger.warning("SAM-2 local unavailable: %s", type(e).__name__)


def _resize_for_sam2(image: Image.Image) -> Image.Image:
    """Resize image if larger than SAM2_MAX_SIZE (default 1024)."""
    w, h = image.size
    long_edge = max(w, h)
    if long_edge <= _SAM2_MAX_SIZE:
        return image
    scale = _SAM2_MAX_SIZE / long_edge
    new_w, new_h = int(w * scale), int(h * scale)
    return image.resize((new_w, new_h), Image.LANCZOS)


def _run_sam2_local(image: Image.Image) -> dict | None:
    """Run SAM-2 locally via transformers pipeline."""
    _load_sam2_local()
    if not _sam2_available:
        return None

    image = _resize_for_sam2(image)
    try:
        with torch.inference_mode():
            outputs = _sam2_pipeline(
                image,
                points_per_batch=_SAM2_POINTS_PER_BATCH,
                pred_iou_thresh=0.92,
                stability_score_thresh=0.97,
            )
    finally:
        if _sam2_device == "cuda":
            torch.cuda.empty_cache()

    masks_data = []
    raw_masks = outputs.get("masks", [])
    raw_scores = outputs.get("scores", [])
    if hasattr(raw_scores, "tolist"):
        raw_scores = raw_scores.tolist()

    for i, mask in enumerate(raw_masks):
        import numpy as np

        mask_arr = np.array(mask) if not isinstance(mask, np.ndarray) else mask
        area = int(mask_arr.sum())
        total = mask_arr.size
        score = raw_scores[i] if i < len(raw_scores) else 0.0
        masks_data.append({
            "mask_index": i,
            "area_pixels": area,
            "area_ratio": round(area / total, 4) if total > 0 else 0.0,
            "iou_score": round(float(score), 4),
        })

    masks_data.sort(key=lambda m: m["area_pixels"], reverse=True)
    return {"masks": masks_data, "n_masks": len(masks_data), "backend": "local"}


def _run_sam2_replicate(image_bytes: bytes) -> dict | None:
    """Run SAM-2 via Replicate cloud API."""
    token = os.getenv("REPLICATE_API_TOKEN")
    if not token:
        return None
    try:
        import replicate

        output = replicate.run(
            "meta/sam-2",
            input={
                "image": io.BytesIO(image_bytes),
                "multimask_output": True,
            },
        )
        masks = []
        if isinstance(output, dict):
            individual = output.get("individual_masks", [])
            for i, mask_url in enumerate(individual):
                masks.append({"mask_index": i, "mask_url": str(mask_url)})
        elif isinstance(output, list):
            for i, item in enumerate(output):
                masks.append({"mask_index": i, "mask_url": str(item)})
        return {"masks": masks, "n_masks": len(masks), "backend": "replicate"}
    except Exception as e:
        logger.warning("SAM-2 Replicate call failed: %s", type(e).__name__)
        return None


def run_sam2_raw(
    image: Image.Image,
    pred_iou_thresh: float = 0.92,
    stability_score_thresh: float = 0.97,
) -> list[tuple[dict, "np.ndarray"]] | None:
    """Run SAM-2 locally and return masks with raw numpy arrays.

    Returns list of (mask_info_dict, mask_ndarray) or None if unavailable.
    Used by segment_analysis for per-mask CV metrics.
    """
    _load_sam2_local()
    if not _sam2_available:
        return None

    import numpy as np

    image = _resize_for_sam2(image)
    try:
        with torch.inference_mode():
            outputs = _sam2_pipeline(
                image,
                points_per_batch=_SAM2_POINTS_PER_BATCH,
                pred_iou_thresh=pred_iou_thresh,
                stability_score_thresh=stability_score_thresh,
            )
    finally:
        if _sam2_device == "cuda":
            torch.cuda.empty_cache()

    raw_masks = outputs.get("masks", [])
    raw_scores = outputs.get("scores", [])
    if hasattr(raw_scores, "tolist"):
        raw_scores = raw_scores.tolist()

    results = []
    for i, mask in enumerate(raw_masks):
        mask_arr = np.array(mask, dtype=np.uint8) if not isinstance(mask, np.ndarray) else mask.astype(np.uint8)
        # Ensure binary: 0 or 255
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


def run_sam2(image_bytes: bytes, image: Image.Image | None = None) -> dict | None:
    """Run SAM-2 segmentation. Tries Replicate first, falls back to local.

    Returns {"masks": [...], "n_masks": int, "backend": "replicate"|"local"}
    or None if both are unavailable.
    """
    result = _run_sam2_replicate(image_bytes)
    if result is not None:
        return result
    if image is None:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return _run_sam2_local(image)


# ── Public API ──


async def run_all_ml_models(image_bytes: bytes) -> dict:
    """Run all available ML models on image bytes.

    DINOv2 + SigLIP2 + BiomedCLIP + SAM-2 run in thread pool.
    SAM-2 tries Replicate first, falls back to local.

    Returns dict with per-model results.
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    result: dict = {
        "sam2": None,
        "dinov2": None,
        "siglip2": None,
        "medsiglip": None,
        "biomedclip": None,
        "models_succeeded": 0,
        "models_failed": 0,
        "errors": {},
    }

    async def _run_model(name: str, fn, *args):
        try:
            r = await asyncio.to_thread(fn, *args)
            result[name] = r
            if r is not None:
                result["models_succeeded"] += 1
            else:
                result["models_failed"] += 1
                result["errors"][name] = "unavailable"
        except Exception as e:
            result["models_failed"] += 1
            result["errors"][name] = type(e).__name__

    await asyncio.gather(
        _run_model("dinov2", run_dinov2, img),
        _run_model("siglip2", run_siglip2, img),
        _run_model("medsiglip", run_medsiglip, img),
        _run_model("biomedclip", run_biomedclip, img),
        _run_model("sam2", run_sam2, image_bytes, img),
    )
    return result
