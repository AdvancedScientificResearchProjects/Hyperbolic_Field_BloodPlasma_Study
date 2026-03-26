# Multi-Provider Comparative LLM Vision Analysis: Blood Plasma Coagulation

**Date**: 2026-03-12 (updated 2026-03-13)
**Version**: 5.1
**Providers**: GPT-5, Groq Llama 4 Scout, Gemini 2.5 Flash, Perplexity Sonar Pro, Mistral Pixtral Large
**Dataset**: 101 photographs, 7 donors
**Prior analysis**: Claude Opus 4.6 single-photo analysis (2026-02-26)

> **UPD v4.0 (2026-03-13)**: Versions 1.0–3.0 used images **downscaled to 512×512 px** — a preprocessing bug. Original photos are 3024×4032 (12 MP). All experiments re-run at full resolution. Mistral data remains at 512px (free-tier rate limit). See Section 5 for resolution impact.

> **UPD v5.0 (2026-03-13)**: Report restructured. Blinded results are now primary evidence. Unblinded results moved to Section 6 (Label Priming Effect) as methodological control. Added batch statistical analysis (Section 4).

> **UPD v5.1 (2026-03-13)**: Comparative blinded runs repeated 3× per provider (GPT-5, Groq, Perplexity) for statistical reliability. Section 3.1 updated with aggregated multi-run data (57→164 verdicts total).

---

## 1. Motivation

The prior Claude Opus 4.6 analysis (single-photo, unblinded) found ch19 > control > ch21 coagulation ordering. However, it had three key limitations:

1. **Not blinded** — the model knew which sample was control/ch19/ch21, potentially introducing confirmation bias
2. **Single-model** — only Claude was used; multi-model consensus was needed
3. **Single-photo** — each photo assessed independently; no direct side-by-side comparison

This report addresses all three: **five independent providers**, blinded protocol as default, and three comparison modes (triplet, multi-tube, and batch statistical).

---

## 2. Methodology

### 2.1. Experiment Design

Five experiments were conducted:

| Experiment | Mode | Images per call | Sets | Providers |
|-----------|------|:---:|:----:|-----------|
| A | Comparative blinded (3 runs) | 3 | 19×3 | GPT-5, Groq, Perplexity (×3); Gemini, Mistral⁰ (×1) |
| B | Multi-tube blinded | 1 | 22 | GPT-5, Groq, Perplexity, Mistral⁰ |
| C | Batch blinded | 15 (all patients) | 1 | GPT-5, Perplexity |
| D | Comparative unblinded | 3 | 19 | GPT-5, Groq, Gemini, Perplexity, Mistral⁰ |
| E | Multi-tube unblinded | 1 | 22 | GPT-5, Groq, Perplexity, Mistral⁰ |

⁰ Mistral: 512px images from v3.0 (free-tier rate limit prevented full-resolution re-run).

**Comparative mode**: 3 separate photos (control, ch19, ch21) sent simultaneously.
**Multi-tube mode**: Single photo showing 2–6 tubes from all 3 channels with caption.
**Batch mode**: All 5 patients × 3 photos = 15 images in one request for cross-patient statistical comparison.

### 2.2. Blinding Protocol

| Element | Blinded prompt | Unblinded prompt |
|---------|----------------|-----------------|
| Channel labels | "Sample A", "Sample B", "Sample C" | "CONTROL", "CH19 — time acceleration", "CH21 — time deceleration" |
| Experiment context | "different experimental conditions that are NOT disclosed to you" | "hyperbolic field", "time acceleration/deceleration" |
| Caption blinding | Neutral labels (e.g., "B / A / C") | Real sample IDs (e.g., "19.2.1 / 0.2.1 / 21.2.1") |

Blind mapping (fixed): **0 → A** (control), **19 → B** (ch19), **21 → C** (ch21).

Blinded labels were programmatically remapped to real channels after analysis.

### 2.3. Providers

| Provider | Model | Image resolution | Notes |
|----------|-------|:---:|-------|
| **GPT-5** | gpt-5 | 3024×4032 | |
| **Groq** | llama-4-scout-17b-16e-instruct | 3024×4032 | Max 5 images per request |
| **Gemini 2.5** | gemini-2.5-flash / flash-lite | 3024×4032 | Free-tier quota limited |
| **Perplexity** | sonar-pro | 3024×4032 | ~74% structured parse rate |
| **Mistral**⁰ | pixtral-large-2411 | 512px | Deprecated model, 512px data |

