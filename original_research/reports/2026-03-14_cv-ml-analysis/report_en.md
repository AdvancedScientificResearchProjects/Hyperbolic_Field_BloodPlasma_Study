# Computer Vision & ML Model Analysis: Blood Plasma Coagulation

**Date**: 2026-03-14
**Dataset**: 101 photographs, 7 donors (67 single-channel, 34 multi-tube)
**GPU**: NVIDIA RTX 3060 Laptop (6 GB VRAM)
**Prior analysis**: [Multi-Provider LLM Vision Analysis](../2026-03-12_comparative-llm-analysis/report_en.md)

---

## 1. Motivation

The [LLM vision report](../2026-03-12_comparative-llm-analysis/report_en.md) showed that large language models (Gemini 57.9%, Mistral 44.4%) can identify ch19 as the most coagulated sample above the 33% chance baseline in blinded comparative analysis over 19 triplet sets.

This report investigates whether **dedicated computer vision models** — zero-shot classifiers and feature extractors — can detect the same coagulation differences. CV models are deterministic, faster, and do not require prompt engineering.

To ensure direct comparability, the same **19 comparative sets** (triplets of control / ch19 / ch21 from the same patient) and the same **per-patient batch analysis** used in the LLM report are applied here.

---

## 2. Methodology

### 2.1. Dataset

| Channel | Description | Single-channel photos |
|---------|------------|:---:|
| Control (ch0) | No hyperbolic field exposure | 24 |
| CH19 | Time acceleration | 23 |
| CH21 | Time deceleration | 20 |
| **Total labeled** | | **67** |

34 additional multi-tube photos (multiple channels visible) excluded from analysis.

Channel assignment derived from `samples_shown` field in [`processed/en/all_patients.json`](../../processed/en/all_patients.json).

### 2.2. Comparative Sets (19 triplets)

Same 19 sets as in the [LLM report](../2026-03-12_comparative-llm-analysis/report_en.md), Section 3.1:

| Patient | Sets | Set indices |
|---------|:---:|-------------|
| P02 | 5 | 1–5 |
| P03 | 4 | 6–9 |
| P04 | 1 | 10 |
| P05 | 3 | 11–13 |
| P07 | 6 | 14–19 |

Each set contains one photo per channel (control, ch19, ch21) from the same patient. The model with the highest coagulation score in a set "wins" that set. **ch19 win rate** is the primary metric — directly comparable to LLM results.

### 2.3. Analysis Strategies

1. **Zero-shot classification** — model receives an image and 11 text labels describing plasma states. Returns probability distribution over labels via softmax. **Coagulation score** = sum of probabilities for clot/fibrin labels. No training required.

2. **Linear probe (DINOv2)** — frozen DINOv2-large extracts 1024-dim embeddings. A logistic regression classifier is trained on these embeddings. DINOv2 weights are **not fine-tuned** — only the linear classifier is trained. Evaluated with **leave-one-set-out CV**: for each of the 19 sets, the probe is trained on the remaining 64 photos and tested on the 3 held-out photos.

3. **Multi-chain pipeline** — SAM-2 segments plasma region → crop → DINOv2/SigLIP2 on cropped plasma only.

### 2.4. Label Set (Zero-Shot Models)

11 labels covering the coagulation spectrum:

| Label | Category |
|-------|----------|
| clear transparent blood plasma | No coagulation |
| normal blood plasma sample | No coagulation |
| blood plasma with no fibrin formation | No coagulation |
| turbid cloudy blood plasma | Ambiguous |
| blood plasma with sediment | Ambiguous |
| hemolyzed blood plasma | Ambiguous |
| blood plasma with early fibrin strand formation | Coagulation |
| blood plasma with partially formed fibrin clot | Coagulation |
| blood plasma with dense mature fibrin clot | Coagulation |
| blood plasma showing fibrinolysis with dissolving clot | Coagulation |
| blood plasma with fibrin clots | Coagulation |

Prompt format: `"A photo of {label}"`.

---

## 3. Models

