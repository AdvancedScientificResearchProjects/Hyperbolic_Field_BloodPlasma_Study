#!/usr/bin/env python3
"""Generate charts for the CV/ML analysis report."""

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from pathlib import Path

CHARTS_DIR = Path(__file__).resolve().parent / "charts"
CHARTS_DIR.mkdir(exist_ok=True)

# Style
plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.grid": True,
    "grid.alpha": 0.3,
    "font.size": 12,
})

CHANCE = 33.3


def chart_ch19_winrate():
    """Chart 1: CH19 win rate — all CV models + LLM top models."""
    models = [
        "Gemini 2.5\n(LLM)", "DINOv2\nprobe", "Mistral\n(LLM)",
        "BiomedCLIP", "SigLIP2\nbase", "SigLIP2\nSO400M"
    ]
    rates = [57.9, 47.4, 44.4, 36.8, 31.6, 26.3]
    colors = ["#7B68EE", "#2ECC71", "#7B68EE", "#E74C3C", "#E74C3C", "#E74C3C"]
    edge_colors = ["#5B48CE", "#27AE60", "#5B48CE", "#C0392B", "#C0392B", "#C0392B"]

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(models, rates, color=colors, edgecolor=edge_colors, linewidth=1.5, width=0.6)

    # Chance baseline
    ax.axhline(y=CHANCE, color="gray", linestyle="--", linewidth=1.5, label="Chance (33.3%)")

    # Labels on bars
    for bar, rate in zip(bars, rates):
        weight = "bold" if rate > CHANCE else "normal"
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                f"{rate:.1f}%", ha="center", va="bottom", fontweight=weight, fontsize=13)

    ax.set_ylabel("CH19 identified as most coagulated (%)", fontsize=13)
    ax.set_title("CH19 Win Rate: CV Models vs LLM (19 Comparative Sets)", fontsize=15, fontweight="bold")
    ax.set_ylim(0, 72)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter())
    ax.legend(loc="upper right", fontsize=11)

    # Add p-values
    p_values = ["p=0.027", "p=0.146", "p=0.22", "p=0.46", "p=0.65", "p=0.81"]
    for bar, p in zip(bars, p_values):
        ax.text(bar.get_x() + bar.get_width() / 2, 2,
                p, ha="center", va="bottom", fontsize=9, color="white", fontweight="bold")

    plt.tight_layout()
    fig.savefig(CHARTS_DIR / "chart_ch19_winrate.png", dpi=150)
    plt.close()
    print("  chart_ch19_winrate.png")