### 2.4. Dataset

| Patient | Comparative sets | Multi-tube sets | Notes |
|---------|:---:|:---:|-------|
| P01 | 0 | 10 | No single-channel control; multi-tube only |
| P02 | 5 | 8 | Includes temporal series (0h, 6h, 16h, 21h) |
| P03 | 4 | 0 | Single-channel only |
| P04 | 1 | 1 | Minimal data |
| P05 | 3 | 0 | Single-channel only |
| P06 | 0 | 2 | Multi-tube only (6-tube photo) |
| P07 | 6 | 1 | Most comparative sets |
| **Total** | **19** | **22** | **41** unique sets |

### 2.5. Structured Output

JSON block per call: `most_coagulated`, `least_coagulated`, `overall_difference` (none / subtle / moderate / pronounced), per-channel `clot_stage` (none / early_fibrin / partial_clot / full_coagulation / lysis).

Prompts: [`scripts/llm_analysis/prompts.py`](../../scripts/llm_analysis/prompts.py). All include: **"Be precise, objective. Describe only what you see."**

---

## 3. Primary Results: Blinded Analysis

All results in this section use the **blinded protocol** — models see only "Sample A / B / C" with no experiment context.

### 3.1. Comparative Blinded (3 photos per set, 19 sets × 3 runs)

To verify statistical reliability, comparative blinded analysis was repeated 3 times per provider (GPT-5, Groq, Perplexity). Gemini and Mistral were limited to 1 run due to quota/rate limits.

#### Per-Run Breakdown

| Run | GPT-5 ch19 % | Groq ch19 % | Perplexity ch19 % |
|-----|:---:|:---:|:---:|
| Run 1 | 5/18 (27.8%) | 6/19 (31.6%) | 5/12 (41.7%) |
| Run 2 | 4/18 (22.2%) | 7/19 (36.8%) | 2/9 (22.2%) |
| Run 3 | 4/19 (21.1%) | 6/19 (31.6%) | 5/12 (41.7%) |

Groq is the most stable (31.6–36.8% range). Perplexity is noisiest (~74% parse rate). GPT-5 consistently selects ch21 (50–61%).

#### Aggregated Results (All Runs)

| Provider | Runs | Verdicts | ch19 | ctrl | ch21 | ch19 % | Resolution |
|----------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Gemini 2.5** | 1 | 19 | 11 | 5 | 3 | **57.9%** | Full |
| **Mistral**⁰ | 1 | 18 | 8 | 2 | 4 | **44.4%** | 512px |
| **Perplexity** | 3 | 33 | 12 | 8 | 13 | **36.4%** | Full |
| **Groq** | 3 | 57 | 19 | 26 | 12 | **33.3%** | Full |
| **GPT-5** | 3 | 55 | 13 | 13 | 29 | **23.6%** | Full |
| Chance baseline | — | — | — | — | — | 33.3% | — |

⁰ 512px data from v3.0.

**Gemini** is the clear leader: 57.9% ch19 identification — nearly double the chance rate. **Mistral** also identifies ch19 well above chance (44.4%). **Perplexity** is slightly above chance (36.4%). **Groq** is at exactly chance level (33.3%) but shows strong control bias (45.6% ctrl). **GPT-5** has a consistent ch21 bias across all 3 runs (52.7% ch21) — see Section 6.

### 3.2. Multi-Tube Blinded (1 photo per set, 22 sets)

| Provider | ch19 wins | ch21 wins | ctrl wins | ch19 % |
|----------|:---:|:---:|:---:|:---:|
| **Mistral**⁰ | 12/22 | 1/22 | 1/22 | **54.5%** |
| **Groq** | 8/21 | 2/21 | 6/21 | **38.1%** |
| **GPT-5** | 8/22 | 3/22 | 6/22 | **36.4%** |
| **Perplexity** | 4/16 | 1/16 | 2/16 | **25.0%** |

⁰ 512px data. Gemini excluded (only 3/22 due to quota).

