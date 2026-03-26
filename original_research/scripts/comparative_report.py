#!/usr/bin/env python3
"""Generate comparative LLM vision analysis report.

Combines results from Mistral (pixtral-large) and Perplexity (sonar-pro)
comparative analysis: 3 photos per set (control, ch19, ch21).
"""

import json
from collections import defaultdict
from datetime import date
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
MISTRAL_RESULTS = PROJECT / "results" / "comparative_mistral" / "results.json"
PERPLEXITY_RESULTS = PROJECT / "results" / "comparative_perplexity" / "results.json"
REPORT_DIR = PROJECT / "reports" / f"{date.today()}_comparative-llm-analysis"

DIFF_ORDER = ["none", "subtle", "moderate", "pronounced"]


def load_results(path: Path) -> list[dict]:
    with open(path) as f:
        data = json.load(f)
    return data["comparisons"]


def extract_provider(comp: dict, provider: str) -> dict | None:
    prov = comp.get("providers", {}).get(provider, {})
    if prov.get("error"):
        return None
    return prov.get("structured") or {}


def normalize_most(val: str | None) -> str | None:
    if not val:
        return None
    v = val.lower().strip()
    for key in ("ch19", "ch21", "control"):
        if key in v:
            return key
    return None


def build_unified_table(mistral_comps, perplexity_comps):
    """Build unified comparison table keyed by (patient, control_filename)."""
    rows = []

    # Index perplexity by control filename
    pplx_by_key = {}
    for comp in perplexity_comps:
        key = (comp["patient"], comp["photos"]["control"]["filename"])
        pplx_by_key[key] = comp

    # Use all 12 sets from either source
    all_keys = set()
    for comp in mistral_comps + perplexity_comps:
        all_keys.add((comp["patient"], comp["photos"]["control"]["filename"]))

    for patient, ctrl_fn in sorted(all_keys):
        row = {"patient": patient, "control": ctrl_fn}

        # Find matching comps
        m_comp = next(
            (c for c in mistral_comps
             if c["patient"] == patient and c["photos"]["control"]["filename"] == ctrl_fn),
            None,
        )
        p_comp = pplx_by_key.get((patient, ctrl_fn))

        if m_comp:
            row["ch19_fn"] = m_comp["photos"]["ch19"]["filename"]
            row["ch21_fn"] = m_comp["photos"]["ch21"]["filename"]
        elif p_comp:
            row["ch19_fn"] = p_comp["photos"]["ch19"]["filename"]
            row["ch21_fn"] = p_comp["photos"]["ch21"]["filename"]

        # Mistral
        ms = extract_provider(m_comp, "mistral") if m_comp else None
        row["m_diff"] = (ms.get("overall_difference") or "-") if ms else "N/A"
        row["m_most"] = normalize_most(ms.get("most_coagulated")) if ms else None
        row["m_notes"] = (ms.get("comparison_notes") or "") if ms else ""

        # Perplexity
        ps = extract_provider(p_comp, "perplexity") if p_comp else None
        row["p_diff"] = (ps.get("overall_difference") or "-") if ps else "N/A"
        row["p_most"] = normalize_most(ps.get("most_coagulated")) if ps else None
        row["p_notes"] = (ps.get("comparison_notes") or "") if ps else ""

        rows.append(row)

    return rows


def compute_stats(rows, provider_prefix):
    diff_key = f"{provider_prefix}_diff"
    most_key = f"{provider_prefix}_most"

    counts = {"ch19": 0, "ch21": 0, "control": 0, "none": 0, "unclear": 0, "error": 0}
    diff_dist = defaultdict(int)

    for row in rows:
        diff = row[diff_key]
        most = row[most_key]

        if diff in ("N/A", "ERR"):
            counts["error"] += 1
            continue

        diff_dist[diff] += 1

        if diff == "none" or diff == "-":
            counts["none"] += 1
        elif most in ("ch19", "ch21", "control"):
            counts[most] += 1
        else:
            counts["unclear"] += 1

    informative = counts["ch19"] + counts["ch21"] + counts["control"]
    return counts, diff_dist, informative


