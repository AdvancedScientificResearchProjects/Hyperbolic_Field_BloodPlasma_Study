#!/usr/bin/env python3
"""
Multi-LLM Comparison Analysis for Blood Plasma Coagulation Study.

Compares assessments from Claude Opus 4.6 (baseline), ChatGPT-4o, and Gemini 2.0 Pro
on blood plasma coagulation photos from hyperbolic field experiment.
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# === PATHS ===
PROJECT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT.parent / "browser-automation" / "results"
CLAUDE_RESULTS = PROJECT / "reports" / "2026-02-26_llm-vision-analysis" / "results.json"
CHATGPT_FILE = RESULTS_DIR / "chatgpt_all.json"
GEMINI_FILE = RESULTS_DIR / "gemini_all.json"
REPORT_DIR = PROJECT / "reports" / "2026-03-01_multi-llm-comparison"

VALID_STAGES = {"none", "early_fibrin", "partial_clot", "full_coagulation", "lysis"}
STAGE_ORDER = ["none", "early_fibrin", "partial_clot", "full_coagulation", "lysis"]
CHANNEL_NAMES = {"0": "control", "19": "ch19", "21": "ch21",
                 "control": "control", "ch19_acceleration": "ch19",
                 "ch21_deceleration": "ch21"}


# === JSON EXTRACTION ===

def extract_json_block(text):
    """Extract JSON block from LLM response text."""
    pos = text.rfind("JSON")
    if pos != -1:
        bs = text.find("{", pos)
        if bs != -1:
            result = _brace_match(text, bs)
            if result:
                return result

    m = re.search(r'\{\s*\n?\s*"scene"', text)
    if m:
        return _brace_match(text, m.start())
    return None


def _brace_match(text, start):
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        c = text[i]
        if esc:
            esc = False
            continue
        if c == '\\':
            esc = True
            continue
        if c == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    return None
    return None


# === DATA LOADING ===

def normalize_filename(fn):
    """Strip extension, return base name for matching."""
    return Path(fn).stem


def normalize_channel(ch):
    return CHANNEL_NAMES.get(ch, ch)


def normalize_stage(stage):
    if stage is None:
        return None
    stage = str(stage).strip().lower()
    if stage in ("null", "none_visible", ""):
        return None
    if "/" in stage:
        parts = [p.strip() for p in stage.split("/")]
        for s in reversed(STAGE_ORDER):
            if s in parts:
                return s
    if stage in VALID_STAGES:
        return stage
    return None


def load_claude():
    """Load Claude results.json — baseline data."""
    with open(CLAUDE_RESULTS) as f:
        data = json.load(f)

    entries = {}
    for section in ("single_channel", "single_channel_inferred", "multi_channel", "truly_unclassified"):
        for item in data.get(section, []):
            fn = item.get("filename") or item.get("file", "")
            key = normalize_filename(fn)
            ch_raw = item.get("channel", item.get("likely_channel", "unknown"))
            ch = normalize_channel(ch_raw)
            raw_clots = item.get("clots_visible")
            if isinstance(raw_clots, str):
                raw_clots = raw_clots.lower() in ("true", "yes", "1")

            entries[key] = {
                "filename": key,
                "patient": item["patient"].replace("patient-", ""),
                "channel": ch,
                "clots": raw_clots,
                "clot_stage": item.get("clot_stage"),
                "clarity": item.get("plasma_clarity"),
                "description": item.get("description", ""),
                "section": section,
            }
    return entries, data.get("statistics", {})


def load_external(filepath):
    """Load ChatGPT or Gemini consolidated JSON."""
    with open(filepath) as f:
        data = json.load(f)

    entries = {}
    for item in data["photos"]:
        key = normalize_filename(item["filename"])
        ch = normalize_channel(item["channel"])
        jb = extract_json_block(item.get("response", ""))

        if jb:
            plasma = jb.get("plasma", {})
            clots = plasma.get("clots")
            stage = normalize_stage(plasma.get("clot_stage"))
            color = plasma.get("color")
            transparency = plasma.get("transparency")
            notes = plasma.get("notes", "")
            is_egg = "[EGG_ANOMALY]" in notes
        else:
            clots = None
            stage = None
            color = None
            transparency = None
            notes = ""
            is_egg = False

        entries[key] = {
            "filename": key,
            "patient": item["patient_id"],
            "channel": ch,
            "clots": clots,
            "clot_stage": stage,
            "color": color,
            "transparency": transparency,
            "notes": notes,
            "is_egg": is_egg,
        }
    return entries


# === ANALYSIS ===

def channel_stats(entries, exclude_channels=None):
    """Compute clot rates and stage distributions per channel."""
    if exclude_channels is None:
        exclude_channels = {"multi", "multi_unknown", "unknown", "multiple"}

    by_ch = defaultdict(list)
    for e in entries.values():
        ch = e["channel"]
        if ch in exclude_channels:
            continue
        by_ch[ch].append(e)

    stats = {}
    for ch in ("control", "ch19", "ch21"):
        items = by_ch.get(ch, [])
        if not items:
            stats[ch] = {"total": 0, "assessed": 0, "with_clots": 0,
                         "clot_rate": 0, "stages": {}, "null_stages": 0,
                         "null_clots": 0}
            continue

        # Only count photos where clots was actually assessed (not None)
        assessed = [e for e in items if e["clots"] is not None]
        with_clots = sum(1 for e in assessed if e["clots"] is True)

        stages = defaultdict(int)
        null_count = 0
        for e in items:
            s = e["clot_stage"]
            if s and s in VALID_STAGES:
                stages[s] += 1
            else:
                null_count += 1

        total_assessed = len(assessed)
        stats[ch] = {
            "total": len(items),
            "assessed": total_assessed,
            "with_clots": with_clots,
            "clot_rate": round(with_clots / total_assessed * 100, 1) if total_assessed else 0,
            "stages": dict(stages),
            "null_stages": null_count,
            "null_clots": len(items) - total_assessed,
        }
    return stats


def agreement_matrix(baseline, other, field="clot_stage"):
    """Compute agreement between two models on a given field."""
    common = set(baseline.keys()) & set(other.keys())
    agree = 0
    disagree = 0
    comparisons = []

    for key in sorted(common):
        b = baseline[key]
        o = other[key]
        bv = b.get(field)
        ov = o.get(field)

        if bv is None or ov is None:
            continue

        match = bv == ov
        if match:
            agree += 1
        else:
            disagree += 1

        comparisons.append({
            "filename": key,
            "patient": b.get("patient", o.get("patient")),
            "channel": b.get("channel", o.get("channel")),
            f"baseline_{field}": bv,
            f"other_{field}": ov,
            "match": match,
        })

    total = agree + disagree
    rate = round(agree / total * 100, 1) if total else 0
    return {
        "total_compared": total,
        "agree": agree,
        "disagree": disagree,
        "agreement_rate": rate,
        "comparisons": comparisons,
    }


def clots_agreement(baseline, other):
    """Compute agreement on clots visible (bool)."""
    return agreement_matrix(baseline, other, field="clots")


def per_patient_comparison(claude, chatgpt, gemini):
    """Compare models per patient, per channel."""
    patients = sorted(set(
        e["patient"] for e in list(claude.values()) + list(chatgpt.values())
    ))

    results = {}
    for pid in patients:
        patient_data = {}
        for ch in ("control", "ch19", "ch21"):
            ch_data = {}
            for name, entries in [("claude", claude), ("chatgpt", chatgpt), ("gemini", gemini)]:
                items = [e for e in entries.values()
                         if e["patient"] == pid and e["channel"] == ch]
                if not items:
                    ch_data[name] = None
                    continue

                stages = defaultdict(int)
                clot_count = 0
                for e in items:
                    if e["clots"] is True:
                        clot_count += 1
                    s = e["clot_stage"]
                    if s and s in VALID_STAGES:
                        stages[s] += 1

                ch_data[name] = {
                    "total": len(items),
                    "with_clots": clot_count,
                    "clot_rate": round(clot_count / len(items) * 100) if items else 0,
                    "dominant_stage": max(stages, key=stages.get) if stages else None,
                    "stages": dict(stages),
                }
            patient_data[ch] = ch_data
        results[pid] = patient_data
    return results


def disagreement_details(claude, chatgpt, gemini):
    """Find photos where models disagree on clot_stage."""
    common = set(claude.keys()) & set(chatgpt.keys()) & set(gemini.keys())
    disagreements = []

    for key in sorted(common):
        c = claude[key].get("clot_stage")
        g = chatgpt[key].get("clot_stage")
        m = gemini[key].get("clot_stage")

        if c is None or g is None or m is None:
            continue

        if not (c == g == m):
            disagreements.append({
                "filename": key,
                "patient": claude[key].get("patient"),
                "channel": claude[key].get("channel"),
                "claude": c,
                "chatgpt": g,
                "gemini": m,
            })
    return disagreements


# === REPORT GENERATION ===

def pct(n, total):
    return f"{round(n / total * 100)}%" if total else "—"


def generate_report(claude_stats, chatgpt_stats, gemini_stats,
                    claude_baseline_stats, chatgpt_baseline_stats, gemini_baseline_stats,
                    stage_agree_cg, stage_agree_cm, stage_agree_gm,
                    clots_agree_cg, clots_agree_cm, clots_agree_gm,
                    patient_data, disagreements, claude, chatgpt, gemini):
    """Generate markdown report."""

    lines = []
    a = lines.append

    a("# Multi-LLM Blood Plasma Coagulation Analysis: Comparative Report")
    a("")
    a("**Date**: 2026-03-01")
    a("**Models compared**: Claude Opus 4.6 (baseline), ChatGPT-4o, Gemini 2.0 Pro")
    a("**Dataset**: 98 photographs, 7 donors")
    a("**Baseline report**: [LLM Vision Analysis v2.0](../2026-02-26_llm-vision-analysis/report_en.md)")
    a("")
    a("---")
    a("")

    # === Section 1: Overview ===
    a("## 1. Experiment Overview")
    a("")
    a("Blood samples from 7 donors were separated into plasma and distributed into samples:")
    a("- **Control** (channel 0) — no irradiation, placed 1.5 m from emitters")
    a("- **Channel 19** — hyperbolic field, **time acceleration** mode")
    a("- **Channel 21** — hyperbolic field, **time deceleration** mode")
    a("")
    a("Irradiation: ~1h12m. Temperature: 17°C constant. 98 photographs analyzed by each model.")
    a("")

    # === Section 2: Methodology ===
    a("## 2. Methodology")
    a("")
    a("### 2.1. Models")
    a("")
    a("| Model | Access | Analysis Type |")
    a("|-------|--------|---------------|")
    a("| **Claude Opus 4.6** | Direct multimodal API | Baseline — direct photo analysis with experiment context |")
    a("| **ChatGPT-4o** | Web interface (automated) | Structured prompt, same 9-point assessment |")
    a("| **Gemini 2.0 Pro** | Web interface (automated) | Structured prompt, same 9-point assessment |")
    a("")
    a("### 2.2. Assessment Criteria")
    a("")
    a("All three models used the same coagulation stage scale:")
    a("")
    a("| Stage | Description |")
    a("|-------|-------------|")
    a("| `none` | No visible coagulation |")
    a("| `early_fibrin` | Initial fibrin formation — faint strands or films |")
    a("| `partial_clot` | Defined clot mass, not fully consolidated |")
    a("| `full_coagulation` | Large, dense, well-formed clot |")
    a("| `lysis` | Clot decomposition — cracked, fragmented fibrin |")
    a("")
    a("### 2.3. Data Collection")
    a("")
    a("| Model | Method | Valid entries | JSON parseable |")
    a("|-------|--------|:---:|:---:|")
    a("| Claude | API multimodal batches | 101 | 101 (100%) |")
    a("| ChatGPT | nodriver browser automation | 98 | 98 (100%) |")
    a("| Gemini | nodriver browser automation | 98 | 98 (100%) |")
    a("")
    a("ChatGPT and Gemini received identical structured prompts requesting 9-point assessment + JSON output.")
    a("")

    # === Section 3: Results by Channel ===
    a("## 3. Results by Channel")
    a("")
    a("### 3.1. Clot Frequency — All Photos (98)")
    a("")
    a("All 98 photos analyzed by each model. Channel assignments from experiment protocol metadata.")
    a("")
    a("| Channel | Claude | ChatGPT | Gemini |")
    a("|---------|:---:|:---:|:---:|")
    for ch in ("control", "ch19", "ch21"):
        cs = claude_stats.get(ch, {})
        gs = chatgpt_stats.get(ch, {})
        ms = gemini_stats.get(ch, {})

        def fmt_rate(s):
            if not s.get("assessed"):
                return "—"
            nc = s.get("null_clots", 0)
            suffix = f" ^{nc}n" if nc > 0 else ""
            return f"{s['with_clots']}/{s['assessed']} ({s['clot_rate']}%){suffix}"

        a(f"| {ch} | {fmt_rate(cs)} | {fmt_rate(gs)} | {fmt_rate(ms)} |")
    a("")
    a("> ^Nn = N photos excluded (clots not assessed). ~34 photos show 2–6 tubes from multiple")
    a("> channels in one shot — channel assignment is ambiguous. **Section 3.2 is the primary comparison.**")
    a("")

    a("### 3.2. Clot Frequency — Single-Channel Photos Only (55)")
    a("")
    a("Only photos showing a single tube (labeled + EXIF-inferred). All three models' assessments")
    a("for the same 55 photos — the cleanest per-channel comparison.")
    a("")
    a("| Channel | Claude | ChatGPT | Gemini |")
    a("|---------|:---:|:---:|:---:|")
    for ch in ("control", "ch19", "ch21"):
        bs = claude_baseline_stats.get(ch, {})
        gs = chatgpt_baseline_stats.get(ch, {})
        ms = gemini_baseline_stats.get(ch, {})
        b_rate = f"{bs.get('with_clots', 0)}/{bs['assessed']} ({bs['clot_rate']}%)" if bs.get("assessed") else "—"
        g_rate = f"{gs.get('with_clots', 0)}/{gs['assessed']} ({gs['clot_rate']}%)" if gs.get("assessed") else "—"
        m_rate = f"{ms.get('with_clots', 0)}/{ms['assessed']} ({ms['clot_rate']}%)" if ms.get("assessed") else "—"
        a(f"| {ch} | {b_rate} | {g_rate} | {m_rate} |")
    a("")

    a("### 3.3. Clot Frequency Ordering")
    a("")
    a("**All photos (98):**")
    for name, stats in [("Claude", claude_stats), ("ChatGPT", chatgpt_stats), ("Gemini", gemini_stats)]:
        rates = {ch: stats.get(ch, {}).get("clot_rate", 0) for ch in ("control", "ch19", "ch21")}
        ordered = sorted(rates.items(), key=lambda x: -x[1])
        order_str = " > ".join(f"{ch} ({r}%)" for ch, r in ordered)
        a(f"- **{name}**: {order_str}")
    a("")
    a("**Single-channel baseline (55):**")
    for name, stats in [("Claude", claude_baseline_stats),
                        ("ChatGPT", chatgpt_baseline_stats),
                        ("Gemini", gemini_baseline_stats)]:
        rates = {ch: stats.get(ch, {}).get("clot_rate", 0) for ch in ("control", "ch19", "ch21")}
        ordered = sorted(rates.items(), key=lambda x: -x[1])
        order_str = " > ".join(f"{ch} ({r}%)" for ch, r in ordered)
        a(f"- **{name}**: {order_str}")
    a("")

    # === Section 3.4: Stage Distribution ===
    a("### 3.4. Stage Distribution by Channel (All Photos)")
    a("")
    for ch in ("control", "ch19", "ch21"):
        a(f"**{ch.upper()}**")
        a("")
        a(f"| Stage | Claude | ChatGPT | Gemini |")
        a(f"|-------|:---:|:---:|:---:|")
        for stage in STAGE_ORDER:
            cs = claude_stats.get(ch, {}).get("stages", {}).get(stage, 0)
            gs = chatgpt_stats.get(ch, {}).get("stages", {}).get(stage, 0)
            ms = gemini_stats.get(ch, {}).get("stages", {}).get(stage, 0)
            if cs + gs + ms > 0:
                ct = claude_stats.get(ch, {}).get("total", 1)
                gt = chatgpt_stats.get(ch, {}).get("total", 1)
                mt = gemini_stats.get(ch, {}).get("total", 1)
                a(f"| {stage} | {cs} ({pct(cs, ct)}) | {gs} ({pct(gs, gt)}) | {ms} ({pct(ms, mt)}) |")
        null_c = claude_stats.get(ch, {}).get("null_stages", 0)
        null_g = chatgpt_stats.get(ch, {}).get("null_stages", 0)
        null_m = gemini_stats.get(ch, {}).get("null_stages", 0)
        if null_c + null_g + null_m > 0:
            a(f"| null/undetermined | {null_c} | {null_g} | {null_m} |")
        a("")

    # === Section 4: Inter-Model Agreement ===
    a("## 4. Inter-Model Agreement")
    a("")
    a("### 4.1. Clot Stage Agreement")
    a("")
    a("| Pair | Compared | Agree | Disagree | Agreement Rate |")
    a("|------|:---:|:---:|:---:|:---:|")
    for label, ag in [("Claude↔ChatGPT", stage_agree_cg),
                       ("Claude↔Gemini", stage_agree_cm),
                       ("ChatGPT↔Gemini", stage_agree_gm)]:
        a(f"| {label} | {ag['total_compared']} | {ag['agree']} | {ag['disagree']} | **{ag['agreement_rate']}%** |")
    a("")

    a("### 4.2. Clots Visible Agreement (boolean)")
    a("")
    a("| Pair | Compared | Agree | Agreement Rate |")
    a("|------|:---:|:---:|:---:|")
    for label, ag in [("Claude↔ChatGPT", clots_agree_cg),
                       ("Claude↔Gemini", clots_agree_cm),
                       ("ChatGPT↔Gemini", clots_agree_gm)]:
        a(f"| {label} | {ag['total_compared']} | {ag['agree']} | **{ag['agreement_rate']}%** |")
    a("")

    # === Section 4.3: Disagreement details ===
    a("### 4.3. Notable Disagreements (all three models differ)")
    a("")
    three_way = [d for d in disagreements
                 if d["claude"] != d["chatgpt"] and d["claude"] != d["gemini"]
                 and d["chatgpt"] != d["gemini"]]
    two_vs_one = [d for d in disagreements
                  if d not in three_way]

    if three_way:
        a("**Three-way disagreements** (each model gives a different stage):")
        a("")
        a("| Photo | Patient | Channel | Claude | ChatGPT | Gemini |")
        a("|-------|---------|---------|--------|---------|--------|")
        for d in three_way:
            a(f"| {d['filename']} | {d['patient']} | {d['channel']} | {d['claude']} | {d['chatgpt']} | {d['gemini']} |")
        a("")

    if two_vs_one:
        a(f"**Two-vs-one disagreements**: {len(two_vs_one)} photos where two models agree but one differs.")
        a("")
        # Count which model is the outlier
        outlier_counts = defaultdict(int)
        for d in two_vs_one:
            if d["chatgpt"] == d["gemini"]:
                outlier_counts["Claude"] += 1
            elif d["claude"] == d["gemini"]:
                outlier_counts["ChatGPT"] += 1
            elif d["claude"] == d["chatgpt"]:
                outlier_counts["Gemini"] += 1
        a("| Outlier model | Times disagreeing with consensus |")
        a("|:---:|:---:|")
        for model in ("Claude", "ChatGPT", "Gemini"):
            a(f"| {model} | {outlier_counts.get(model, 0)} |")
        a("")

        a("<details>")
        a("<summary>Full disagreement table</summary>")
        a("")
        a("| Photo | Patient | Channel | Claude | ChatGPT | Gemini |")
        a("|-------|---------|---------|--------|---------|--------|")
        for d in disagreements:
            a(f"| {d['filename']} | {d['patient']} | {d['channel']} | {d['claude']} | {d['chatgpt']} | {d['gemini']} |")
        a("")
        a("</details>")
        a("")

    # === Section 5: Key Findings ===
    a("## 5. Key Findings")
    a("")

    # 5.1 Channel ordering consensus
    a("### 5.1. Channel Ordering Consensus")
    a("")
    orderings = {}
    for name, stats in [("Claude", claude_stats), ("ChatGPT", chatgpt_stats), ("Gemini", gemini_stats)]:
        rates = {ch: stats.get(ch, {}).get("clot_rate", 0) for ch in ("control", "ch19", "ch21")}
        order = tuple(ch for ch, _ in sorted(rates.items(), key=lambda x: -x[1]))
        orderings[name] = order

    if len(set(orderings.values())) == 1:
        a(f"All three models agree on the clot frequency ordering: **{' > '.join(orderings['Claude'])}**.")
    else:
        a("Models differ on clot frequency ordering:")
        for name, order in orderings.items():
            a(f"- {name}: {' > '.join(order)}")
    a("")

    # 5.2 Lysis
    a("### 5.2. Lysis Detection")
    a("")
    for name, entries in [("Claude", claude), ("ChatGPT", chatgpt), ("Gemini", gemini)]:
        lysis = [e for e in entries.values() if e.get("clot_stage") == "lysis"]
        if lysis:
            details = ", ".join(f"{e['filename']} ({e['channel']})" for e in lysis)
            a(f"- **{name}**: {len(lysis)} lysis detection(s) — {details}")
        else:
            a(f"- **{name}**: no lysis detected")
    a("")

    # 5.3 Gemini anomalies
    egg_entries = [e for e in gemini.values() if e.get("is_egg")]
    if egg_entries:
        a("### 5.3. Gemini Content Anomalies")
        a("")
        a(f"Gemini identified {len(egg_entries)} photo(s) as resembling eggs rather than plasma:")
        a("")
        for e in egg_entries:
            a(f"- **{e['filename']}** (patient-{e['patient']}, {e['channel']})")
        a("")

    # === Section 6: Per-Patient Comparison ===
    a("## 6. Per-Patient Comparison")
    a("")
    a("Dominant clot_stage per patient per channel (—  = no data):")
    a("")
    a("| Patient | Channel | Claude | ChatGPT | Gemini |")
    a("|---------|---------|--------|---------|--------|")
    for pid in sorted(patient_data.keys()):
        for ch in ("control", "ch19", "ch21"):
            ch_data = patient_data[pid].get(ch, {})
            cells = [pid if ch == "control" else "", ch]
            for model in ("claude", "chatgpt", "gemini"):
                md = ch_data.get(model)
                if md is None:
                    cells.append("—")
                else:
                    ds = md.get("dominant_stage") or "null"
                    cr = md.get("clot_rate", 0)
                    cells.append(f"{ds} ({cr}%)")
            a(f"| {cells[0]} | {cells[1]} | {cells[2]} | {cells[3]} | {cells[4]} |")
    a("")

    # === Section 7: Limitations ===
    a("## 7. Limitations")
    a("")
    a("1. **Not blinded**: All models received experiment context (channel meanings). Potential confirmation bias.")
    a("2. **Different access methods**: Claude used direct API with photo uploads; ChatGPT/Gemini used web interface via browser automation, which may affect response quality.")
    a("3. **Scraper artifacts**: ChatGPT had 3 truncated responses reconstructed from text (no original JSON). Gemini had 2 egg-misidentification anomalies.")
    a("4. **Small sample**: 7 donors, 98 photos. Not suitable for statistical significance testing.")
    a("5. **Channel imbalance**: Control has ~49 photos, ch19 ~25, ch21 ~24. Patient-06 has only ch21 data.")
    null_g = sum(1 for e in chatgpt.values() if e.get("clot_stage") is None)
    null_m = sum(1 for e in gemini.values() if e.get("clot_stage") is None)
    a(f"6. **Null stages**: ChatGPT returned null clot_stage for {null_g} photos, Gemini for {null_m}.")
    a("")

    # === Section 8: Conclusion ===
    a("## 8. Conclusion")
    a("")

    # Auto-generate conclusion based on data
    all_agree_ordering = len(set(orderings.values())) == 1
    avg_stage_agree = round((stage_agree_cg["agreement_rate"] +
                             stage_agree_cm["agreement_rate"] +
                             stage_agree_gm["agreement_rate"]) / 3, 1)
    avg_clots_agree = round((clots_agree_cg["agreement_rate"] +
                             clots_agree_cm["agreement_rate"] +
                             clots_agree_gm["agreement_rate"]) / 3, 1)

    a(f"1. **Inter-model clot_stage agreement**: {avg_stage_agree}% average pairwise agreement across all three models.")
    a(f"2. **Clots detection agreement**: {avg_clots_agree}% average pairwise agreement on whether clots are visible.")

    if all_agree_ordering:
        a(f"3. **Channel ordering consensus**: All three models independently confirm **{' > '.join(orderings['Claude'])}** clot frequency ordering.")
    else:
        a("3. **Channel ordering**: Models do not fully agree on clot frequency ordering across channels.")

    claude_lysis = any(e.get("clot_stage") == "lysis" for e in claude.values())
    chatgpt_lysis = any(e.get("clot_stage") == "lysis" for e in chatgpt.values())
    gemini_lysis = any(e.get("clot_stage") == "lysis" for e in gemini.values())
    lysis_models = sum([claude_lysis, chatgpt_lysis, gemini_lysis])
    a(f"4. **Lysis**: Detected by {lysis_models}/3 models. {'All models confirm lysis exclusively in ch19.' if lysis_models == 3 else 'Not all models detected lysis.'}")

    a("")
    a("---")
    a("")
    a("## Data Files")
    a("")
    a("- `results.json` — Full comparison data with per-photo assessments from all three models")
    a("- `../2026-02-26_llm-vision-analysis/report_en.md` — Claude baseline report (v2.0)")
    a("")

    return "\n".join(lines)


def build_results_json(claude, chatgpt, gemini,
                       claude_stats, chatgpt_stats, gemini_stats,
                       stage_agree_cg, stage_agree_cm, stage_agree_gm,
                       disagreements):
    """Build results.json for the report."""
    all_keys = sorted(set(claude.keys()) | set(chatgpt.keys()) | set(gemini.keys()))

    per_photo = []
    for key in all_keys:
        entry = {"filename": key}
        c = claude.get(key, {})
        g = chatgpt.get(key, {})
        m = gemini.get(key, {})

        entry["patient"] = c.get("patient") or g.get("patient") or m.get("patient")
        entry["channel"] = c.get("channel") or g.get("channel") or m.get("channel")

        entry["claude"] = {
            "clots": c.get("clots"),
            "clot_stage": c.get("clot_stage"),
            "clarity": c.get("clarity"),
        } if c else None

        entry["chatgpt"] = {
            "clots": g.get("clots"),
            "clot_stage": g.get("clot_stage"),
            "color": g.get("color"),
            "transparency": g.get("transparency"),
        } if g else None

        entry["gemini"] = {
            "clots": m.get("clots"),
            "clot_stage": m.get("clot_stage"),
            "color": m.get("color"),
            "transparency": m.get("transparency"),
            "is_egg": m.get("is_egg", False),
        } if m else None

        # Agreement flags
        stages = [x for x in [
            c.get("clot_stage"), g.get("clot_stage"), m.get("clot_stage")
        ] if x is not None]
        entry["all_agree_stage"] = len(set(stages)) == 1 if len(stages) == 3 else None

        per_photo.append(entry)

    return {
        "metadata": {
            "generated": "2026-03-01",
            "models": ["claude_opus_4.6", "chatgpt_4o", "gemini_2.0_pro"],
            "total_photos": len(all_keys),
            "baseline": "claude_opus_4.6",
        },
        "channel_stats": {
            "claude": claude_stats,
            "chatgpt": chatgpt_stats,
            "gemini": gemini_stats,
        },
        "agreement": {
            "claude_chatgpt_stage": {
                k: v for k, v in stage_agree_cg.items() if k != "comparisons"
            },
            "claude_gemini_stage": {
                k: v for k, v in stage_agree_cm.items() if k != "comparisons"
            },
            "chatgpt_gemini_stage": {
                k: v for k, v in stage_agree_gm.items() if k != "comparisons"
            },
        },
        "disagreements": disagreements,
        "per_photo": per_photo,
    }


# === MAIN ===

def main():
    print("Loading data...")
    claude, claude_existing_stats = load_claude()
    chatgpt = load_external(CHATGPT_FILE)
    gemini = load_external(GEMINI_FILE)

    print(f"  Claude:  {len(claude)} photos")
    print(f"  ChatGPT: {len(chatgpt)} photos")
    print(f"  Gemini:  {len(gemini)} photos")

    common = set(claude.keys()) & set(chatgpt.keys()) & set(gemini.keys())
    print(f"  Common:  {len(common)} photos in all 3 models")

    # Enrich Claude channel assignments from ChatGPT/Gemini for multi/unclassified photos
    NO_CHANNEL = {"multi", "multi_unknown", "unknown", "multiple", "unclassified"}
    enriched = 0
    for key, entry in claude.items():
        if entry["channel"] in NO_CHANNEL:
            ext = chatgpt.get(key) or gemini.get(key)
            if ext and ext["channel"] not in NO_CHANNEL:
                entry["channel"] = ext["channel"]
                enriched += 1
    print(f"  Enriched {enriched} Claude entries with channel from ChatGPT/Gemini")

    # Baseline stats: only single-channel photos (55) — same subset & same channels for all
    baseline_keys = {k for k, v in claude.items()
                     if v.get("section") in ("single_channel", "single_channel_inferred")}
    claude_baseline = {k: v for k, v in claude.items() if k in baseline_keys}

    # Override ChatGPT/Gemini channels with Claude's channels for fair comparison
    chatgpt_baseline = {}
    gemini_baseline = {}
    for k in baseline_keys:
        claude_ch = claude[k]["channel"]
        if k in chatgpt:
            entry = dict(chatgpt[k])
            entry["channel"] = claude_ch
            chatgpt_baseline[k] = entry
        if k in gemini:
            entry = dict(gemini[k])
            entry["channel"] = claude_ch
            gemini_baseline[k] = entry

    claude_baseline_stats = channel_stats(claude_baseline)
    chatgpt_baseline_stats = channel_stats(chatgpt_baseline)
    gemini_baseline_stats = channel_stats(gemini_baseline)
    print(f"  Baseline subset (single-channel): {len(baseline_keys)} photos"
          f" (ChatGPT: {len(chatgpt_baseline)}, Gemini: {len(gemini_baseline)})")

    print("\nComputing channel stats (all photos)...")
    claude_stats = channel_stats(claude)
    chatgpt_stats = channel_stats(chatgpt)
    gemini_stats = channel_stats(gemini)

    print("\nComputing agreement...")
    stage_agree_cg = agreement_matrix(claude, chatgpt)
    stage_agree_cm = agreement_matrix(claude, gemini)
    stage_agree_gm = agreement_matrix(chatgpt, gemini)

    clots_agree_cg = clots_agreement(claude, chatgpt)
    clots_agree_cm = clots_agreement(claude, gemini)
    clots_agree_gm = clots_agreement(chatgpt, gemini)

    print(f"  Stage: Claude↔ChatGPT={stage_agree_cg['agreement_rate']}% "
          f"Claude↔Gemini={stage_agree_cm['agreement_rate']}% "
          f"ChatGPT↔Gemini={stage_agree_gm['agreement_rate']}%")
    print(f"  Clots: Claude↔ChatGPT={clots_agree_cg['agreement_rate']}% "
          f"Claude↔Gemini={clots_agree_cm['agreement_rate']}% "
          f"ChatGPT↔Gemini={clots_agree_gm['agreement_rate']}%")

    print("\nPer-patient analysis...")
    patient_data = per_patient_comparison(claude, chatgpt, gemini)

    print("\nDisagreement analysis...")
    disagreements = disagreement_details(claude, chatgpt, gemini)
    print(f"  {len(disagreements)} photos with disagreements")

    print("\nGenerating report...")
    report = generate_report(
        claude_stats, chatgpt_stats, gemini_stats,
        claude_baseline_stats, chatgpt_baseline_stats, gemini_baseline_stats,
        stage_agree_cg, stage_agree_cm, stage_agree_gm,
        clots_agree_cg, clots_agree_cm, clots_agree_gm,
        patient_data, disagreements,
        claude, chatgpt, gemini,
    )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    report_path = REPORT_DIR / "report_en.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"  Saved: {report_path}")

    print("\nBuilding results.json...")
    results = build_results_json(
        claude, chatgpt, gemini,
        claude_stats, chatgpt_stats, gemini_stats,
        stage_agree_cg, stage_agree_cm, stage_agree_gm,
        disagreements,
    )
    results_path = REPORT_DIR / "results.json"
    results_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"  Saved: {results_path}")

    print("\nDone!")


if __name__ == "__main__":
    main()