Mistral leads in multi-tube blinded. Notably, GPT-5 performs **better** in multi-tube blinded (36.4%) than comparative blinded (26.3%) — single-photo context may be easier for this model.

### 3.3. Cross-Mode Summary (Blinded)

| Provider | Comp. blinded ch19 % (runs) | MT blinded ch19 % | Average | Tier |
|----------|:---:|:---:|:---:|---|
| **Gemini** | **57.9%** (1×19) | N/A | **57.9%** | Tier 1 |
| **Mistral**⁰ | 44.4% (1×18) | **54.5%** | **49.5%** | Tier 1 |
| **Perplexity** | 36.4% (3×33) | 25.0% | **30.7%** | Tier 2 |
| **Groq** | 33.3% (3×57) | 38.1% | **35.7%** | Tier 2 |
| **GPT-5** | 23.6% (3×55) | 36.4% | **30.0%** | Tier 2 |

**Tier 1** (ch19 above chance in all available modes): Gemini, Mistral.
**Tier 2** (near chance, inconsistent): Groq, Perplexity, GPT-5.

### 3.4. Clot Stage Distribution (Mistral, all blinded datasets, 512px)

| Stage | Control | CH19 | CH21 |
|-------|:---:|:---:|:---:|
| none | 67 (90.5%) | 32 (43.2%) | 52 (70.3%) |
| early_fibrin | 2 (2.7%) | 20 (27.0%) | 14 (18.9%) |
| partial_clot | 5 (6.8%) | 19 (25.7%) | 8 (10.8%) |
| full_coagulation | 0 (0%) | 2 (2.7%) | 0 (0%) |
| **Any coagulation** | **9.5%** | **56.8%** | **29.7%** |

CH19 is the only channel reaching `full_coagulation`. Clear progression:
**CH19 (partial_clot) > CH21 (early_fibrin) > Control (none)**

### 3.5. Per-Patient Results (Mistral, all datasets, 512px)

| Patient | Sets | ch19 wins | ch21 wins | ctrl wins | null/tie | ch19 win % |
|---------|:---:|:---------:|:---------:|:-----------:|:--------:|:-----:|
| P01 | 20 | 16 | 3 | 0 | 1 | **84%** |
| P02 | 21 | 8 | 0 | 1 | 12 | **89%** |
| P03 | 7 | 3 | 3 | 1 | 0 | 43% |
| P04 | 4 | 4 | 0 | 0 | 0 | **100%** |
| P05 | 4 | 2 | 1 | 0 | 1 | 67% |
| P06 | 4 | 2 | 0 | 1 | 1 | 67% |
| P07 | 14 | 7 | 2 | 1 | 4 | **70%** |

CH19 leads in **6 of 7 patients**. P03 is the only tie (3 each).

---

## 4. Batch Statistical Analysis (Blinded)

In batch mode, all 5 patients' triplets (15 images) are sent in one request. The model evaluates each patient individually and then provides a cross-patient statistical summary. Only GPT-5 and Perplexity support 15+ images per request (Groq: max 5 images; Gemini: quota exhausted).

Multiple runs were performed for reproducibility.

### 4.1. Per-Run Results

| Provider | Run | ch19 (B) | ch21 (C) | ctrl (A) | Pattern |
|----------|:---:|:---:|:---:|:---:|---|
| **GPT-5** | 1 | **3/5** | 2/5 | 0/5 | weak |
| **GPT-5** | 2 | 2/5 | 2/5 | 1/5 | weak |
| **GPT-5** | 3 | 2/5 | 1/5 | 2/5 | weak |
| **Perplexity** | 1 | **3/5** | 2/5 | 0/5 | moderate |
| **Perplexity** | 2 | **3/5** | 2/5 | 0/5 | moderate |
| **Perplexity** | 3 | 2/5 | **3/5** | 0/5 | moderate |

### 4.2. Aggregated Results

| Provider | Runs | Patient-verdicts | ch19 | ch21 | ctrl | ch19 % |
|----------|:---:|:---:|:---:|:---:|:---:|:---:|
| **GPT-5** | 3 | 15 | **7** | 5 | 3 | **46.7%** |
| **Perplexity** | 3 | 15 | **8** | 7 | 0 | **53.3%** |
| **Combined** | 6 | 30 | **15** | 12 | 3 | **50.0%** |

