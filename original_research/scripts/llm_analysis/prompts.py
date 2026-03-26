"""Prompt templates for blood plasma LLM vision analysis."""

STRUCTURED_OUTPUT_SUFFIX = (
    "\n\nAfter your analysis, output a JSON code block with structured data:\n"
    "```json\n"
    "{\n"
    '  "scene": "description of the physical setup and background",\n'
    '  "sample_count": 2,\n'
    '  "view": "macro / side / top-down / horizontal / close-up",\n'
    '  "plasma": {\n'
    '    "color": "yellow-greenish",\n'
    '    "transparency": "translucent / opaque / cloudy",\n'
    '    "clots": true,\n'
    '    "clot_stage": "none | early_fibrin | partial_clot | full_coagulation | lysis",\n'
    '    "notes": "detailed observations about morphology, density, texture"\n'
    "  }\n"
    "}\n"
    "```\n"
    "Fill only the fields you can determine from the image. Use null for uncertain fields."
)

# Prompt A: single-photo blind assessment (no experiment context)
SINGLE_PROMPT = (
    "You are an expert biomedical image analyst specializing in blood plasma samples.\n\n"
    "Analyze this image and provide a structured assessment:\n\n"
    "1. **Sample count**: How many sample tubes/containers are visible?\n"
    "2. **View type**: What is the camera angle? "
    "(macro close-up / frontal / horizontal / top-down / bottom-up / side)\n"
    "3. **Plasma color**: Describe the exact color "
    "(e.g. pale yellow, bright yellow, yellow-green, yellow-orange, yellowish-brown, colorless)\n"
    "4. **Transparency**: Is the plasma transparent, semi-transparent, or opaque?\n"
    "5. **Clots/fibrin**: Are any clots, fibrin strands, or coagulation structures visible? "
    "(yes/no, then describe size, shape, location)\n"
    "6. **Clot stage**: If clots are present, estimate the coagulation stage "
    "(early fibrin formation / partial clot / full coagulation / lysis)\n"
    "7. **Density**: Describe the overall density and homogeneity of the plasma\n"
    "8. **Scene**: Describe the background and lighting setup "
    "(LED backlight, dark surface, lab bench, etc.)\n"
    "9. **Anomalies**: Note any unusual features, artifacts, or contamination\n\n"
    "Be precise, objective, and use consistent terminology."
    + STRUCTURED_OUTPUT_SUFFIX
)

# Prompt B: comparative analysis (3 images with experiment context)
COMPARATIVE_PROMPT = (
    "You are an expert biomedical image analyst conducting a comparative study "
    "of blood plasma coagulation under different experimental conditions.\n\n"
    "You are shown THREE blood plasma samples from the SAME donor, photographed "
    "under identical conditions but exposed to different treatments:\n\n"
    "- **Image 1 (CONTROL)**: No exposure — sample placed ~1.5m from the field emitter\n"
    "- **Image 2 (CH19 — time acceleration)**: Exposed to hyperbolic field channel 19\n"
    "- **Image 3 (CH21 — time deceleration)**: Exposed to hyperbolic field channel 21\n\n"
    "For EACH sample, assess independently:\n"
    "1. Plasma color and transparency\n"
    "2. Presence/absence of clots, fibrin strands, or coagulation structures (yes/no + details)\n"
    "3. Coagulation stage: none / early_fibrin / partial_clot / full_coagulation / lysis\n"
    "4. Density and homogeneity\n"
    "5. Any unique morphological features\n\n"
    "Then COMPARE:\n"
    "- Which sample shows the most advanced coagulation? Which the least?\n"
    "- Are there visible differences between control and treated samples?\n"
    "- Do CH19 and CH21 samples differ from each other?\n"
    "- Rate the overall visual difference between control and treated samples: "
    "none / subtle / moderate / pronounced\n\n"
    "Be precise, objective. Do not assume outcomes — describe only what you see.\n\n"
    "After your analysis, output a JSON code block:\n"
    "```json\n"
    "{\n"
    '  "control": {\n'
    '    "color": "pale yellow",\n'
    '    "transparency": "transparent / semi-transparent / opaque",\n'
    '    "clots": false,\n'
    '    "clot_stage": "none | early_fibrin | partial_clot | full_coagulation | lysis",\n'
    '    "notes": "observations"\n'
    "  },\n"
    '  "ch19": {\n'
    '    "color": "...", "transparency": "...", "clots": true, "clot_stage": "...", "notes": "..."\n'
    "  },\n"
    '  "ch21": {\n'
    '    "color": "...", "transparency": "...", "clots": false, "clot_stage": "...", "notes": "..."\n'
    "  },\n"
    '  "most_coagulated": "control | ch19 | ch21",\n'
    '  "least_coagulated": "control | ch19 | ch21",\n'
    '  "overall_difference": "none | subtle | moderate | pronounced",\n'
    '  "comparison_notes": "key observations about differences between samples"\n'
    "}\n"
    "```\n"
    "Fill only the fields you can determine. Use null for uncertain fields."
)

