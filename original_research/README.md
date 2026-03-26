# Original Research Data & Code

Experimental datasets, imaging results and analytical materials from blood plasma exposure to hyperbolic field emitters. Includes raw data, controlled environment documentation, protocol references, analysis scripts and reports.

> Imported from the original working repository (`HyperbolicField-BloodPlasma-Study`).

---

## File Structure

```
original_research/
├── data/                          # Raw experimental data (7 patients, 101 photos)
│   └── patient-XX/
│       ├── photos/
│       │   ├── original/          # HEIC (iPhone 16 Pro Max, 4032×3024)
│       │   └── jpg/               # JPG conversions
│       ├── protocol_part-*.pdf    # Physical experiment protocols with embedded photos
│       ├── metadata.json          # EXIF data
│       └── en/
│           ├── README.md          # Per-patient protocol, sample table, descriptions
│           └── analysis.json      # Structured analysis data
│
├── scripts/                       # Analysis code
│   ├── llm_analysis/              # Multi-LLM vision analysis framework
│   │   ├── providers.py           # 9 providers: GPT-5, Gemini, Claude, Groq, etc.
│   │   ├── prompts.py             # Single, comparative, batch, blinded prompts
│   │   ├── run_single.py          # Single-photo analysis
│   │   ├── run_comparative.py     # Triplet (control + ch19 + ch21) analysis
│   │   ├── run_batch.py           # All-patients batch analysis
│   │   └── ...
│   ├── cv_analysis/               # Computer vision / ML pipeline
│   │   ├── segment.py             # SAM-2 + HSV plasma masking + CV clot detection
│   │   ├── ml_models.py           # DINOv2, SigLIP2, MedSigLIP, BiomedCLIP
│   │   ├── ml_results/            # Per-photo ML model outputs (101 files)
│   │   └── ...
│   ├── merge_patients.py          # Merge per-patient JSON → all_patients.json
│   ├── generate_charts.py         # Chart generation for reports
│   └── ...
│
├── results/                       # LLM analysis run outputs (~50 runs)
│   ├── comparative_*/             # Comparative triplet results per provider
│   ├── fullres_comparative_*/     # Full-resolution comparative results
│   ├── batch_blinded_*/           # Batch blinded analysis results
│   ├── multi_tube_*/              # Multi-tube photo analysis
│   └── api_logs/                  # Daily JSONL API call logs
│
├── reports/                       # Analysis reports with charts
│   ├── experiment_protocol_en.md  # Experiment protocol summary
│   ├── 2026-02-25_ai-analysis/    # First AI analysis (CV + ML + 8 providers)
│   ├── 2026-02-26_llm-vision-analysis/  # Claude Opus single-photo analysis
│   ├── 2026-03-12_comparative-llm-analysis/  # 5-provider blinded comparative
│   └── 2026-03-14_cv-ml-analysis/ # CV/ML model analysis (DINOv2, SigLIP2, SAM-2)
│
├── notebooks/
│   └── cv_analysis.ipynb          # CV analysis Jupyter notebook
│
├── processed/
│   └── en/all_patients.json       # Merged master JSON (all 7 patients)
│
└── en/
    └── README.md                  # English documentation index
```

## Patients

| # | Date | Blood Group | Photos | Protocols |
|---|------|-------------|--------|-----------|
| 01 | 2026-01-24 | II+ | 13 | 2 PDF |
| 02 | 2026-01-28 | III+ | 25 | 3 PDF |
| 03 | 2026-01-29 | IV- | 16 | 1 PDF |
| 04 | 2026-01-30 | IV+ | 4 | 1 PDF |
| 05 | 2026-01-31 | — | 10 | 1 PDF |
| 06 | 2026-02-01 | I+ | 3 | 1 PDF |
| 07 | 2026-02-07 | — | 30 | 2 PDF |

**Total: 101 photographs, 10 PDF protocols, 7 patients**

## Sample ID Format

`{channel}.{patient}.{number}` — e.g. `19.2.1` = Channel 19, Patient 02, Sample 1

- **Channel 0** — Control (no exposure)
- **Channel 19** — Time-acceleration hyperbolic field
- **Channel 21** — Time-deceleration hyperbolic field