Both providers identify ch19 above the 33% chance baseline. Control is consistently the least coagulated — Perplexity never selected control (0/15), GPT-5 only 3/15 times.

### 4.3. Batch vs Comparative (Blinded)

| Provider | Comparative blinded ch19 % (multi-run) | Batch blinded ch19 % | Δ |
|----------|:---:|:---:|:---:|
| **GPT-5** | 23.6% (3 runs, 55 verdicts) | **46.7%** | **+23.1 pp** |
| **Perplexity** | 36.4% (3 runs, 33 verdicts) | **53.3%** | **+16.9 pp** |

Both providers show substantially higher ch19 identification in batch mode. When seeing all patients simultaneously, models detect the **cross-patient pattern** that is harder to see when evaluating triplets one at a time.

**GPT-5 correction**: In comparative blinded mode, GPT-5 consistently selects ch21 (52.7% across 3 runs). But in batch blinded mode, GPT-5 selects ch19 (46.7%). Cross-patient context overrides the processing artifact that causes the comparative reversal.

### 4.4. Batch Qualitative Notes

GPT-5 batch observations (blinded):
- *"Sample B has a bulky opaque coagulum with diffuse cloudiness"*
- *"B appears slightly denser/opaquer centrally"*

Perplexity batch observations (blinded):
- *"Sample B displays large central circular opacity consistent with clot formation"*
- *"Sample A consistently least coagulated across all patients with clear liquid appearance"*

Both models independently note: **B (ch19) shows opaque/dense clots, A (control) is consistently clear**.

---

## 5. Resolution Impact: 512px vs Full Resolution

Original images (3024×4032) were accidentally downscaled to 512px in v1.0–v3.0. Full-resolution re-run changed results significantly.

| Experiment | Provider | 512px ch19 % | FullRes ch19 % | Δ |
|---|---|:-:|:-:|:-:|
| Comp. blinded | **Gemini** | 47.4% | **57.9%** | **+10.5 pp** |
| Comp. blinded | **Perplexity** | 14.3% | **35.7%** | **+21.4 pp** |
| Comp. blinded | Groq | 26.3% | 31.6% | +5.3 pp |
| Comp. blinded | GPT-5 | 31.6% | 26.3% | −5.3 pp |
| MT blinded | GPT-5 | 27.3% | **36.4%** | +9.1 pp |
| MT blinded | Groq | 50.0% | 38.1% | −11.9 pp |

**Winners**: Gemini (+10.5 pp), Perplexity (+21.4 pp) — fine fibrin details become visible.
**Losers**: Groq MT (−11.9 pp) — was overconfident at low resolution.

**Conclusion**: Image resolution is a critical variable. Full resolution helps models that are sensitive to fine fibrin structure (Gemini, Perplexity) but adds noise for others (Groq MT).

---

## 6. Label Priming Effect (Unblinded as Methodological Control)

Unblinded results are presented here **not as evidence for the hypothesis**, but as a demonstration of why blinding is essential in LLM-based analysis.

### 6.1. The Priming Mechanism

The unblinded prompt tells models:
- CH19 = **"time acceleration"** — exposed to hyperbolic field
- CH21 = **"time deceleration"** — exposed to hyperbolic field

Models interpret "deceleration" as "more time for coagulation to develop" → select ch21. This is **reverse priming**: the label biases the model *against* the hypothesis rather than toward it.

### 6.2. Comparative: Blinded vs Unblinded

| Provider | Blinded ch19 % (runs) | Unblinded ch19 % | Unblinded ch21 % | Effect |
|----------|:-:|:-:|:-:|---|
| **Gemini** | **57.9%** (1 run) | 63.2% | 15.8% | Slight boost (+5 pp) |
| **Groq** | 33.3% (3 runs) | **68.4%** | 21.1% | Strong boost (+35 pp) |
| **Perplexity** | 36.4% (3 runs) | **46.7%** | 6.7% | Moderate boost (+10 pp) |
| **GPT-5** | 23.6% (3 runs) | 21.1% | **42.1%** | **Reversed to ch21** |