# Prompt C: multi-tube single-photo comparative analysis
MULTI_TUBE_PROMPT_TEMPLATE = (
    "You are an expert biomedical image analyst conducting a comparative study "
    "of blood plasma coagulation under different experimental conditions.\n\n"
    "This SINGLE photograph shows MULTIPLE test tubes from the SAME donor.\n"
    "Tube arrangement: **{caption}**\n\n"
    "The channel codes mean:\n"
    "- **0** (CONTROL): No field exposure — sample placed ~1.5m from the emitter\n"
    "- **19** (CH19 — time acceleration): Exposed to hyperbolic field channel 19\n"
    "- **21** (CH21 — time deceleration): Exposed to hyperbolic field channel 21\n\n"
    "For EACH visible tube, assess:\n"
    "1. Plasma color and transparency\n"
    "2. Presence/absence of clots, fibrin strands, or coagulation structures\n"
    "3. Coagulation stage: none / early_fibrin / partial_clot / full_coagulation / lysis\n"
    "4. Density and homogeneity\n\n"
    "Then COMPARE:\n"
    "- Which tube shows the most advanced coagulation? Which the least?\n"
    "- Are there visible differences between control and treated samples?\n"
    "- Do CH19 and CH21 tubes differ from each other?\n"
    "- Rate the overall visual difference: none / subtle / moderate / pronounced\n\n"
    "Be precise, objective. Do not assume outcomes — describe only what you see.\n\n"
    "After your analysis, output a JSON code block:\n"
    "```json\n"
    "{{\n"
    '  "control": {{\n'
    '    "color": "pale yellow",\n'
    '    "transparency": "transparent / semi-transparent / opaque",\n'
    '    "clots": false,\n'
    '    "clot_stage": "none | early_fibrin | partial_clot | full_coagulation | lysis",\n'
    '    "notes": "observations"\n'
    "  }},\n"
    '  "ch19": {{\n'
    '    "color": "...", "transparency": "...", "clots": true, "clot_stage": "...", "notes": "..."\n'
    "  }},\n"
    '  "ch21": {{\n'
    '    "color": "...", "transparency": "...", "clots": false, "clot_stage": "...", "notes": "..."\n'
    "  }},\n"
    '  "most_coagulated": "control | ch19 | ch21",\n'
    '  "least_coagulated": "control | ch19 | ch21",\n'
    '  "overall_difference": "none | subtle | moderate | pronounced",\n'
    '  "comparison_notes": "key observations about differences between tubes"\n'
    "}}\n"
    "```\n"
    "Fill only the fields you can determine. Use null for uncertain fields."
)

# ============================================================
# BLINDED prompts — no experiment context, neutral labels
# ============================================================

