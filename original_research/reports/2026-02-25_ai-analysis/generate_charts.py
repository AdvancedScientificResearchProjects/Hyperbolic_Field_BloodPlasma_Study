"""Generate charts for the experiment report."""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

OUT = Path(__file__).parent
DATA = Path(__file__).parents[2] / "processed" / ".." / ".." / "asrp.science-llm" / "scripts" / "experiment_results"

# Find latest results
results_files = sorted(Path("/home/liker/projects/ai-research/asrp.science-llm/scripts/experiment_results").glob("results_*.json"))
with open(results_files[-1]) as f:
    data = json.load(f)

agg = data["channel_aggregates"]
channels = ["0", "19", "21"]
labels = ["Control", "Ch19\n(acceleration)", "Ch21\n(deceleration)"]
colors = ["#4CAF50", "#FF9800", "#2196F3"]

# --- Chart 1: Clot Count ---
fig, ax = plt.subplots(figsize=(8, 5))
counts = [agg[ch]["segment"]["clot_count"]["mean"] for ch in channels]
stds = [agg[ch]["segment"]["clot_count"]["std"] for ch in channels]
bars = ax.bar(labels, counts, yerr=stds, color=colors, capsize=8, edgecolor="black", linewidth=0.5)
ax.set_ylabel("Average Clot Count per Image", fontsize=12)
ax.set_title("Fibrin Clot Count by Channel", fontsize=14, fontweight="bold")
for bar, val in zip(bars, counts):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3, f"{val:.1f}",
            ha="center", va="bottom", fontsize=11, fontweight="bold")
ax.set_ylim(0, max(counts) * 1.3)
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(OUT / "chart_clot_count.png", dpi=150)
plt.close()

# --- Chart 2: Clot Area ---
fig, ax = plt.subplots(figsize=(8, 5))
areas = [agg[ch]["segment"]["clot_area_ratio"]["mean"] * 100 for ch in channels]
bars = ax.bar(labels, areas, color=colors, edgecolor="black", linewidth=0.5)
ax.set_ylabel("Total Clot Area (% of image)", fontsize=12)
ax.set_title("Fibrin Clot Total Area by Channel", fontsize=14, fontweight="bold")
for bar, val in zip(bars, areas):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, f"{val:.3f}%",
            ha="center", va="bottom", fontsize=11, fontweight="bold")
ax.set_ylim(0, max(areas) * 1.3)
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(OUT / "chart_clot_area.png", dpi=150)
plt.close()

# --- Chart 3: SigLIP2 Coagulation Scores ---
fig, ax = plt.subplots(figsize=(10, 6))
stages = ["none", "early_fibrin", "partial_clot", "full_coagulation", "lysis"]
stage_labels = ["No fibrin", "Early\nfibrin", "Partial\nclot", "Full\ncoagulation", "Lysis"]
x = np.arange(len(stages))
width = 0.25

for i, (ch, label, color) in enumerate(zip(channels, ["Control", "Ch19", "Ch21"], colors)):
    scores = [agg[ch]["ml"]["stage_scores"].get(s, {}).get("mean", 0) for s in stages]
    ax.bar(x + i * width, scores, width, label=label, color=color, edgecolor="black", linewidth=0.5)

ax.set_ylabel("SigLIP2 Score (0-1)", fontsize=12)
ax.set_title("Coagulation Stage Scores by Channel (SigLIP2 Zero-Shot)", fontsize=14, fontweight="bold")
ax.set_xticks(x + width)
ax.set_xticklabels(stage_labels, fontsize=10)
ax.legend(fontsize=11)
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(OUT / "chart_siglip2_stages.png", dpi=150)
plt.close()

# --- Chart 4: CV Metrics Comparison ---
fig, axes = plt.subplots(1, 3, figsize=(14, 5))

metrics = [
    ("GLCM Contrast", "glcm_contrast"),
    ("Edge Density", "edge_density"),
    ("Brightness", "brightness_mean"),
]
for ax, (title, key) in zip(axes, metrics):
    vals = [agg[ch]["cv"][key]["mean"] for ch in channels]
    bars = ax.bar(labels, vals, color=colors, edgecolor="black", linewidth=0.5)
    ax.set_title(title, fontsize=12, fontweight="bold")
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                f"{val:.4f}" if val < 1 else f"{val:.1f}",
                ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax.set_ylim(0, max(vals) * 1.25)
    ax.grid(axis="y", alpha=0.3)

fig.suptitle("Classical CV Metrics by Channel", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig(OUT / "chart_cv_metrics.png", dpi=150)
plt.close()

# --- Chart 5: Delta summary ---
fig, ax = plt.subplots(figsize=(10, 6))
metric_names = [
    "Clot count",
    "Clot area",
    "GLCM contrast",
    "Edge density",
    "Brightness",
    "Entropy",
]
d19 = data["deltas_ch19_vs_control"]
d21 = data["deltas_ch21_vs_control"]
ch19_deltas = [
    d19.get("segment.clot_count", {}).get("delta_pct", 0),
    d19.get("segment.clot_area_ratio", {}).get("delta_pct", 0),
    d19.get("cv.glcm_contrast", {}).get("delta_pct", 0),
    d19.get("cv.edge_density", {}).get("delta_pct", 0),
    d19.get("cv.brightness_mean", {}).get("delta_pct", 0),
    d19.get("cv.entropy", {}).get("delta_pct", 0),
]
ch21_deltas = [
    d21.get("segment.clot_count", {}).get("delta_pct", 0),
    d21.get("segment.clot_area_ratio", {}).get("delta_pct", 0),
    d21.get("cv.glcm_contrast", {}).get("delta_pct", 0),
    d21.get("cv.edge_density", {}).get("delta_pct", 0),
    d21.get("cv.brightness_mean", {}).get("delta_pct", 0),
    d21.get("cv.entropy", {}).get("delta_pct", 0),
]

y = np.arange(len(metric_names))
height = 0.35
ax.barh(y + height/2, ch19_deltas, height, label="Ch19 (acceleration)", color="#FF9800", edgecolor="black", linewidth=0.5)
ax.barh(y - height/2, ch21_deltas, height, label="Ch21 (deceleration)", color="#2196F3", edgecolor="black", linewidth=0.5)
ax.axvline(0, color="black", linewidth=0.8)
ax.set_yticks(y)
ax.set_yticklabels(metric_names, fontsize=11)
ax.set_xlabel("Change vs Control (%)", fontsize=12)
ax.set_title("Metric Deltas: Treatment vs Control", fontsize=14, fontweight="bold")
ax.legend(fontsize=11)
ax.grid(axis="x", alpha=0.3)
plt.tight_layout()
plt.savefig(OUT / "chart_deltas.png", dpi=150)
plt.close()

print("Charts generated:")
for f in sorted(OUT.glob("chart_*.png")):
    print(f"  {f.name}")