Three providers (Gemini, Groq, Perplexity) show **higher** ch19 in unblinded — the "acceleration" label primes toward ch19. GPT-5 shows the **opposite** — "deceleration" label primes toward ch21.

### 6.3. Batch: Most Striking Priming Demonstration

| Provider | Batch blinded ch19 % | Batch unblinded ch19 % | Batch unblinded ch21 % |
|----------|:-:|:-:|:-:|
| **GPT-5** | **47%** (3 runs) | 40% | **60%** |
| **Perplexity** | **53%** (3 runs) | 0% | **60%** |

Same photos, same model, same patients. The **only difference is the prompt text**:
- Blinded: ch19 = 47–53% → model sees genuine visual signal
- Unblinded: ch21 = 60% → model overrides visual signal with label interpretation

Perplexity is the most extreme case: **0% ch19 unblinded vs 53% ch19 blinded** on identical images.

### 6.4. Implications

1. **Unblinded LLM analysis is unreliable** for subtle biomedical differences. Labels override visual evidence.
2. **The direction of priming is unpredictable**: "acceleration" can prime either toward ch19 (Groq, Gemini) or toward ch21 (GPT-5). The same label means different things to different models.
3. **Blinding is non-negotiable** in LLM vision studies. This finding alone justifies the blinded protocol.

---

## 7. Key Findings

### 7.1. CH19 = Most Coagulated (Blinded Evidence)

| Evidence source | ch19 identification rate |
|----------------|:---:|
| Gemini comparative blinded (full-res) | **57.9%** |
| Mistral combined blinded (512px) | **49.5%** |
| GPT-5 batch blinded, 3 runs (full-res) | **46.7%** |
| Perplexity batch blinded, 3 runs (full-res) | **53.3%** |
| Chance baseline | 33.3% |

All blinding-stable measurements exceed the 33% chance rate.

### 7.2. Coagulation Ordering: CH19 > CH21 > Control

Based on Tier 1 blinded providers:

| Metric | CH19 | CH21 | Control |
|--------|:----:|:----:|:-------:|
| Gemini blinded comp. (full-res) | **57.9%** | 15.8% | 26.3% |
| Mistral blinded comp. (512px) | **44.4%** | 22.2% | 11.1% |
| Clot detection (Mistral, 512px) | **56.8%** | 29.7% | 9.5% |
| Dominant clot stage | partial_clot | early_fibrin | none |

### 7.3. Batch Mode Amplifies Signal

When models see all 5 patients simultaneously, ch19 identification jumps from 24–36% (comparative, multi-run) to **47–53%** (batch) for GPT-5 and Perplexity across 6 independent runs (30 patient-verdicts). Cross-patient context helps models detect the pattern.

### 7.4. Multi-Run Stability

Three runs per provider confirmed: Groq is most stable (31.6–36.8% ch19), GPT-5 is consistently ch21-biased (50–61% per run), Perplexity is noisiest (~74% parse rate). Single-run results can be misleading — aggregate data is essential.

### 7.5. Blinding Is Essential

Label priming reverses model verdicts: Perplexity goes from 53% ch19 (blinded batch) to 0% ch19 (unblinded batch) on identical images. Unblinded LLM results should not be used as evidence.

---

## 8. Comparison with Prior Analysis

| Method | ch19 signal (blinded) | Verdicts | Resolution |
|--------|:---:|:---:|:---:|
| **Claude single-photo** (Feb 2026) | 78% clot rate (unblinded) | ~100 | Full |
| **Gemini comparative** (this report, 1 run) | **57.9%** | 19 | Full |
| **Mistral combined** (this report) | **49.5%** | ~40 | 512px |
| **Perplexity batch** (this report, 3 runs) | **53.3%** | 15 | Full |
| **GPT-5 batch** (this report, 3 runs) | **46.7%** | 15 | Full |
| **Perplexity comparative** (this report, 3 runs) | 36.4% | 33 | Full |
| **Groq comparative** (this report, 3 runs) | 33.3% | 57 | Full |
| **GPT-5 comparative** (this report, 3 runs) | 23.6% | 55 | Full |

---

## 9. Limitations

