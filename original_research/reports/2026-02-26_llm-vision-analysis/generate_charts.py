"""Generate charts for the LLM Vision Analysis report v2."""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

OUT = Path(__file__).parent

with open(OUT / "results.json") as f:
    data = json.load(f)

# Color scheme
COLORS = {
    "control": "#4CAF50",
    "ch19": "#FF9800",
    "ch21": "#2196F3",
}
STAGE_COLORS = {
    "none": "#E0E0E0",
    "early_fibrin": "#FFF9C4",
    "partial_clot": "#FFCC80",
    "full_coagulation": "#EF6C00",
    "lysis": "#B71C1C",
}
STAGE_LABELS = {
    "none": "None",
    "early_fibrin": "Early fibrin",
    "partial_clot": "Partial clot",
    "full_coagulation": "Full coagulation",
    "lysis": "Lysis",
}


def get_photos(category):
    """Get photos from a data category."""
    if category in data:
        return data[category]
    return []


def count_by_channel_and_stage(photos):
    """Count stage occurrences per channel."""
    result = {}
    for p in photos:
        ch = p.get("channel", "unknown")
        # Normalize channel names
        if ch in ("ch19_acceleration", "ch19"):
            ch = "ch19"
        elif ch in ("ch21_deceleration", "ch21"):
            ch = "ch21"
        elif ch in ("control", "ch0"):
            ch = "control"
        else:
            continue
        stage = p.get("clot_stage", "none")
        if ch not in result:
            result[ch] = {}
        result[ch][stage] = result[ch].get(stage, 0) + 1
    return result


# Collect all single-channel photos
labeled = get_photos("single_channel")
inferred = get_photos("single_channel_inferred")
combined = labeled + inferred

stats_labeled = count_by_channel_and_stage(labeled)
stats_combined = count_by_channel_and_stage(combined)


# ─── Chart 1: Clot Frequency Comparison (Labeled vs Combined) ───

fig, ax = plt.subplots(figsize=(9, 5.5))
channels = ["ch19", "control", "ch21"]
labels = ["Ch19\n(acceleration)", "Control", "Ch21\n(deceleration)"]

labeled_rates = []
combined_rates = []
labeled_n = []
combined_n = []

for ch in channels:
    l_photos = [p for p in labeled if p.get("channel", "").replace("_acceleration", "").replace("_deceleration", "").replace("ch0", "control") == ch or
                (ch == "ch19" and p.get("channel") == "ch19_acceleration") or
                (ch == "ch21" and p.get("channel") == "ch21_deceleration")]
    c_photos = [p for p in combined if p.get("channel", "").replace("_acceleration", "").replace("_deceleration", "").replace("ch0", "control") == ch or
                (ch == "ch19" and p.get("channel") == "ch19_acceleration") or
                (ch == "ch21" and p.get("channel") == "ch21_deceleration")]

    l_clots = sum(1 for p in l_photos if p.get("clots_visible", False))
    c_clots = sum(1 for p in c_photos if p.get("clots_visible", False))

    labeled_rates.append(l_clots / len(l_photos) * 100 if l_photos else 0)
    combined_rates.append(c_clots / len(c_photos) * 100 if c_photos else 0)
    labeled_n.append(len(l_photos))
    combined_n.append(len(c_photos))

x = np.arange(len(channels))
width = 0.35

bars1 = ax.bar(x - width/2, labeled_rates, width, label=f"Labeled only (n=40)",
               color=[COLORS[ch] for ch in channels], edgecolor="black", linewidth=0.5, alpha=0.6)
bars2 = ax.bar(x + width/2, combined_rates, width, label=f"Labeled + Inferred (n=55)",
               color=[COLORS[ch] for ch in channels], edgecolor="black", linewidth=0.5)

for bar, val, n in zip(bars1, labeled_rates, labeled_n):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
            f"{val:.0f}%\n(n={n})", ha="center", va="bottom", fontsize=10)
for bar, val, n in zip(bars2, combined_rates, combined_n):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
            f"{val:.0f}%\n(n={n})", ha="center", va="bottom", fontsize=10, fontweight="bold")

ax.set_ylabel("Photos with Visible Clots (%)", fontsize=12)
ax.set_title("Clot Frequency by Channel", fontsize=14, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=11)
ax.set_ylim(0, 105)
ax.legend(fontsize=10, loc="upper right")
ax.grid(axis="y", alpha=0.3)
ax.axhline(y=50, color="gray", linestyle="--", alpha=0.3)
plt.tight_layout()
plt.savefig(OUT / "chart_clot_frequency.png", dpi=150)
plt.close()


# ─── Chart 2: Stage Distribution (Combined, Stacked Bar) ───

fig, ax = plt.subplots(figsize=(9, 5.5))
stages = ["none", "early_fibrin", "partial_clot", "full_coagulation", "lysis"]