def chart_per_patient():
    """Chart 2: Per-patient DINOv2 results."""
    patients = ["P02\n(n=5)", "P03\n(n=4)", "P04\n(n=1)", "P05\n(n=3)", "P07\n(n=6)"]
    ch19 = [3, 2, 1, 0, 3]
    ch21 = [0, 1, 0, 1, 1]
    ctrl = [2, 1, 0, 2, 2]

    x = np.arange(len(patients))
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 6))
    b1 = ax.bar(x - width, ch19, width, label="CH19", color="#E74C3C", edgecolor="#C0392B")
    b2 = ax.bar(x, ctrl, width, label="Control", color="#2ECC71", edgecolor="#27AE60")
    b3 = ax.bar(x + width, ch21, width, label="CH21", color="#3498DB", edgecolor="#2980B9")

    # Labels
    for bars in [b1, b2, b3]:
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, h + 0.05,
                        str(int(h)), ha="center", va="bottom", fontsize=11, fontweight="bold")

    ax.set_ylabel("Sets won", fontsize=13)
    ax.set_title("DINOv2 Probe: Per-Patient CH19 Win Count (Leave-Patient-Out CV)", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(patients, fontsize=12)
    ax.legend(fontsize=11)
    ax.set_ylim(0, max(max(ch19), max(ctrl), max(ch21)) + 1)

    plt.tight_layout()
    fig.savefig(CHARTS_DIR / "chart_per_patient.png", dpi=150)
    plt.close()
    print("  chart_per_patient.png")


def chart_cv_vs_llm():
    """Chart 3: All methods compared — CV and LLM on same axis."""
    methods = [
        "Gemini\n(LLM blinded)",
        "Perplexity batch\n(LLM blinded)",
        "DINOv2 probe\n(LOSO-CV)",
        "GPT-5 batch\n(LLM blinded)",
        "Mistral\n(LLM blinded)",
        "BiomedCLIP\n(zero-shot)",
        "Groq\n(LLM blinded)",
        "SigLIP2-base\n(zero-shot)",
        "SigLIP2-SO400M\n(zero-shot)",
    ]
    rates = [57.9, 53.3, 47.4, 46.7, 44.4, 36.8, 33.3, 31.6, 26.3]
    is_cv = [False, False, True, False, False, True, False, True, True]

    colors = ["#2ECC71" if cv else "#7B68EE" for cv in is_cv]
    edge_colors = ["#27AE60" if cv else "#5B48CE" for cv in is_cv]

    fig, ax = plt.subplots(figsize=(14, 6))
    bars = ax.barh(range(len(methods)), rates, color=colors, edgecolor=edge_colors, linewidth=1.5, height=0.6)

    ax.axvline(x=CHANCE, color="gray", linestyle="--", linewidth=1.5, label="Chance (33.3%)")

    for i, (bar, rate) in enumerate(zip(bars, rates)):
        weight = "bold" if rate > CHANCE else "normal"
        ax.text(rate + 0.8, bar.get_y() + bar.get_height() / 2,
                f"{rate:.1f}%", ha="left", va="center", fontweight=weight, fontsize=11)

    ax.set_yticks(range(len(methods)))
    ax.set_yticklabels(methods, fontsize=11)
    ax.set_xlabel("CH19 identified as most coagulated (%)", fontsize=13)
    ax.set_title("All Methods: CH19 Win Rate (19 Comparative Sets)", fontsize=15, fontweight="bold")
    ax.set_xlim(0, 72)
    ax.invert_yaxis()

    # Custom legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#2ECC71", edgecolor="#27AE60", label="CV model"),
        Patch(facecolor="#7B68EE", edgecolor="#5B48CE", label="LLM"),
        plt.Line2D([0], [0], color="gray", linestyle="--", label="Chance (33.3%)"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=11)

    plt.tight_layout()
    fig.savefig(CHARTS_DIR / "chart_cv_vs_llm.png", dpi=150)
    plt.close()
    print("  chart_cv_vs_llm.png")


def chart_multichain():
    """Chart 4: Multi-chain pipeline comparison."""
    pipelines = ["DINOv2\nfull photo", "DINOv2\nSAM-2 crop", "DINOv2\nHSV crop", "Chance\nbaseline"]
    rates = [47.8, 34.3, 32.8, 33.3]
    colors = ["#2ECC71", "#E67E22", "#E67E22", "#BDC3C7"]
    edge_colors = ["#27AE60", "#D35400", "#D35400", "#95A5A6"]

    fig, ax = plt.subplots(figsize=(9, 6))
    bars = ax.bar(pipelines, rates, color=colors, edgecolor=edge_colors, linewidth=1.5, width=0.55)

    ax.axhline(y=CHANCE, color="gray", linestyle="--", linewidth=1.5)

    for bar, rate in zip(bars, rates):
        weight = "bold" if rate > CHANCE + 1 else "normal"
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.8,
                f"{rate:.1f}%", ha="center", va="bottom", fontweight=weight, fontsize=14)

    ax.set_ylabel("CH19 win rate (%)", fontsize=13)
    ax.set_title("Multi-Chain Pipeline: Cropping Plasma Degrades Signal", fontsize=14, fontweight="bold")
    ax.set_ylim(0, 60)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter())

    plt.tight_layout()
    fig.savefig(CHARTS_DIR / "chart_multichain.png", dpi=150)
    plt.close()
    print("  chart_multichain.png")


if __name__ == "__main__":
    print("Generating charts...")
    chart_ch19_winrate()
    chart_per_patient()
    chart_cv_vs_llm()
    chart_multichain()
    print(f"Done. Charts saved to {CHARTS_DIR}/")