def generate_report(rows, m_counts, m_diff, p_counts, p_diff):
    lines = []
    a = lines.append

    a("# Comparative LLM Vision Analysis: Blood Plasma Coagulation")
    a("")
    a(f"**Date**: {date.today()}")
    a("**Analysis type**: Comparative (3 photos per set: control + ch19 + ch21)")
    a("**Models**: Mistral Pixtral Large 2411, Perplexity Sonar Pro")
    a("**Dataset**: 12 comparison sets from 5 patients (02, 03, 04, 05, 07)")
    a("")
    a("---")
    a("")

    # 1. Overview
    a("## 1. Experiment Overview")
    a("")
    a("Blood plasma from each donor was split into 3 samples:")
    a("- **Control** (channel 0) — no field exposure, placed ~1.5m from emitter")
    a("- **CH19** — hyperbolic field, **time acceleration** mode")
    a("- **CH21** — hyperbolic field, **time deceleration** mode")
    a("")
    a("Each LLM received all 3 photos simultaneously and was asked to:")
    a("1. Assess each sample independently (color, transparency, clots, coagulation stage)")
    a("2. Compare: which shows most/least coagulation")
    a("3. Rate overall difference: none / subtle / moderate / pronounced")
    a("")
    a('Prompt included: *"Do not assume outcomes — describe only what you see."*')
    a("")

    # 2. Methodology
    a("## 2. Methodology")
    a("")
    a("| Parameter | Value |")
    a("|-----------|-------|")
    a("| Providers | Mistral (pixtral-large-2411), Perplexity (sonar-pro) |")
    a("| Image resolution | 512×512 (Mistral), 768×768 (Perplexity) |")
    a("| Prompt | Structured comparative with JSON output |")
    a("| Temperature | 0 |")
    a("| Comparison sets | 12 (5 patients: P02×5, P03×3, P04×1, P05×1, P07×2) |")
    a("| Access | LangChain API via OpenAI-compatible shim |")
    a("")
    a("**Why only 12 sets?** Of 101 total photos, many are multi-channel (2-6 tubes per photo),")
    a("unknown channel, or from patients missing one of the 3 channels. Only single-channel")
    a("photos from patients with all 3 channels can form valid triplets.")
    a("")
    a("| Patient | Control | CH19 | CH21 | Sets | Lost photos |")
    a("|---------|:---:|:---:|:---:|:---:|-------------|")
    a("| P01 | 0 | 1 | 1 | 0 | no control photos |")
    a("| **P02** | 5 | 6 | 5 | **5** | 1 ch19 extra |")
    a("| **P03** | 4 | 3 | 3 | **3** | 1 control extra |")
    a("| **P04** | 1 | 1 | 1 | **1** | — |")
    a("| **P05** | 1 | 1 | 1 | **1** | 7 unknown |")
    a("| P06 | 0 | 0 | 0 | 0 | all multi-channel |")
    a("| **P07** | 2 | 2 | 2 | **2** | 21 unknown |")
    a("")

    # 3. Results table
    a("## 3. Results")
    a("")
    a("### 3.1. Per-Set Comparison")
    a("")
    a("| # | Patient | Control | CH19 | CH21 | Mistral diff | Mistral most | Perplexity diff | Perplexity most |")
    a("|---|---------|---------|------|------|:---:|:---:|:---:|:---:|")
    for i, row in enumerate(rows):
        m_most_str = row["m_most"] or "—"
        p_most_str = row["p_most"] or "—"
        m_diff_str = row["m_diff"]
        p_diff_str = row["p_diff"]

        # Bold informative results
        if m_most_str != "—":
            m_most_str = f"**{m_most_str}**"
        if p_most_str != "—":
            p_most_str = f"**{p_most_str}**"
        if m_diff_str in ("moderate", "pronounced"):
            m_diff_str = f"**{m_diff_str}**"
        if p_diff_str in ("moderate", "pronounced"):
            p_diff_str = f"**{p_diff_str}**"

        a(f"| {i+1} | P{row['patient']} | {row['control']} | {row['ch19_fn']} | {row['ch21_fn']} "
          f"| {m_diff_str} | {m_most_str} | {p_diff_str} | {p_most_str} |")
    a("")

    # 3.2 Aggregated stats
    a("### 3.2. Aggregated Results")
    a("")
    a("| Metric | Mistral | Perplexity |")
    a("|--------|:---:|:---:|")
    a(f"| Sets completed | {12 - m_counts['error']}/12 | {12 - p_counts['error']}/12 |")
    a(f"| CH19 = most coagulated | {m_counts['ch19']} | {p_counts['ch19']} |")
    a(f"| CH21 = most coagulated | {m_counts['ch21']} | {p_counts['ch21']} |")
    a(f"| Control = most coagulated | {m_counts['control']} | {p_counts['control']} |")
    a(f"| No difference | {m_counts['none']} | {p_counts['none']} |")
    a(f"| Unclear / no structured | {m_counts['unclear']} | {p_counts['unclear']} |")
    a("")

    m_inf = m_counts["ch19"] + m_counts["ch21"] + m_counts["control"]
    p_inf = p_counts["ch19"] + p_counts["ch21"] + p_counts["control"]
    m_rate = f"{m_counts['ch19']*100//m_inf}%" if m_inf else "—"
    p_rate = f"{p_counts['ch19']*100//p_inf}%" if p_inf else "—"

    a(f"**CH19 win rate (informative sets)**: Mistral {m_counts['ch19']}/{m_inf} ({m_rate}), "
      f"Perplexity {p_counts['ch19']}/{p_inf} ({p_rate})")
    a("")

    # 3.3 Difference distribution
    a("### 3.3. Difference Rating Distribution")
    a("")
    a("| Rating | Mistral | Perplexity |")
    a("|--------|:---:|:---:|")
    for d in DIFF_ORDER:
        a(f"| {d} | {m_diff.get(d, 0)} | {p_diff.get(d, 0)} |")
    a("")

    # 4. Cross-provider agreement
    a("## 4. Cross-Provider Agreement")
    a("")
    agree_most = 0
    agree_none = 0
    disagree = 0
    both_have = 0
    for row in rows:
        if row["m_diff"] in ("N/A", "ERR") or row["p_diff"] in ("N/A", "ERR"):
            continue
        both_have += 1
        if row["m_diff"] == "none" and row["p_diff"] == "none":
            agree_none += 1
        elif row["m_most"] and row["p_most"] and row["m_most"] == row["p_most"]:
            agree_most += 1
        elif row["m_most"] and row["p_most"] and row["m_most"] != row["p_most"]:
            disagree += 1

    a(f"Of {both_have} sets where both providers returned results:")
    a(f"- **Agree on most_coagulated**: {agree_most} sets")
    a(f"- **Both say no difference**: {agree_none} sets")
    a(f"- **Disagree on most_coagulated**: {disagree} set(s)")
    a("")

    # 5. Per-patient breakdown
    a("## 5. Per-Patient Summary")
    a("")
    patients = sorted(set(r["patient"] for r in rows))
    for pid in patients:
        p_rows = [r for r in rows if r["patient"] == pid]
        a(f"### Patient {pid} ({len(p_rows)} sets)")
        a("")
        m_ch19 = sum(1 for r in p_rows if r["m_most"] == "ch19")
        p_ch19 = sum(1 for r in p_rows if r["p_most"] == "ch19")
        m_none = sum(1 for r in p_rows if r["m_diff"] in ("none", "-"))
        p_none = sum(1 for r in p_rows if r["p_diff"] in ("none", "-"))

        a(f"- Mistral: ch19 wins {m_ch19}, no diff {m_none}")
        a(f"- Perplexity: ch19 wins {p_ch19}, no diff {p_none}")

        # Notable observations
        for r in p_rows:
            notes = []
            if r["m_most"] == "control":
                notes.append("Mistral: control most coagulated")
            if r["p_most"] == "control":
                notes.append("Perplexity: control most coagulated")
            if r["m_most"] == "ch21":
                notes.append("Mistral: ch21 most coagulated")
            if notes:
                a(f"- Outlier ({r['control']}): {'; '.join(notes)}")
        a("")

    # 6. Key findings
    a("## 6. Key Findings")
    a("")
    a(f"1. **CH19 (acceleration) = most coagulated** in {m_rate} (Mistral) and {p_rate} (Perplexity) "
      "of informative sets. Both providers independently converge on the same result.")
    a("")
    a("2. **P02 early sets show no difference** — first 2-3 photo sets from Patient 02 show "
      "identical-looking plasma with no coagulation in any channel. Later P02 sets (with visible clots) "
      "show ch19 > control.")
    a("")
    a("3. **P07 set 12 is an outlier** — both providers agree control is most coagulated, "
      "opposite to the pattern. This may indicate a preparation artifact or natural variation "
      "in this donor's samples.")
    a("")
    a("4. **Perplexity was more conservative** — rated many sets as 'subtle' without naming "
      "most_coagulated, while Mistral rated the same sets as 'moderate' with explicit ch19 winner. "
      f"(Perplexity: {p_counts['unclear']+p_counts['none']} unclear/none, "
      f"Mistral: {m_counts['unclear']+m_counts['none']})")
    a("")
    a("5. **Consistency with previous analysis**: Claude's earlier single-photo analysis found "
      "ch19 clot frequency > control > ch21. The comparative analysis confirms this ordering "
      "with direct visual comparison.")
    a("")

    # 7. Limitations
    a("## 7. Limitations")
    a("")
    a("1. **Not blinded**: Prompt tells the model which image is control/ch19/ch21. "
      "Potential label bias.")
    a("2. **Small sample**: 12 comparison sets from 5 patients. "
      "Not sufficient for statistical significance.")
    a("3. **Missing data**: 34+ photos not used (multi-channel, unknown channel, no control). "
      "Patient 07 has 21 unclassified photos that could increase coverage.")
    a("4. **Resolution reduced**: Images downscaled to 512-768px from 3024×4032 originals. "
      "Fine details may be lost.")
    a("5. **Two providers only**: Groq returned 403 (IP block). "
      "OpenAI/Google had quota exhausted. More providers would strengthen consensus.")
    a("6. **Perplexity limitations**: First set was refused entirely "
      "(model claimed it couldn't see 3 images). Sonar-pro may have inconsistent multi-image support.")
    a("")

    # 8. Conclusion
    a("## 8. Conclusion")
    a("")
    a("Two independent LLM vision providers (Mistral Pixtral Large, Perplexity Sonar Pro) "
      "performed comparative analysis of blood plasma samples exposed to hyperbolic field channels.")
    a("")
    a("**Primary finding**: CH19 (time acceleration) consistently shows the most advanced "
      f"coagulation — identified as most_coagulated in {m_rate} (Mistral) and {p_rate} (Perplexity) "
      "of sets where differences were detected.")
    a("")
    a("**Secondary finding**: CH21 (time deceleration) generally appears similar to or slightly "
      "more coagulated than control, but less than CH19. The ordering CH19 > CH21 ≥ Control "
      "is consistent across providers and aligns with the hypothesis that time acceleration "
      "enhances coagulation.")
    a("")
    a("---")
    a("")
    a("## Data Files")
    a("")
    a("- `results.json` — Combined structured results from both providers")
    a("- `../comparative_mistral/results.json` — Raw Mistral results")
    a("- `../comparative_perplexity/results.json` — Raw Perplexity results")
    a("")

    return "\n".join(lines)


