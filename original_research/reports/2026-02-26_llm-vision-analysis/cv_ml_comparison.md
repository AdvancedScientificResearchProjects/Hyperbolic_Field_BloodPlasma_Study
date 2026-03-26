# Experiment Analysis Summary

Generated: 2026-02-25T16:19:13.450701

## Channel Distribution
- Control (0): 13 photos
- Ch19 acceleration: 14 photos
- Ch21 deceleration: 13 photos
- Multi-channel: 61 photos (excluded)

## Segment Analysis (Clots)

| Metric | Control (0) | Ch19 (accel) | Ch21 (decel) | Ch19 delta | Ch21 delta |
|--------|-------------|--------------|--------------|------------|------------|
| Clot count | 8.92 | 5.64 | 8.69 | -36.77% | -2.58% |
| Clot area ratio | 0.009004 | 0.005206 | 0.005825 | -42.18% | -35.31% |

## SigLIP2 Coagulation Stage Classification

### Control
- Top stage: **none**
- Distribution: {'none': 12, 'partial_clot': 1}
- Mean scores per stage:
  - none: 0.6427
  - early_fibrin: 0.2135
  - partial_clot: 0.3694
  - full_coagulation: 0.2739
  - lysis: 0.4952

### Ch19 acceleration
- Top stage: **none**
- Distribution: {'none': 14}
- Mean scores per stage:
  - none: 0.7317
  - early_fibrin: 0.2664
  - partial_clot: 0.4506
  - full_coagulation: 0.3349
  - lysis: 0.5949

### Ch21 deceleration
- Top stage: **none**
- Distribution: {'none': 12, 'lysis': 1}
- Mean scores per stage:
  - none: 0.7907
  - early_fibrin: 0.2527
  - partial_clot: 0.4644
  - full_coagulation: 0.3637
  - lysis: 0.6256

## CV Metrics

| Metric | Control | Ch19 | Ch21 | Ch19 delta% | Ch21 delta% |
|--------|---------|------|------|-------------|-------------|
| brightness_mean | 166.2973 | 166.417 | 160.4751 | 0.07% | -3.5% |
| entropy | 6.1424 | 6.2284 | 6.2653 | 1.4% | 2.0% |
| glcm_contrast | 4.1215 | 5.2593 | 4.1642 | 27.61% | 1.04% |
| glcm_homogeneity | 0.9522 | 0.9498 | 0.9447 | -0.25% | -0.79% |
| edge_density | 0.0016 | 0.0012 | 0.0034 | -25.0% | 112.5% |

## Hypothesis Check

**Hypothesis**: Ch19 (acceleration) samples should look 'older' (more lysis, fewer/dissolving clots).
Ch21 (deceleration) samples should look 'younger' (early formation, denser clots).

- Control stage: **none**
- Ch19 stage: **none** (expect: lysis or late)
- Ch21 stage: **none** (expect: early_fibrin or early)
- Ch19 clot count vs control: -36.77%
- Ch21 clot count vs control: -2.58%