# Prompt B-blind: comparative analysis, 3 separate images, blinded
COMPARATIVE_PROMPT_BLINDED = (
    "You are an expert biomedical image analyst.\n\n"
    "You are shown THREE blood plasma samples from the SAME donor, "
    "photographed under identical conditions. The samples were exposed "
    "to different experimental conditions that are NOT disclosed to you.\n\n"
    "- **Image 1 → Sample A**\n"
    "- **Image 2 → Sample B**\n"
    "- **Image 3 → Sample C**\n\n"
    "For EACH sample, assess independently:\n"
    "1. Plasma color and transparency\n"
    "2. Presence/absence of clots, fibrin strands, or coagulation structures (yes/no + details)\n"
    "3. Coagulation stage: none / early_fibrin / partial_clot / full_coagulation / lysis\n"
    "4. Density and homogeneity\n"
    "5. Any unique morphological features\n\n"
    "Then COMPARE:\n"
    "- Which sample shows the most advanced coagulation? Which the least?\n"
    "- Describe any visible differences between the three samples\n"
    "- Rate the overall visual difference between the samples: "
    "none / subtle / moderate / pronounced\n\n"
    "Be precise, objective. Describe only what you see.\n\n"
    "After your analysis, output a JSON code block:\n"
    "```json\n"
    "{\n"
    '  "sample_a": {\n'
    '    "color": "pale yellow",\n'
    '    "transparency": "transparent / semi-transparent / opaque",\n'
    '    "clots": false,\n'
    '    "clot_stage": "none | early_fibrin | partial_clot | full_coagulation | lysis",\n'
    '    "notes": "observations"\n'
    "  },\n"
    '  "sample_b": {\n'
    '    "color": "...", "transparency": "...", "clots": true, "clot_stage": "...", "notes": "..."\n'
    "  },\n"
    '  "sample_c": {\n'
    '    "color": "...", "transparency": "...", "clots": false, "clot_stage": "...", "notes": "..."\n'
    "  },\n"
    '  "most_coagulated": "sample_a | sample_b | sample_c",\n'
    '  "least_coagulated": "sample_a | sample_b | sample_c",\n'
    '  "overall_difference": "none | subtle | moderate | pronounced",\n'
    '  "comparison_notes": "key observations about differences between samples"\n'
    "}\n"
    "```\n"
    "Fill only the fields you can determine. Use null for uncertain fields."
)

# Prompt C-blind: multi-tube single-photo, blinded
# Caption channel numbers are replaced with A/B/C at runtime
MULTI_TUBE_PROMPT_BLINDED_TEMPLATE = (
    "You are an expert biomedical image analyst.\n\n"
    "This SINGLE photograph shows MULTIPLE test tubes with blood plasma "
    "from the SAME donor. The samples were exposed to different experimental "
    "conditions that are NOT disclosed to you.\n\n"
    "Tube arrangement: **{caption}**\n\n"
    "For EACH visible tube, assess:\n"
    "1. Plasma color and transparency\n"
    "2. Presence/absence of clots, fibrin strands, or coagulation structures\n"
    "3. Coagulation stage: none / early_fibrin / partial_clot / full_coagulation / lysis\n"
    "4. Density and homogeneity\n\n"
    "Then COMPARE:\n"
    "- Which tube shows the most advanced coagulation? Which the least?\n"
    "- Describe any visible differences between the tubes\n"
    "- Rate the overall visual difference: none / subtle / moderate / pronounced\n\n"
    "Be precise, objective. Describe only what you see.\n\n"
    "After your analysis, output a JSON code block:\n"
    "```json\n"
    "{{\n"
    '  "sample_a": {{\n'
    '    "color": "pale yellow",\n'
    '    "transparency": "transparent / semi-transparent / opaque",\n'
    '    "clots": false,\n'
    '    "clot_stage": "none | early_fibrin | partial_clot | full_coagulation | lysis",\n'
    '    "notes": "observations"\n'
    "  }},\n"
    '  "sample_b": {{\n'
    '    "color": "...", "transparency": "...", "clots": true, "clot_stage": "...", "notes": "..."\n'
    "  }},\n"
    '  "sample_c": {{\n'
    '    "color": "...", "transparency": "...", "clots": false, "clot_stage": "...", "notes": "..."\n'
    "  }},\n"
    '  "most_coagulated": "sample_a | sample_b | sample_c",\n'
    '  "least_coagulated": "sample_a | sample_b | sample_c",\n'
    '  "overall_difference": "none | subtle | moderate | pronounced",\n'
    '  "comparison_notes": "key observations about differences between tubes"\n'
    "}}\n"
    "```\n"
    "Fill only the fields you can determine. Use null for uncertain fields."
)

# ============================================================
# BATCH prompts — all patients at once for statistical comparison
# ============================================================