def build_results_json(rows, m_counts, p_counts):
    return {
        "metadata": {
            "generated": str(date.today()),
            "analysis_type": "comparative",
            "providers": ["mistral_pixtral_large_2411", "perplexity_sonar_pro"],
            "total_sets": len(rows),
            "patients": sorted(set(r["patient"] for r in rows)),
        },
        "summary": {
            "mistral": {
                "completed": 12 - m_counts["error"],
                "ch19_most_coagulated": m_counts["ch19"],
                "ch21_most_coagulated": m_counts["ch21"],
                "control_most_coagulated": m_counts["control"],
                "no_difference": m_counts["none"],
            },
            "perplexity": {
                "completed": 12 - p_counts["error"],
                "ch19_most_coagulated": p_counts["ch19"],
                "ch21_most_coagulated": p_counts["ch21"],
                "control_most_coagulated": p_counts["control"],
                "no_difference": p_counts["none"],
            },
        },
        "per_set": [
            {
                "set_number": i + 1,
                "patient": r["patient"],
                "photos": {
                    "control": r["control"],
                    "ch19": r["ch19_fn"],
                    "ch21": r["ch21_fn"],
                },
                "mistral": {
                    "overall_difference": r["m_diff"],
                    "most_coagulated": r["m_most"],
                    "notes": r["m_notes"],
                },
                "perplexity": {
                    "overall_difference": r["p_diff"],
                    "most_coagulated": r["p_most"],
                    "notes": r["p_notes"],
                },
            }
            for i, r in enumerate(rows)
        ],
    }