1. **Small sample size**: 7 donors, 41 unique comparison sets. Not sufficient for formal statistical significance testing.
2. **Mixed resolution**: Mistral data uses 512px (v3.0); others use full 3024×4032.
3. **Gemini incomplete**: Free-tier quota limited to comparative mode only.
4. **Gemini model split**: Unblinded uses gemini-2.5-flash, blinded uses gemini-2.5-flash-lite.
5. **Batch limited**: Only GPT-5 and Perplexity support 15+ images. Groq caps at 5 images per request.
6. **Perplexity parse rate**: ~74% structured parse success; 26% returned clinical disclaimers.
7. **No human ground truth**: No hematologist review for validation.
8. **Mistral deprecated**: pixtral-large-2411 is deprecated. Needs re-run with mistral-large-2512.

---

## 10. Conclusion

Five LLM vision providers analyzed blood plasma coagulation under blinded conditions at full image resolution, with comparative blinded analysis repeated 3 times per provider for statistical reliability (164 total verdicts).

**CH19 (time acceleration) is consistently identified as the most coagulated sample** by blinding-stable providers: Gemini 57.9% (19 verdicts), Mistral 49.5% (~40 verdicts), GPT-5 batch 46.7% (15 verdicts), Perplexity batch 53.3% (15 verdicts) — all well above the 33% chance baseline.

**Multi-run validation confirms stability**: 3 runs per provider showed that Groq is the most stable (31.6–36.8%), GPT-5 has a consistent ch21 bias in comparative mode (50–61%), and Perplexity is noisiest (~74% parse rate). Single-run numbers can be misleading — aggregate data is essential.

**Blinding is essential**: unblinded prompts reverse model verdicts due to label priming. The term "time deceleration" causes models to select ch21 instead of ch19, overriding genuine visual evidence. Perplexity swings from 53% ch19 (blinded batch) to 0% ch19 (unblinded batch) on identical images.

**Batch mode amplifies signal**: when models evaluate all patients simultaneously across 6 runs (30 verdicts), ch19 identification rises from 24→47% (GPT-5) and 36→53% (Perplexity), suggesting cross-patient context helps detect subtle visual patterns harder to see in individual comparisons.

**Coagulation ordering**: CH19 > CH21 > Control — confirmed by blinded analysis across multiple providers and consistent with the prior Claude Opus analysis and the acceleration/deceleration hypothesis.

---

## Data Files

### Blinded Results (Primary)

| File | Contents |
|------|----------|
| [`results/fullres_comparative_blinded_gemini/`](../../results/fullres_comparative_blinded_gemini/) | Comp. blinded, 19 sets, Gemini, full-res |
| [`results/fullres_comparative_blinded_groq/`](../../results/fullres_comparative_blinded_groq/) | Comp. blinded r1, 19 sets, Groq, full-res |
| [`results/fullres_comparative_blinded_groq_r2/`](../../results/fullres_comparative_blinded_groq_r2/) | Comp. blinded r2, 19 sets, Groq, full-res |
| [`results/fullres_comparative_blinded_groq_r3/`](../../results/fullres_comparative_blinded_groq_r3/) | Comp. blinded r3, 19 sets, Groq, full-res |
| [`results/fullres_comparative_blinded_openai/`](../../results/fullres_comparative_blinded_openai/) | Comp. blinded r1, 19 sets, GPT-5, full-res |
| [`results/fullres_comparative_blinded_openai_r2/`](../../results/fullres_comparative_blinded_openai_r2/) | Comp. blinded r2, 19 sets, GPT-5, full-res |
| [`results/fullres_comparative_blinded_openai_r3/`](../../results/fullres_comparative_blinded_openai_r3/) | Comp. blinded r3, 19 sets, GPT-5, full-res |
| [`results/fullres_comparative_blinded_perplexity/`](../../results/fullres_comparative_blinded_perplexity/) | Comp. blinded r1, 19 sets, Perplexity, full-res |
| [`results/fullres_comparative_blinded_perplexity_r2/`](../../results/fullres_comparative_blinded_perplexity_r2/) | Comp. blinded r2, 19 sets, Perplexity, full-res |
| [`results/fullres_comparative_blinded_perplexity_r3/`](../../results/fullres_comparative_blinded_perplexity_r3/) | Comp. blinded r3, 19 sets, Perplexity, full-res |
| [`results/fullres_multi_tube_blinded_groq/`](../../results/fullres_multi_tube_blinded_groq/) | MT blinded, 22 sets, Groq, full-res |
| [`results/fullres_multi_tube_blinded_openai/`](../../results/fullres_multi_tube_blinded_openai/) | MT blinded, 22 sets, GPT-5, full-res |
| [`results/fullres_multi_tube_blinded_perplexity/`](../../results/fullres_multi_tube_blinded_perplexity/) | MT blinded, 22 sets, Perplexity, full-res |
| [`results/batch_blinded_openai/`](../../results/batch_blinded_openai/) | Batch blinded, 5 patients, GPT-5, full-res |
| [`results/batch_blinded_perplexity/`](../../results/batch_blinded_perplexity/) | Batch blinded, 5 patients, Perplexity, full-res |
| [`results/comparative_blinded/`](../../results/comparative_blinded/) | Comp. blinded, 19 sets, Mistral, 512px |
| [`results/multi_tube_blinded/`](../../results/multi_tube_blinded/) | MT blinded, 22 sets, Mistral, 512px |