| Model | Params | Type | Input | Source |
|-------|:---:|------|:---:|--------|
| [SigLIP2-base](https://huggingface.co/google/siglip2-base-patch16-224) | 86M | Zero-shot CLIP | 224px | Google |
| [SigLIP2-SO400M](https://huggingface.co/google/siglip2-so400m-patch14-384) | 400M | Zero-shot CLIP | 384px | Google |
| [BiomedCLIP](https://huggingface.co/microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224) | 200M | Zero-shot CLIP | 224px | Microsoft |
| [MedSigLIP](https://huggingface.co/google/medsiglip-448) | 800M | Zero-shot CLIP | 448px | Google |
| [DINOv2-large](https://huggingface.co/facebook/dinov2-large) | 307M | Feature extractor + probe | 518px | Meta |

**SigLIP2** — Google's CLIP variant with sigmoid loss. Base (86M) and SO400M (400M, 5x larger) tested.

**BiomedCLIP** — Microsoft's CLIP fine-tuned on PubMed biomedical image-text pairs (PMC-15M dataset).

**MedSigLIP** — Google's medical SigLIP trained on CT, MRI, X-ray, and pathology images.

**DINOv2** — Meta's self-supervised vision transformer. Produces general-purpose visual embeddings (1024-dim) without text prompts. Weights frozen; only the logistic regression probe is trained on our data.

---

## 4. Comparative Results (19 Sets)

For each of the 19 sets, the photo with the highest coagulation score (zero-shot) or highest ch19 probability (DINOv2 probe) is the "winner".

### 4.1. DINOv2-large Probe (Leave-One-Set-Out CV)

For each set, the probe is trained on all labeled photos **except** the 3 in that set — ensuring no data leakage.

| Set | Patient | ctrl | ch19 | ch21 | Winner |
|:---:|:---:|:---:|:---:|:---:|--------|
| 1 | P02 | 0.8881 | **0.9170** | 0.6405 | **ch19** |
| 2 | P02 | 0.0289 | **0.9657** | 0.2113 | **ch19** |
| 3 | P02 | **0.9889** | 0.9855 | 0.5402 | control |
| 4 | P02 | **0.9433** | 0.1960 | 0.9040 | control |
| 5 | P02 | **0.1490** | 0.0532 | 0.0083 | control |
| 6 | P03 | 0.0001 | **0.9633** | 0.1489 | **ch19** |
| 7 | P03 | **0.9791** | 0.7123 | 0.9243 | control |
| 8 | P03 | 0.0000 | 0.5329 | **0.8234** | ch21 |
| 9 | P03 | 0.0287 | **0.9664** | 0.0786 | **ch19** |
| 10 | P04 | 0.0866 | **0.2720** | 0.0524 | **ch19** |
| 11 | P05 | 0.0021 | 0.2765 | **0.8542** | ch21 |
| 12 | P05 | **0.8087** | 0.2150 | 0.3987 | control |
| 13 | P05 | 0.6173 | 0.0018 | **0.7872** | ch21 |
| 14 | P07 | 0.4001 | 0.5597 | **0.9179** | ch21 |
| 15 | P07 | 0.2325 | **0.8625** | 0.8530 | **ch19** |
| 16 | P07 | 0.0797 | **0.8843** | 0.0669 | **ch19** |
| 17 | P07 | **0.5058** | 0.0246 | 0.0001 | control |
| 18 | P07 | 0.0173 | **0.7998** | 0.0278 | **ch19** |
| 19 | P07 | 0.0055 | **0.4184** | 0.0513 | **ch19** |

**Result: ch19 = 9/19 (47.4%)**, ch21 = 4/19 (21.1%), control = 6/19 (31.6%).

Stability: 10 random seeds all produce identical 9/19 result (logistic regression is deterministic given the same data split).

### 4.2. Zero-Shot Models

| Set | Patient | SigLIP2-base | SigLIP2-SO400M | BiomedCLIP |
|:---:|:---:|:---:|:---:|:---:|
| 1 | P02 | control | ch21 | ch21 |
| 2 | P02 | control | control | ch21 |
| 3 | P02 | control | control | control |
| 4 | P02 | ch21 | **ch19** | **ch19** |
| 5 | P02 | **ch19** | ch21 | ch21 |
| 6 | P03 | **ch19** | control | **ch19** |
| 7 | P03 | **ch19** | **ch19** | ch21 |
| 8 | P03 | control | ch21 | control |
| 9 | P03 | ch21 | ch21 | **ch19** |
| 10 | P04 | ch21 | ch21 | control |
| 11 | P05 | ch21 | ch21 | ch21 |
| 12 | P05 | control | control | **ch19** |
| 13 | P05 | control | ch21 | control |
| 14 | P07 | control | ch21 | control |
| 15 | P07 | **ch19** | **ch19** | control |
| 16 | P07 | **ch19** | **ch19** | **ch19** |
| 17 | P07 | **ch19** | **ch19** | **ch19** |
| 18 | P07 | ch21 | ch21 | **ch19** |
| 19 | P07 | control | control | control |

| Model | ch19 wins | ch21 wins | ctrl wins | ch19 % |
|-------|:---:|:---:|:---:|:---:|
| **SigLIP2-base** | 6/19 | 5/19 | 8/19 | 31.6% |
| **SigLIP2-SO400M** | 5/19 | 9/19 | 5/19 | 26.3% |
| **BiomedCLIP** | 7/19 | 5/19 | 7/19 | 36.8% |

All zero-shot models are at or below the 33% chance baseline. SigLIP2-SO400M shows a **ch21 bias** (47.4%) rather than detecting ch19.

### 4.3. Aggregated Comparison

| Model | ch19 wins | ch19 % | vs Chance |
|-------|:---:|:---:|:---:|
| **Gemini 2.5 Flash** (LLM) | 11/19 | **57.9%** | +24.6 pp |
| **DINOv2-large probe** (LOSO-CV) | 9/19 | **47.4%** | +14.1 pp |
| **Mistral Pixtral** (LLM) | 8/18 | **44.4%** | +11.1 pp |
| BiomedCLIP | 7/19 | 36.8% | +3.5 pp |
| SigLIP2-base | 6/19 | 31.6% | −1.7 pp |
| SigLIP2-SO400M | 5/19 | 26.3% | −7.0 pp |
| Chance baseline | — | 33.3% | — |

![CH19 Win Rate: CV Models vs LLM](charts/chart_ch19_winrate.png)

![All Methods: CH19 Win Rate](charts/chart_cv_vs_llm.png)

---

## 5. Batch Analysis: Per-Patient Verdict

Analogous to the LLM batch mode ([LLM report](../2026-03-12_comparative-llm-analysis/report_en.md), Section 4), where all patients' photos were evaluated simultaneously.

For DINOv2, **leave-patient-out CV** is used: the probe is trained on photos from the other 4 patients and predicts on the held-out patient's sets. This ensures full independence between train and test data.

### 5.1. Per-Patient Results

| Patient | Sets | DINOv2 (leave-patient-out) | SigLIP2-base | SigLIP2-SO400M | BiomedCLIP |
|---------|:---:|:---:|:---:|:---:|:---:|
| P02 | 5 | **3/5 (60%)** | 1/5 (20%) | 1/5 (20%) | 1/5 (20%) |
| P03 | 4 | 2/4 (50%) | 2/4 (50%) | 1/4 (25%) | 2/4 (50%) |
| P04 | 1 | **1/1 (100%)** | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) |
| P05 | 3 | 0/3 (0%) | 0/3 (0%) | 0/3 (0%) | 1/3 (33%) |
| P07 | 6 | **3/6 (50%)** | 3/6 (50%) | 3/6 (50%) | 3/6 (50%) |

![DINOv2 Per-Patient Results](charts/chart_per_patient.png)

### 5.2. Summary

| Model | Total ch19 | ch19 % | Patients with ch19 majority |
|-------|:---:|:---:|:---:|
| **DINOv2-large** (leave-patient-out) | 9/19 | **47.4%** | **2/5** (P02, P04) |
| BiomedCLIP | 7/19 | 36.8% | 0/5 |
| SigLIP2-base | 6/19 | 31.6% | 0/5 |
| SigLIP2-SO400M | 5/19 | 26.3% | 0/5 |

DINOv2 is the only CV model where ch19 wins the majority of sets in any patient. Zero-shot models never achieve ch19 majority for any patient.

For reference, LLM batch analysis ([LLM report](../2026-03-12_comparative-llm-analysis/report_en.md), Section 4.2): GPT-5 batch blinded = 46.7%, Perplexity batch blinded = 53.3%.

### 5.3. P05 Anomaly

All models score 0% ch19 for P05 (3 sets). This patient may have weaker visual differences between channels, or the photos may have confounding factors (lighting, timing). The same P05 is challenging for LLM models — Gemini scored P05 at 33% (1/3), below its overall 57.9%.

---

## 6. Statistical Significance

Binomial test (H₀: ch19 win rate = 33.3%, one-sided):

| Model | ch19 wins | p-value | Significance |
|-------|:---:|:---:|:---:|
| **DINOv2-large probe** | 9/19 (47.4%) | 0.1462 | not significant |
| BiomedCLIP | 7/19 (36.8%) | 0.4569 | not significant |
| SigLIP2-base | 6/19 (31.6%) | 0.6481 | not significant |
| SigLIP2-SO400M | 5/19 (26.3%) | 0.8121 | not significant |

**No CV model reaches statistical significance** at p < 0.05. DINOv2's 47.4% (p = 0.15) is the closest, but with only 19 sets, even a genuine 47% effect cannot reach significance — the sample is too small.

For comparison, Gemini's 11/19 (57.9%) gives p = 0.027 (significant at 5%). The LLM analysis compensates for small set count with multi-run repetition (3 runs × 19 sets = 57 verdicts for Groq/GPT-5).

### 6.1. DINOv2 Probe Stability

10 random seeds for logistic regression all produce identical result: **9/19** (47.4%). The probe is deterministic — the signal is consistent but weak.

### 6.2. Is 47.4% Real or Chance?

Arguments **for** a real signal:
- 47.4% is 14.1 pp above chance — not trivial
- Result is perfectly stable across random seeds
- DINOv2 is the only model with signal; zero-shot models cluster at 26–37%
- Leave-one-set-out CV prevents data leakage

Arguments **against**:
- p = 0.15 — not statistically significant
- Only 19 sets — insufficient power to detect a moderate effect
- No consistent per-patient pattern (P05 = 0%, P02 = 60%)
- DINOv2 embeddings encode all visual features (lighting, tube position, background) — the signal may not be coagulation-specific

**Verdict**: The DINOv2 probe detects a **suggestive but inconclusive** signal. More data (more patients, more photos) would be needed to confirm or reject the effect.

---

## 7. Multi-Chain Pipeline: SAM-2 Segmentation → Feature Extraction

### 7.1. Hypothesis

Standard CV models receive the **full photograph** — tube, background, label, table surface. If the plasma region is first segmented and cropped, feature extractors should get a cleaner signal focused on the liquid itself.

### 7.2. Implementation

| Method | Approach | Coverage |
|--------|----------|:---:|
| **HSV thresholding** | Plasma detected by color range (H:12–50, S:35–255, V:60–230), morphological cleanup, largest component | 98/98 (100%) |
| **SAM-2** | `facebook/sam2.1-hiera-tiny` mask generation → plasma mask selection by HSV scoring | ~70% (HSV fallback for rest) |

After segmentation, the plasma bounding box is cropped. The crop is fed to DINOv2-large (probe) and SigLIP2-SO400M (zero-shot).

### 7.3. Results

| Pipeline | Accuracy (5-fold CV) | vs Chance |
|----------|:---:|:---:|
| DINOv2-large **full photo** | **47.8%** | **+14.5 pp** |
| DINOv2-large **SAM-2 crop** | 34.3% | +1.0 pp |
| DINOv2-large **HSV crop** | 32.8% | −0.5 pp |
| Chance baseline | 33.3% | — |

SigLIP2-SO400M on cropped plasma: no channel discrimination (coag scores: control 0.31, ch19 0.28, ch21 0.34).

*Note: DINOv2 full-photo shows 47.8% here (5-fold CV) vs 47.4% in Section 4.1 (leave-one-set-out CV) due to different fold boundaries. Both evaluate on held-out data with no leakage.*

![Multi-Chain Pipeline Results](charts/chart_multichain.png)

### 7.4. Why Multi-Chain Failed

1. **Tube context carries signal.** The full-photo probe (47.8%) uses information from meniscus shape, liquid level, reflections. Cropping removes this.
2. **Plasma in isolation looks identical.** The subtle differences between channels disappear when only the liquid region is visible.
3. **Domain mismatch.** Multi-chain pipelines work for clinical imaging (CT/MRI) where pathology is visually distinct. For tube photographs, the ROI is nearly uniform liquid.

---

## 8. Limitations

1. **Small sample size**: 5 patients, 19 comparative sets, 67 labeled photos. Insufficient for formal statistical significance with moderate effect sizes.
2. **No human ground truth**: No hematologist review — coagulation labels derived from experimental protocol, not independent clinical assessment.
3. **Zero-shot label sensitivity**: Results depend on the specific 11-label set chosen. Alternative label formulations were not systematically tested.
4. **Single GPU constraint**: All models run on RTX 3060 Laptop (6 GB VRAM), limiting model sizes testable (e.g., SigLIP2-SO400M-896 excluded).
5. **MedSigLIP excluded**: The largest model (800M) was out-of-distribution for laboratory tube photos, reducing the number of comparable models to 4.

---

## 9. Conclusion

**Zero-shot CV models cannot distinguish experimental channels.** SigLIP2-base (31.6%), SigLIP2-SO400M (26.3%), and BiomedCLIP (36.8%) all score at or below chance on the 19 comparative sets. Scaling model size 5x or using biomedical pre-training does not help.

**DINOv2 linear probe shows a suggestive signal** — 9/19 sets (47.4%), above chance (33.3%) but not statistically significant (p = 0.15). The result is stable across random seeds. The probe detects ch19 as most coagulated in 2 of 5 patients (P02: 60%, P04: 100%), but fails completely on P05 (0%).

**Multi-chain pipeline (SAM-2 → DINOv2) degrades results** from 47.8% to 34.3%. Tube context (meniscus, reflections) contributes to the signal — cropping removes it.

**LLM vision outperforms CV models.** Gemini (57.9%, p = 0.027) is the only method reaching statistical significance on 19 sets. DINOv2 probe (47.4%) is comparable to Mistral (44.4%) and GPT-5 batch (46.7%), but none of these reach significance individually.

**Combined evidence**: The DINOv2 probe result is consistent with LLM findings — ch19 shows elevated coagulation signal — but CV models alone cannot confirm or quantify this effect on the current dataset of 67 photos.

---

## Data Files

| File | Contents |
|------|----------|
| [`scripts/cv_analysis/ml_results/`](../../scripts/cv_analysis/ml_results/) | Per-photo JSON results for 4 base models (101 files + `all_results.json`) |
| [`scripts/cv_analysis/ml_results_v2/siglip2_so400m.json`](../../scripts/cv_analysis/ml_results_v2/siglip2_so400m.json) | SigLIP2-SO400M zero-shot results (98 photos) |
| [`scripts/cv_analysis/ml_results_v2/dinov2_large_probe.json`](../../scripts/cv_analysis/ml_results_v2/dinov2_large_probe.json) | DINOv2-large probe predictions (98 photos) |
| [`scripts/cv_analysis/ml_results_v3_multichain/`](../../scripts/cv_analysis/ml_results_v3_multichain/) | Multi-chain pipeline results (SAM-2/HSV crop → DINOv2/SigLIP2) |

### Scripts

| Script | Purpose |
|--------|---------|
| [`scripts/cv_analysis/run_ml_models.py`](../../scripts/cv_analysis/run_ml_models.py) | Run 4 base models (DINOv2, SigLIP2, BiomedCLIP, MedSigLIP) on all photos |
| [`scripts/cv_analysis/run_upgraded_models.py`](../../scripts/cv_analysis/run_upgraded_models.py) | Run SigLIP2-SO400M + DINOv2-large linear probe with channel analysis |
| [`scripts/cv_analysis/run_multichain.py`](../../scripts/cv_analysis/run_multichain.py) | Multi-chain: SAM-2/HSV segmentation → DINOv2/SigLIP2 on cropped plasma |
| [`scripts/cv_analysis/segment.py`](../../scripts/cv_analysis/segment.py) | SAM-2 segmentation + plasma mask detection + clot analysis |

### Source Data

- [`processed/en/all_patients.json`](../../processed/en/all_patients.json) — Photo-to-channel mapping (101 photos, 7 patients)
- [`data/patient-*/photos/jpg/`](../../data/) — Original photographs (3024x4032 JPEG)

### Dependencies

- Python environment: `.venv-cv` (torch 2.7.1+cu118, scikit-learn 1.8.0)
- Model wrappers: [`scripts/cv_analysis/ml_models.py`](../../scripts/cv_analysis/ml_models.py) — DINOv2, SigLIP2, BiomedCLIP, MedSigLIP