# Prompt E: batch analysis, unblinded
BATCH_PROMPT_UNBLINDED = """\
You are an expert biomedical image analyst conducting a statistical study \
of blood plasma coagulation under different experimental conditions.

You are shown {n_triplets} SETS of blood plasma photographs from {n_patients} different donors. \
Each set contains 3 samples from the SAME donor:
- CONTROL (channel 0): No exposure — sample placed ~1.5m from the field emitter
- CH19 (time acceleration): Exposed to hyperbolic field channel 19
- CH21 (time deceleration): Exposed to hyperbolic field channel 21

The images are organized as follows:
{image_list}

For EACH triplet, briefly assess which sample (control/ch19/ch21) shows the most advanced coagulation.

Then provide a STATISTICAL SUMMARY across ALL patients:
1. In how many patients is CH19 the most coagulated? CH21? Control?
2. Is there a consistent pattern across patients?
3. How would you characterize the overall evidence: no pattern / weak trend / moderate trend / strong pattern?
4. Describe the typical visual differences you see between channels.

Be precise, objective. Do not assume outcomes — describe only what you see.

Output a JSON code block:
```json
{{
  "per_patient": [
    {{
      "patient": "P02",
      "most_coagulated": "control | ch19 | ch21",
      "least_coagulated": "control | ch19 | ch21",
      "difference": "none | subtle | moderate | pronounced",
      "notes": "brief observation"
    }}
  ],
  "summary": {{
    "ch19_most_coagulated_count": 0,
    "ch21_most_coagulated_count": 0,
    "control_most_coagulated_count": 0,
    "pattern_strength": "none | weak | moderate | strong",
    "pattern_description": "description of the overall pattern",
    "conclusion": "one-sentence verdict"
  }}
}}
```"""

# Prompt E-blind: batch analysis, blinded
BATCH_PROMPT_BLINDED = """\
You are an expert biomedical image analyst.

You are shown {n_triplets} SETS of blood plasma photographs from {n_patients} different donors. \
Each set contains 3 samples from the SAME donor, exposed to different experimental conditions \
that are NOT disclosed to you. The samples are labeled A, B, C (same labeling across all patients).

The images are organized as follows:
{image_list}

For EACH triplet, briefly assess which sample (A/B/C) shows the most advanced coagulation.

Then provide a STATISTICAL SUMMARY across ALL patients:
1. In how many patients is Sample A most coagulated? B? C?
2. Is there a consistent pattern across patients — does one sample letter tend to show more coagulation?
3. How would you characterize the overall evidence: no pattern / weak trend / moderate trend / strong pattern?
4. Describe the typical visual differences you see between the three conditions.

Be precise, objective. Describe only what you see.

Output a JSON code block:
```json
{{
  "per_patient": [
    {{
      "patient": "Patient 1",
      "most_coagulated": "sample_a | sample_b | sample_c",
      "least_coagulated": "sample_a | sample_b | sample_c",
      "difference": "none | subtle | moderate | pronounced",
      "notes": "brief observation"
    }}
  ],
  "summary": {{
    "sample_a_most_coagulated_count": 0,
    "sample_b_most_coagulated_count": 0,
    "sample_c_most_coagulated_count": 0,
    "pattern_strength": "none | weak | moderate | strong",
    "pattern_description": "description of the overall pattern",
    "conclusion": "one-sentence verdict"
  }}
}}
```"""

# ============================================================
# FALLBACK prompts — text-only, no images
# ============================================================

# Prompt F: text-only comparison fallback (no images)
COMPARATIVE_FALLBACK_TEMPLATE = (
    "You are comparing three blood plasma analysis reports from the same donor.\n"
    "Each sample was exposed to different conditions:\n\n"
    "## CONTROL (no exposure):\n{control_description}\n\n"
    "## CH19 (time acceleration field):\n{ch19_description}\n\n"
    "## CH21 (time deceleration field):\n{ch21_description}\n\n"
    "Based on these descriptions, compare the three samples:\n"
    "- Which shows the most advanced coagulation?\n"
    "- Are there meaningful differences between control and treated samples?\n"
    "- Do CH19 and CH21 differ from each other?\n\n"
    "Output a JSON code block:\n"
    "```json\n"
    "{{\n"
    '  "most_coagulated": "control | ch19 | ch21",\n'
    '  "least_coagulated": "control | ch19 | ch21",\n'
    '  "overall_difference": "none | subtle | moderate | pronounced",\n'
    '  "comparison_notes": "key differences"\n'
    "}}\n"
    "```"
)