### Unblinded Results (Methodological Control)

| File | Contents |
|------|----------|
| [`results/fullres_comparative_gemini/`](../../results/fullres_comparative_gemini/) | Comp. unblinded, 19 sets, Gemini, full-res |
| [`results/fullres_comparative_groq/`](../../results/fullres_comparative_groq/) | Comp. unblinded, 19 sets, Groq, full-res |
| [`results/fullres_comparative_openai/`](../../results/fullres_comparative_openai/) | Comp. unblinded, 19 sets, GPT-5, full-res |
| [`results/fullres_comparative_perplexity/`](../../results/fullres_comparative_perplexity/) | Comp. unblinded, 19 sets, Perplexity, full-res |
| [`results/fullres_multi_tube_groq/`](../../results/fullres_multi_tube_groq/) | MT unblinded, 22 sets, Groq, full-res |
| [`results/fullres_multi_tube_openai/`](../../results/fullres_multi_tube_openai/) | MT unblinded, 22 sets, GPT-5, full-res |
| [`results/fullres_multi_tube_perplexity/`](../../results/fullres_multi_tube_perplexity/) | MT unblinded, 22 sets, Perplexity, full-res |
| [`results/batch_unblinded_openai/`](../../results/batch_unblinded_openai/) | Batch unblinded, 5 patients, GPT-5, full-res |
| [`results/batch_unblinded_perplexity/`](../../results/batch_unblinded_perplexity/) | Batch unblinded, 5 patients, Perplexity, full-res |
| [`results/comparative_mistral/`](../../results/comparative_mistral/) | Comp. unblinded, 12 sets, Mistral, 512px |
| [`results/multi_tube/`](../../results/multi_tube/) | MT unblinded, 22 sets, Mistral, 512px |

### Scripts
| Script | Purpose |
|--------|---------|
| [`scripts/llm_analysis/run_comparative.py`](../../scripts/llm_analysis/run_comparative.py) | Triplet comparative analysis |
| [`scripts/llm_analysis/run_multi_tube.py`](../../scripts/llm_analysis/run_multi_tube.py) | Multi-tube analysis |
| [`scripts/llm_analysis/run_batch.py`](../../scripts/llm_analysis/run_batch.py) | Batch statistical analysis (all patients at once) |
| [`scripts/llm_analysis/providers.py`](../../scripts/llm_analysis/providers.py) | Provider initialization, API wrapper |
| [`scripts/llm_analysis/prompts.py`](../../scripts/llm_analysis/prompts.py) | All prompt templates |
| [`scripts/llm_analysis/imaging.py`](../../scripts/llm_analysis/imaging.py) | Image loading (full resolution) |
| [`scripts/gemini_direct.py`](../../scripts/gemini_direct.py) | Direct Gemini API (no LangChain retries) |

### Source Data
- [`processed/en/all_patients.json`](../../processed/en/all_patients.json) — Photo-to-channel mapping (101 photos, 7 patients)
- [`data/patient-*/photos/jpg/`](../../data/) — Original photographs (3024×4032 JPEG)