stage_data = {}
for ch in channels:
    stage_data[ch] = {}
    ch_photos = [p for p in combined if
                 p.get("channel") == ch or
                 p.get("channel") == f"{ch}_acceleration" or
                 p.get("channel") == f"{ch}_deceleration" or
                 (ch == "control" and p.get("channel") == "ch0")]
    total = len(ch_photos) if ch_photos else 1
    for s in stages:
        count = sum(1 for p in ch_photos if p.get("clot_stage") == s)
        stage_data[ch][s] = count / total * 100

x = np.arange(len(channels))
bottom = np.zeros(len(channels))

for stage in stages:
    vals = [stage_data[ch][stage] for ch in channels]
    ax.bar(x, vals, 0.5, bottom=bottom, label=STAGE_LABELS[stage],
           color=STAGE_COLORS[stage], edgecolor="black", linewidth=0.5)
    # Add percentage labels for significant segments
    for i, (v, b) in enumerate(zip(vals, bottom)):
        if v >= 8:
            ax.text(x[i], b + v/2, f"{v:.0f}%", ha="center", va="center",
                    fontsize=9, fontweight="bold")
    bottom += vals

ax.set_ylabel("Distribution (%)", fontsize=12)
ax.set_title("Coagulation Stage Distribution by Channel (n=55)", fontsize=14, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=11)
ax.set_ylim(0, 105)
ax.legend(loc="upper right", fontsize=9)
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(OUT / "chart_stage_distribution.png", dpi=150)
plt.close()


# ─── Chart 3: Per-Patient Heatmap ───

patients = {
    "P01": {"ch19": "early_fibrin", "control": None, "ch21": "early_fibrin"},
    "P02": {"ch19": "lysis", "control": "partial_clot", "ch21": "full_coagulation"},
    "P03": {"ch19": "partial_clot", "control": "full_coagulation", "ch21": "full_coagulation"},
    "P04": {"ch19": "none", "control": "partial_clot", "ch21": "early_fibrin"},
    "P05": {"ch19": "full_coagulation", "control": "none", "ch21": "full_coagulation"},
    "P07": {"ch19": "partial_clot", "control": "partial_clot", "ch21": "none"},
}

stage_values = {"none": 0, "early_fibrin": 1, "partial_clot": 2, "full_coagulation": 3, "lysis": 4}
stage_cmap_colors = ["#E0E0E0", "#FFF9C4", "#FFCC80", "#EF6C00", "#B71C1C"]
from matplotlib.colors import ListedColormap
cmap = ListedColormap(stage_cmap_colors)

patient_names = list(patients.keys())
channel_order = ["ch19", "control", "ch21"]
channel_display = ["Ch19\n(accel)", "Control", "Ch21\n(decel)"]

matrix = np.full((len(patient_names), len(channel_order)), np.nan)
for i, pname in enumerate(patient_names):
    for j, ch in enumerate(channel_order):
        stage = patients[pname].get(ch)
        if stage is not None:
            matrix[i, j] = stage_values[stage]

fig, ax = plt.subplots(figsize=(7, 5))
im = ax.imshow(matrix, cmap=cmap, vmin=-0.5, vmax=4.5, aspect="auto")

# Add text labels
for i in range(len(patient_names)):
    for j in range(len(channel_order)):
        stage = patients[patient_names[i]].get(channel_order[j])
        if stage is not None:
            text_color = "white" if stage in ("full_coagulation", "lysis") else "black"
            ax.text(j, i, STAGE_LABELS.get(stage, "N/A"), ha="center", va="center",
                    fontsize=9, fontweight="bold", color=text_color)
        else:
            ax.text(j, i, "—", ha="center", va="center", fontsize=12, color="gray")

ax.set_xticks(range(len(channel_order)))
ax.set_xticklabels(channel_display, fontsize=11)
ax.set_yticks(range(len(patient_names)))
ax.set_yticklabels(patient_names, fontsize=11)
ax.set_title("Peak Coagulation Stage per Patient", fontsize=14, fontweight="bold")

# Legend
patches = [mpatches.Patch(color=c, label=l) for c, l in
           zip(stage_cmap_colors, ["None", "Early fibrin", "Partial clot", "Full coagulation", "Lysis"])]
ax.legend(handles=patches, loc="upper left", bbox_to_anchor=(1.02, 1), fontsize=9)

plt.tight_layout()
plt.savefig(OUT / "chart_patient_heatmap.png", dpi=150, bbox_inches="tight")
plt.close()


# ─── Chart 4: Method Comparison ───

fig, ax = plt.subplots(figsize=(10, 4.5))

methods = ["LLM Vision\n(Claude Opus 4.6)", "SigLIP2\n(zero-shot CLIP)", "CV Segment\n(SAM-2 + HSV)"]
# How well each method captures the expected ch19 > control > ch21 gradient
# LLM: correctly identifies 78% > 65% > 41%
# SigLIP2: classifies 100% as "none" — no discrimination
# CV: counter-intuitive results (control 8.9 > ch21 8.7 > ch19 5.6)

