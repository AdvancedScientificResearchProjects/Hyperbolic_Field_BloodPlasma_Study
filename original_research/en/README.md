# HyperbolicField-BloodPlasma-Study
Experimental datasets, imaging results and analytical materials from blood plasma exposure to hyperbolic field emitters. Includes raw data, controlled environment documentation and protocol references.

## How to browse data

1. **Select a patient** → table below, click on the number
2. **Patient README** — main file:
   - Protocol (blood group, collection time, centrifugation, irradiation)
   - Sample table (ID, volume, collection time)
   - Photo table with PDF protocol mapping (file → page → caption → samples)
   - EXIF parameters for each photo
   - Photo descriptions (scene, number of samples, plasma morphology)
3. **Photos** → `photos/jpg/` — JPG for browser viewing, `photos/original/` — original HEIC files
4. **PDF protocol** → `protocol_part-*.pdf` — experiment checklist with photos
5. **Structured data** → `analysis.json` — all README data in machine-readable format (including visual photo descriptions)
6. **All-patient summary** → [`processed/all_patients.json`](../processed/en/all_patients.json)

## Patients

| Patient | Date | Blood group | Samples | Photos | Irradiation |
|---------|------|-------------|---------|--------|-------------|
| [01](../data/patient-01/) | 2026-01-24 | II+ | 0.1.1, 0.1.2, 19.1.1, 21.1.1 | 13 | 19:18–20:30 |
| [02](../data/patient-02/) | 2026-01-28 | III+ | 0.2.1, 0.2.2, 19.2.1, 19.2.2, 21.2.1, 21.2.2 | 25 | 20:09–21:24 |
| [03](../data/patient-03/) | 2026-01-29 | IV- | 0.3.1, 0.3.2, 19.3.1, 21.3.1 | 16 | 21:35–22:43 |
| [04](../data/patient-04/) | 2026-01-30 | IV+ | 0.4.1, 0.4.2, 19.4.1, 21.4.1 | 4 | 16:13–17:47 |
| [05](../data/patient-05/) | 2026-01-31 | — | 0.5.1, 19.5.1, 21.5.1 | 10 | –01:21 |
| [06](../data/patient-06/) | 2026-02-01 | I+ | 0.6.1, 0.6.2, 19.6.1, 21.6.1, 19.6.2, 21.6.2 | 3 | –22:17 |
| [07](../data/patient-07/) | 2026-02-07 | — | 0.7.1, 0.7.2, 19.7.1, 21.7.1, 19.7.2, 21.7.2 | 30 | 20:15–21:36 |

## Structure

```
data/patient-XX/
├── en/
│   ├── README.md           # protocol + photo/EXIF tables (English)
│   └── analysis.json       # structured protocol data (English)
├── ru/
│   ├── README.md           # protocol + photo/EXIF tables (Russian)
│   └── analysis.json       # structured protocol data (Russian)
├── metadata.json           # EXIF metadata for all photos
├── protocol_part-*.pdf     # experiment checklist (PDF, may be split)
└── photos/
    ├── original/           # originals (HEIC/JPG)
    └── jpg/                # converted for browser viewing
```

## Sample IDs

Each plasma sample is identified by a code in the format **`{channel}.{patient}.{number}`**.

| Component | Value | Description |
|-----------|-------|-------------|
| Channel | `0` | Control — no irradiation exposure |
| | `19` | Exposure on **channel 19** |
| | `21` | Exposure on **channel 21** |
| Patient | `1`–`7` | Donor (subject) number |
| Number | `1`, `2` | Sequential sample number of this type |

**Examples:**
- `0.2.1` — control sample #1 of patient 02 (no irradiation)
- `19.2.1` — sample #1 of patient 02, irradiated on channel 19
- `21.7.2` — sample #2 of patient 07, irradiated on channel 21

**Sample series:**
- Series `.1` (first sample) — typically 1.5 ml of plasma
- Series `.2` (second sample) — typically 1.0 ml of plasma
- Not all patients have a second series; the number of samples depends on the volume of plasma obtained

## Reports

| Report | Date | Description |
|--------|------|-------------|
| [Experiment protocol](../reports/experiment_protocol_en.md) | 2026-02 | Experiment setup, channels, key observations |
| [AI analysis (8 providers)](../reports/2026-02-25_ai-analysis/report_en.md) | 2026-02-25 | Multi-AI image analysis: 8 Vision API providers, MoA synthesis, CV + ML metrics |
| [LLM Vision clot analysis](../reports/2026-02-26_llm-vision-analysis/report_en.md) | 2026-02-26 | 101-photo clot analysis by Claude Opus 4.6, README-enriched channel mapping, coagulation staging |

## Experiment protocol

General sequence for each patient:
1. **Blood collection** — 4 tubes for centrifuge
2. **Centrifugation** — 2000 rpm, 5 min
3. **Plasma extraction** — distribution into sample tubes (control + irradiated)
4. **Irradiation** — hyperbolic field exposure on channels 19 and 21
5. **Documentation** — photos of samples before/during/after irradiation
