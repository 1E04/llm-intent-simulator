#!/usr/bin/env python3
"""plot_comparison.py

Generate a bar‑chart that compares the **clean‑label human baseline** macro‑F1
scores against the **best synthetic persona** macro‑F1 for each model.

The script reads the same log files used by ``summarize_results.py`` and:
  * extracts the clean‑label scores (``logs/single-turn/baseline-human-dataset/clean_labels``)
  * extracts all synthetic scores (only ``*_clean.jsonl`` files) and selects, for
    each evaluator model, the highest score across all generators.
  * produces a side‑by‑side bar chart (clean vs best synthetic) and saves it as
    ``logs/single-turn/comparison_clean_vs_synthetic.png``.

Usage::

    python3 scripte/02_single_turn/plot_comparison.py

The figure can be directly inserted into the thesis (Chapter 6).
"""

import json
import os
import glob
# Use a non‑interactive backend to avoid Tk/Tcl requirements on headless systems
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from typing import Dict, Tuple


def macro_f1(filepath: str) -> float:
    """Compute macro‑averaged F1 for a JSON‑L result file."""
    true, pred = [], []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            d = json.loads(line)
            true.append(d["true_intent"])
            pred.append(d["predicted_intent"])
    labels = set(true)
    f1s = []
    for lbl in labels:
        tp = sum(t == lbl and p == lbl for t, p in zip(true, pred))
        fp = sum(t != lbl and p == lbl for t, p in zip(true, pred))
        fn = sum(t == lbl and p != lbl for t, p in zip(true, pred))
        if tp + fp == 0 or tp + fn == 0:
            continue
        precision = tp / (tp + fp)
        recall = tp / (tp + fn)
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        f1s.append(f1)
    return sum(f1s) / len(f1s) if f1s else 0.0


def load_clean_scores() -> Dict[str, float]:
    """Load clean‑label baseline scores (model -> macro‑F1)."""
    clean_dir = os.path.join("logs", "single-turn", "baseline-human-dataset", "clean_labels")
    scores: Dict[str, float] = {}
    for path in glob.glob(os.path.join(clean_dir, "results-*.jsonl")):
        name = os.path.basename(path)
        model = name.split("results-")[1].split("-banking77")[0]
        scores[model] = macro_f1(path)
    return scores


def load_best_synthetic_scores() -> Dict[str, float]:
    """Load synthetic scores and keep the best (highest) per evaluator model."""
    synthetic_root = os.path.join("logs", "single-turn", "synthetic-dataset")
    best: Dict[str, float] = {}
    for gen in os.listdir(synthetic_root):
        gen_path = os.path.join(synthetic_root, gen)
        if not os.path.isdir(gen_path):
            continue
        for path in glob.glob(os.path.join(gen_path, "results-*_clean.jsonl")):
            name = os.path.basename(path)
            if "_personas_" not in name or "-banking77" not in name:
                continue
            evaluator = name.split("results-")[1].split("-banking77")[0]
            score = macro_f1(path)
            if evaluator not in best or score > best[evaluator]:
                best[evaluator] = score
    return best


def plot_comparison(clean: Dict[str, float], synthetic: Dict[str, float]) -> None:
    """Create a side‑by‑side bar chart and save it as PNG."""
    # Combine model identifiers and sort them for consistent ordering
    models = sorted(set(clean.keys()) | set(synthetic.keys()))
    clean_vals = [clean.get(m, 0) for m in models]
    synth_vals = [synthetic.get(m, 0) for m in models]

    # Human‑readable name mapping for the model identifiers used in the logs
    # Human‑readable names for the model identifiers used in the log files.
    # The Qwen model is excluded as per user request.
    name_map = {
        "phi4:14b": "Phi4",
        "phi4_14b": "Phi4",
        "gpt-oss": "GPT‑OSS",
        "gpt-5.4-nano": "GPT‑5.4 Nano",
        "openai-nano": "OpenAI Nano",
        "openai-gpt-oss-120b": "OpenAI GPT‑OSS 120B",
        "gemini": "Gemini Flash",
        "mistral-small_24b": "Mistral Small",
        # "qwen3.6" entry intentionally omitted
    }
    # Filter out any models that are not in the name_map (e.g., Qwen) to avoid plotting them.
    filtered_models = [m for m in models if m in name_map]
    clean_vals = [clean.get(m, 0) for m in filtered_models]
    synth_vals = [synthetic.get(m, 0) for m in filtered_models]
    display_names = [name_map[m] for m in filtered_models]
    x = range(len(filtered_models))

    # Use narrower bars and a larger offset to create a more visible gap between the paired bars
    bar_width = 0.30
    gap_offset = 0.003  # larger shift for clearer spacing
    x = range(len(filtered_models))

    fig, ax = plt.subplots(figsize=(10, 6))
    # Keep references to bar containers for annotation
    bars_clean = ax.bar([i - gap_offset - bar_width/2 for i in x], clean_vals, bar_width, label="Clean baseline")
    bars_synth = ax.bar([i + gap_offset + bar_width/2 for i in x], synth_vals, bar_width, label="Best synthetic")
    ax.set_xlabel("Model")
    ax.set_ylabel("Macro‑F1")
    ax.set_title("Clean‑label baseline vs. Best synthetic persona (macro‑F1)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(display_names, rotation=45, ha="right")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.7)
    # Ensure y‑axis always spans the full 0.0‑1.0 range for consistency
    ax.set_ylim(0.0, 1.0)
    ax.grid(axis="y", linestyle="--", alpha=0.7)

    # Annotate each bar with its value as a percentage
    def annotate(bars):
        for rect in bars:
            height = rect.get_height()
            if height > 0:
                ax.text(
                    rect.get_x() + rect.get_width() / 2,
                    height + 0.005,
                    f"{height*100:.1f}%",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                )

    annotate(bars_clean)
    annotate(bars_synth)

    out_path = os.path.join("logs", "single-turn", "comparison_clean_vs_synthetic.png")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    print(f"Saved comparison plot to {out_path}")


def main() -> None:
    clean_scores = load_clean_scores()
    best_synth = load_best_synthetic_scores()
    plot_comparison(clean_scores, best_synth)


if __name__ == "__main__":
    main()