# Metric: Does the method show ch19 > control > ch21?
gradient_correct = [1.0, 0.0, 0.0]  # Only LLM got it right
colors_methods = ["#4CAF50", "#F44336", "#F44336"]

bars = ax.barh(methods, gradient_correct, color=colors_methods, edgecolor="black", linewidth=0.5, height=0.5)

# Add result annotations
annotations = [
    "Ch19 78% > Control 65% > Ch21 41%  ✓",
    "Classified 100% as 'none'  ✗",
    "Control 8.9 > Ch21 8.7 > Ch19 5.6  ✗",
]
for bar, ann in zip(bars, annotations):
    ax.text(0.05, bar.get_y() + bar.get_height()/2, ann,
            va="center", fontsize=10, fontweight="bold",
            color="white" if bar.get_width() > 0.5 else "black")

ax.set_xlim(0, 1.1)
ax.set_xticks([0, 1])
ax.set_xticklabels(["Incorrect", "Correct"], fontsize=11)
ax.set_title("Method Comparison: Detecting Ch19 > Control > Ch21 Gradient", fontsize=13, fontweight="bold")
ax.grid(axis="x", alpha=0.3)
plt.tight_layout()
plt.savefig(OUT / "chart_method_comparison.png", dpi=150)
plt.close()


# ─── Chart 5: Patient-02 Ch19 Lifecycle Timeline ───

fig, ax = plt.subplots(figsize=(11, 3.5))

lifecycle = [
    ("IMG_3265", "none", "Clear plasma"),
    ("IMG_3267", "early_fibrin", "Haze at meniscus"),
    ("IMG_3277", "full_coagulation", "Gelatinous clot"),
    ("IMG_3284", "lysis", "Cracked fibrin"),
]

x_pos = np.arange(len(lifecycle))
for i, (img, stage, desc) in enumerate(lifecycle):
    color = STAGE_COLORS[stage]
    circle = plt.Circle((i, 0), 0.3, color=color, ec="black", linewidth=1.5)
    ax.add_patch(circle)
    text_color = "white" if stage in ("full_coagulation", "lysis") else "black"
    ax.text(i, 0, STAGE_LABELS[stage].split()[0] if stage != "full_coagulation" else "Full",
            ha="center", va="center", fontsize=8, fontweight="bold", color=text_color)
    ax.text(i, -0.6, img, ha="center", va="top", fontsize=9, color="#333")
    ax.text(i, 0.55, desc, ha="center", va="bottom", fontsize=9, style="italic")
    if i < len(lifecycle) - 1:
        ax.annotate("", xy=(i + 0.65, 0), xytext=(i + 0.35, 0),
                    arrowprops=dict(arrowstyle="->", color="#555", lw=2))

ax.set_xlim(-0.6, len(lifecycle) - 0.4)
ax.set_ylim(-1.0, 1.0)
ax.set_aspect("equal")
ax.axis("off")
ax.set_title("Patient-02 Ch19: Complete Coagulation Lifecycle", fontsize=13, fontweight="bold", pad=10)
plt.tight_layout()
plt.savefig(OUT / "chart_lifecycle.png", dpi=150, bbox_inches="tight")
plt.close()


# ─── Chart 6: Patient-07 Inferred Gradient ───

fig, ax = plt.subplots(figsize=(8, 5))

p07_data = {
    "Ch19\n(4 photos)": {"clots": 4, "total": 4},
    "Control\n(7 photos)": {"clots": 5, "total": 7},
    "Ch21\n(4 photos)": {"clots": 0, "total": 4},
}

p07_labels = list(p07_data.keys())
p07_rates = [d["clots"] / d["total"] * 100 for d in p07_data.values()]
p07_colors = [COLORS["ch19"], COLORS["control"], COLORS["ch21"]]

bars = ax.bar(p07_labels, p07_rates, color=p07_colors, edgecolor="black", linewidth=0.5, width=0.5)

for bar, d in zip(bars, p07_data.values()):
    rate = d["clots"] / d["total"] * 100
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
            f"{rate:.0f}%\n({d['clots']}/{d['total']})",
            ha="center", va="bottom", fontsize=12, fontweight="bold")

ax.set_ylabel("Photos with Visible Clots (%)", fontsize=12)
ax.set_title("Patient-07: EXIF-Inferred Channel Assignment (n=15)", fontsize=13, fontweight="bold")
ax.set_ylim(0, 120)
ax.grid(axis="y", alpha=0.3)
ax.axhline(y=50, color="gray", linestyle="--", alpha=0.3)
plt.tight_layout()
plt.savefig(OUT / "chart_patient07_gradient.png", dpi=150)
plt.close()


print("Charts generated:")
for f in sorted(OUT.glob("chart_*.png")):
    print(f"  {f.name} ({f.stat().st_size // 1024} KB)")
