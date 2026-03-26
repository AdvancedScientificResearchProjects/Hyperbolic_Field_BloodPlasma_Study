#!/usr/bin/env python3
"""Generate charts for the comparative LLM analysis report v3.0 (5 providers)."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHART_DIR = PROJECT_ROOT / "reports" / "2026-03-12_comparative-llm-analysis" / "charts"
CHART_DIR.mkdir(parents=True, exist_ok=True)

# Colors
C_CTRL = "#4CAF50"   # green
C_CH19 = "#F44336"   # red
C_CH21 = "#2196F3"   # blue
C_NULL = "#9E9E9E"   # grey
COLORS_3CH = [C_CTRL, C_CH19, C_CH21]

# Provider colors
PROVIDER_COLORS = {
    "Gemini": "#4285F4",
    "Groq": "#FF6F00",
    "Mistral": "#7C4DFF",
    "GPT-5": "#10A37F",
    "Perplexity": "#20808D",
}


def _classify_winner(mc_str):
    """Classify most_coagulated string to ch19/ch21/control/null."""
    if not mc_str:
        return "null"
    mc = mc_str.lower()
    if "ch19" in mc or mc in ("b", "sample_b"):
        return "ch19"
    if "ch21" in mc or mc in ("c", "sample_c"):
        return "ch21"
    if "control" in mc or mc in ("a", "sample_a"):
        return "control"
    return "null"


def load_provider_results(provider_key, result_path):
    """Load structured results for a given provider from a results.json file."""
    fpath = PROJECT_ROOT / result_path
    if not fpath.exists():
        return []
    d = json.load(open(fpath))
    records = []
    for comp in d["comparisons"]:
        prov = comp["providers"].get(provider_key, {})
        if prov.get("error"):
            continue
        s = prov.get("structured") or {}
        records.append({
            "patient": comp["patient"],
            "structured": s,
        })
    return records


def load_all_mistral():
    """Load all Mistral structured results across 4 experiments."""
    files = {
        "Comparative\n(unblinded)": ("results/comparative_mistral/results.json", "mistral"),
        "Comparative\n(blinded)": ("results/comparative_blinded/results.json", "mistral"),
        "Multi-tube\n(unblinded)": ("results/multi_tube/results.json", "mistral"),
        "Multi-tube\n(blinded)": ("results/multi_tube_blinded/results.json", "mistral"),
    }
    all_data = {}
    for label, (path, prov_key) in files.items():
        all_data[label] = load_provider_results(prov_key, path)
    return all_data


def load_cross_provider_comparative():
    """Load comparative ch19 win data for all providers."""
    configs = {
        "Gemini": {
            "unblinded": ("results/comparative_google_25flash/results.json", "google"),
            "blinded": ("results/comparative_blinded_google_25flashlite/results.json", "google"),
        },
        "Groq": {
            "unblinded": ("results/comparative_groq/results.json", "groq"),
            "blinded": ("results/comparative_blinded_groq/results.json", "groq"),
        },
        "Mistral": {
            "unblinded": ("results/comparative_mistral/results.json", "mistral"),
            "blinded": ("results/comparative_blinded/results.json", "mistral"),
        },
        "GPT-5": {
            "unblinded": ("results/comparative_openai/results.json", "openai"),
            "blinded": ("results/comparative_blinded_openai/results.json", "openai"),
        },
        "Perplexity": {
            "blinded": ("results/comparative_blinded/results.json", "perplexity"),
        },
    }
    data = {}
    for name, modes in configs.items():
        data[name] = {}
        for mode, (path, key) in modes.items():
            data[name][mode] = load_provider_results(key, path)
    return data


def chart_ch19_winrate_cross_provider(cp_data):
    """Bar chart: ch19 win rate across providers, unblinded vs blinded."""
    providers = ["Gemini", "Groq", "Mistral", "GPT-5", "Perplexity"]
    fig, ax = plt.subplots(figsize=(10, 5.5))

    x = np.arange(len(providers))
    w = 0.35

    unblinded_rates = []
    blinded_rates = []

    for prov in providers:
        # Unblinded
        recs = cp_data[prov].get("unblinded", [])
        if recs:
            ch19 = sum(1 for r in recs if _classify_winner(r["structured"].get("most_coagulated")) == "ch19")
            unblinded_rates.append(ch19 / len(recs) * 100)
        else:
            unblinded_rates.append(0)

        # Blinded
        recs = cp_data[prov].get("blinded", [])
        if recs:
            ch19 = sum(1 for r in recs if _classify_winner(r["structured"].get("most_coagulated")) == "ch19")
            blinded_rates.append(ch19 / len(recs) * 100)
        else:
            blinded_rates.append(0)

    colors = [PROVIDER_COLORS[p] for p in providers]

    bars1 = ax.bar(x - w/2, unblinded_rates, w, label="Unblinded",
                   color=colors, edgecolor="white", linewidth=1)
    bars2 = ax.bar(x + w/2, blinded_rates, w, label="Blinded",
                   color=colors, alpha=0.5, edgecolor="white", linewidth=1,
                   hatch="//")

    # Chance line
    ax.axhline(y=33.3, color="#999", linestyle="--", linewidth=1, label="Chance (33.3%)")

    # Value labels
    for bar, val in zip(bars1, unblinded_rates):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width()/2, val + 1.5,
                    f"{val:.0f}%", ha="center", va="bottom", fontsize=9, fontweight="bold")
    for bar, val in zip(bars2, blinded_rates):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width()/2, val + 1.5,
                    f"{val:.0f}%", ha="center", va="bottom", fontsize=9)

    ax.set_ylabel("CH19 identified as most coagulated (%)", fontsize=11)
    ax.set_title("CH19 Win Rate: Unblinded vs Blinded (Comparative Mode)", fontsize=13)
    ax.set_xticks(x)
    ax.set_xticklabels(providers, fontsize=11)
    ax.legend(fontsize=9)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.set_ylim(0, 85)

    fig.tight_layout()
    fig.savefig(CHART_DIR / "chart_ch19_winrate.png", dpi=150)
    plt.close(fig)
    print("  chart_ch19_winrate.png")


def chart_blinding_effect(cp_data):
    """Show blinding effect: what happens when labels are removed."""
    providers = ["Mistral", "Gemini", "GPT-5", "Groq"]
    fig, ax = plt.subplots(figsize=(10, 5.5))

    x = np.arange(len(providers))
    w = 0.25

    for cat_idx, (cat, color, label) in enumerate([
        ("ch19", C_CH19, "CH19"),
        ("ch21", C_CH21, "CH21"),
        ("control", C_CTRL, "Control"),
    ]):
        vals = []
        for prov in providers:
            recs = cp_data[prov].get("blinded", [])
            if recs:
                count = sum(1 for r in recs
                           if _classify_winner(r["structured"].get("most_coagulated")) == cat)
                vals.append(count / len(recs) * 100)
            else:
                vals.append(0)

        bars = ax.bar(x + (cat_idx - 1) * w, vals, w, label=label, color=color,
                      edgecolor="white", linewidth=1)
        for bar, val in zip(bars, vals):
            if val > 5:
                ax.text(bar.get_x() + bar.get_width()/2, val + 1,
                        f"{val:.0f}%", ha="center", va="bottom", fontsize=8)

    ax.axhline(y=33.3, color="#999", linestyle="--", linewidth=1, label="Chance (33.3%)")

    ax.set_ylabel("% identified as most coagulated", fontsize=11)
    ax.set_title("Blinded Comparative: Which Channel Wins? (labels removed)", fontsize=13)
    ax.set_xticks(x)
    ax.set_xticklabels(providers, fontsize=11)
    ax.legend(fontsize=9)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.set_ylim(0, 60)

    # Annotations
    ax.annotate("ch19 leads\n(stable)", xy=(0, 47), fontsize=8, ha="center",
                color=PROVIDER_COLORS["Mistral"], fontweight="bold")
    ax.annotate("ch19 leads\n(stable)", xy=(1, 50), fontsize=8, ha="center",
                color=PROVIDER_COLORS["Gemini"], fontweight="bold")
    ax.annotate("ch21 flips!\n(label-sensitive)", xy=(2, 40), fontsize=8, ha="center",
                color="#E53935", fontweight="bold")
    ax.annotate("ch21 flips!\n(label-sensitive)", xy=(3, 45), fontsize=8, ha="center",
                color="#E53935", fontweight="bold")

    fig.tight_layout()
    fig.savefig(CHART_DIR / "chart_blinded_vs_unblinded.png", dpi=150)
    plt.close(fig)
    print("  chart_blinded_vs_unblinded.png")


def chart_difference_rating_cross(cp_data):
    """Cross-provider overall_difference distribution."""
    providers = ["Gemini", "Groq", "GPT-5", "Mistral", "Perplexity"]
    ratings = ["none", "subtle", "moderate", "pronounced"]
    rating_colors = ["#E0E0E0", "#FFF9C4", "#FFB74D", "#E53935"]

    # Collect all results per provider (all modes)
    all_configs = {
        "Gemini": [
            ("results/comparative_google_25flash/results.json", "google"),
            ("results/comparative_blinded_google_25flashlite/results.json", "google"),
        ],
        "Groq": [
            ("results/comparative_groq/results.json", "groq"),
            ("results/comparative_blinded_groq/results.json", "groq"),
            ("results/multi_tube_groq/results.json", "groq"),
            ("results/multi_tube_blinded_groq/results.json", "groq"),
        ],
        "GPT-5": [
            ("results/comparative_openai/results.json", "openai"),
            ("results/comparative_blinded_openai/results.json", "openai"),
            ("results/multi_tube_openai/results.json", "openai"),
            ("results/multi_tube_blinded_openai/results.json", "openai"),
        ],
        "Mistral": [
            ("results/comparative_mistral/results.json", "mistral"),
            ("results/comparative_blinded/results.json", "mistral"),
            ("results/multi_tube/results.json", "mistral"),
            ("results/multi_tube_blinded/results.json", "mistral"),
        ],
        "Perplexity": [
            ("results/comparative_blinded/results.json", "perplexity"),
            ("results/multi_tube/results.json", "perplexity"),
            ("results/multi_tube_blinded/results.json", "perplexity"),
        ],
    }

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(providers))

    bottom = np.zeros(len(providers))
    for rating, color in zip(ratings, rating_colors):
        vals = []
        for prov in providers:
            all_recs = []
            for path, key in all_configs[prov]:
                all_recs.extend(load_provider_results(key, path))
            total = len(all_recs) or 1
            count = sum(1 for r in all_recs
                       if (r["structured"].get("overall_difference") or "").lower() == rating)
            vals.append(count / total * 100)

        bars = ax.bar(x, vals, 0.6, bottom=bottom, label=rating.capitalize(),
                      color=color, edgecolor="#666", linewidth=0.5)
        for bar, val, bot in zip(bars, vals, bottom):
            if val > 6:
                ax.text(bar.get_x() + bar.get_width()/2, bot + val/2,
                        f"{val:.0f}%", ha="center", va="center", fontsize=8)
        bottom += vals

    ax.set_ylabel("% of evaluations", fontsize=11)
    ax.set_title("Overall Difference Rating by Provider (all experiments)", fontsize=13)
    ax.set_xticks(x)
    ax.set_xticklabels(providers, fontsize=11)
    ax.legend(fontsize=9, loc="upper right")
    ax.set_ylim(0, 110)

    fig.tight_layout()
    fig.savefig(CHART_DIR / "chart_difference_rating.png", dpi=150)
    plt.close(fig)
    print("  chart_difference_rating.png")


def chart_clot_detection(all_data):
    """Grouped bar: clot detection rate per channel across experiments."""
    fig, ax = plt.subplots(figsize=(8, 5))

    labels = list(all_data.keys())
    channels = ["control", "ch19", "ch21"]
    rates = {ch: [] for ch in channels}

    for label, records in all_data.items():
        total = len(records)
        for ch in channels:
            clots = sum(1 for r in records
                        if isinstance(r["structured"].get(ch), dict)
                        and r["structured"][ch].get("clots") is True)
            rates[ch].append(clots / total * 100 if total else 0)

    x = np.arange(len(labels))
    w = 0.25

    for i, (ch, color) in enumerate(zip(channels, COLORS_3CH)):
        display = {"control": "Control", "ch19": "CH19", "ch21": "CH21"}[ch]
        bars = ax.bar(x + (i-1)*w, rates[ch], w, label=display, color=color)
        for bar, val in zip(bars, rates[ch]):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                        f"{val:.0f}%", ha="center", va="bottom", fontsize=7)

    ax.set_ylabel("Clot detection rate (%)")
    ax.set_title("Clot Detection Rate by Channel and Experiment (Mistral)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.legend()
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.set_ylim(0, 85)

    fig.tight_layout()
    fig.savefig(CHART_DIR / "chart_clot_detection.png", dpi=150)
    plt.close(fig)
    print("  chart_clot_detection.png")


def chart_stage_distribution(all_data):
    """Stacked bar: clot stage per channel (aggregated across all experiments)."""
    stages = ["none", "early_fibrin", "partial_clot", "full_coagulation"]
    stage_colors = ["#E0E0E0", "#FFE082", "#FF8A65", "#E53935"]
    channels = ["Control", "CH19", "CH21"]
    ch_keys = ["control", "ch19", "ch21"]

    counts = {ch: {s: 0 for s in stages} for ch in ch_keys}
    totals = {ch: 0 for ch in ch_keys}

    for records in all_data.values():
        for r in records:
            for ch in ch_keys:
                ch_data = r["structured"].get(ch)
                if not isinstance(ch_data, dict):
                    continue
                totals[ch] += 1
                stage = ch_data.get("clot_stage", "none") or "none"
                stage = stage.strip().lower().replace(" ", "_").replace("-", "_")
                if stage not in stages:
                    stage = "none"
                counts[ch][stage] += 1

    fig, ax = plt.subplots(figsize=(6, 5))
    x = np.arange(len(channels))

    bottom = np.zeros(len(channels))
    for stage, color in zip(stages, stage_colors):
        vals = [counts[ch][stage] / totals[ch] * 100 if totals[ch] else 0 for ch in ch_keys]
        bars = ax.bar(x, vals, 0.5, bottom=bottom, label=stage.replace("_", " "), color=color)
        for bar, val, bot in zip(bars, vals, bottom):
            if val > 5:
                ax.text(bar.get_x() + bar.get_width()/2, bot + val/2,
                        f"{val:.0f}%", ha="center", va="center", fontsize=8)
        bottom += vals

    ax.set_ylabel("% of observations")
    ax.set_title("Clot Stage Distribution by Channel\n(Mistral, all experiments, n=74 per channel)")
    ax.set_xticks(x)
    ax.set_xticklabels(channels)
    ax.legend(loc="upper right")
    ax.set_ylim(0, 105)

    fig.tight_layout()
    fig.savefig(CHART_DIR / "chart_stage_distribution.png", dpi=150)
    plt.close(fig)
    print("  chart_stage_distribution.png")


def chart_per_patient(all_data):
    """Horizontal bar chart: ch19 win rate per patient."""
    patient_stats = {}
    for records in all_data.values():
        for r in records:
            p = r["patient"]
            if p not in patient_stats:
                patient_stats[p] = {"ch19": 0, "ch21": 0, "control": 0, "null": 0, "total": 0}
            patient_stats[p]["total"] += 1
            mc = _classify_winner(r["structured"].get("most_coagulated", ""))
            patient_stats[p][mc] += 1

    patients = sorted(patient_stats.keys())
    fig, ax = plt.subplots(figsize=(8, 4))

    y = np.arange(len(patients))
    cats = ["ch19", "ch21", "control", "null"]
    cat_colors = [C_CH19, C_CH21, C_CTRL, C_NULL]
    cat_labels = ["CH19", "CH21", "Control", "No winner"]

    left = np.zeros(len(patients))
    for cat, color, label in zip(cats, cat_colors, cat_labels):
        vals = [patient_stats[p][cat] for p in patients]
        ax.barh(y, vals, left=left, height=0.6, label=label, color=color)
        left += vals

    ax.set_yticks(y)
    ax.set_yticklabels([f"P{p} (n={patient_stats[p]['total']})" for p in patients])
    ax.set_xlabel("Number of sets")
    ax.set_title("\"Most Coagulated\" by Patient (Mistral, all experiments)")
    ax.legend(loc="lower right", fontsize=8)
    ax.invert_yaxis()

    fig.tight_layout()
    fig.savefig(CHART_DIR / "chart_per_patient.png", dpi=150)
    plt.close(fig)
    print("  chart_per_patient.png")


if __name__ == "__main__":
    print("Loading data...")
    all_mistral = load_all_mistral()
    for label, records in all_mistral.items():
        print(f"  {label}: {len(records)} sets")

    cp_data = load_cross_provider_comparative()
    for name, modes in cp_data.items():
        for mode, recs in modes.items():
            print(f"  {name} ({mode}): {len(recs)} sets")

    print("\nGenerating charts...")
    chart_ch19_winrate_cross_provider(cp_data)
    chart_blinding_effect(cp_data)
    chart_difference_rating_cross(cp_data)
    chart_clot_detection(all_mistral)
    chart_stage_distribution(all_mistral)
    chart_per_patient(all_mistral)
    print(f"\nAll charts saved to {CHART_DIR}")