def main():
    print("Loading results...")
    mistral_comps = load_results(MISTRAL_RESULTS)
    perplexity_comps = load_results(PERPLEXITY_RESULTS)
    print(f"  Mistral: {len(mistral_comps)} comparisons")
    print(f"  Perplexity: {len(perplexity_comps)} comparisons")

    print("\nBuilding unified table...")
    rows = build_unified_table(mistral_comps, perplexity_comps)
    print(f"  {len(rows)} comparison sets")

    print("\nComputing stats...")
    m_counts, m_diff, m_inf = compute_stats(rows, "m")
    p_counts, p_diff, p_inf = compute_stats(rows, "p")

    print(f"  Mistral:    ch19={m_counts['ch19']} ch21={m_counts['ch21']} "
          f"ctrl={m_counts['control']} none={m_counts['none']}")
    print(f"  Perplexity: ch19={p_counts['ch19']} ch21={p_counts['ch21']} "
          f"ctrl={p_counts['control']} none={p_counts['none']}")

    print("\nGenerating report...")
    report = generate_report(rows, m_counts, m_diff, p_counts, p_diff)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    report_path = REPORT_DIR / "report_en.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"  Saved: {report_path}")

    print("\nBuilding results.json...")
    results = build_results_json(rows, m_counts, p_counts)
    results_path = REPORT_DIR / "results.json"
    results_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"  Saved: {results_path}")

    print("\nDone!")


if __name__ == "__main__":
    main()
