#!/usr/bin/env python3
"""summarize_results.py

Utility script to compute and print macro‑averaged F1 scores for all single‑turn
evaluation runs present in the ``logs/single-turn`` directory.

It processes three categories of datasets:
1. **Base (human)** – original ``banking77_test_with_uuid`` results.
2. **Clean (human)** – label‑cleaned ``banking77_test_clean_labels`` results.
3. **Synthetic persona** – generated persona datasets for each LLM.

The script prints a markdown‑compatible table that can be copied directly into
the thesis (Chapter 6).  All numbers are rounded to three decimal places.

Usage:
    python3 scripte/02_single_turn/summarize_results.py

The script requires no external dependencies beyond the Python standard library.
"""

import json
import os
import glob
from typing import Dict, Tuple


def macro_f1(filepath: str) -> float:
    """Compute macro‑averaged F1 for a JSON‑L result file.

    Each line in the file is expected to contain ``true_intent`` and
    ``predicted_intent`` fields.
    """
    true, pred = [], []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            true.append(data["true_intent"])
            pred.append(data["predicted_intent"])

    labels = set(true)
    f1_scores = []
    for lbl in labels:
        tp = sum(t == lbl and p == lbl for t, p in zip(true, pred))
        fp = sum(t != lbl and p == lbl for t, p in zip(true, pred))
        fn = sum(t == lbl and p != lbl for t, p in zip(true, pred))
        if tp + fp == 0 or tp + fn == 0:
            continue
        precision = tp / (tp + fp)
        recall = tp / (tp + fn)
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        f1_scores.append(f1)
    return sum(f1_scores) / len(f1_scores) if f1_scores else 0.0


def collect_base_results() -> Dict[str, float]:
    """Collect macro‑F1 for the *base* (human) dataset.

    Returns a mapping ``model_name -> macro_f1``.
    """
    base_dir = os.path.join("logs", "single-turn", "baseline-human-dataset", "base")
    results: Dict[str, float] = {}
    for path in glob.glob(os.path.join(base_dir, "results-*.jsonl")):
        # filename pattern: results-<model>-banking77_test_with_uuid.jsonl
        name = os.path.basename(path)
        # Extract the model name between "results-" and "-banking77"
        model = name.split("results-")[1].split("-banking77")[0]
        results[model] = macro_f1(path)
    return results


def collect_clean_results() -> Dict[str, float]:
    """Collect macro‑F1 for the *clean* (human) dataset.

    Returns a mapping ``model_name -> macro_f1``.
    """
    clean_dir = os.path.join("logs", "single-turn", "baseline-human-dataset", "clean_labels")
    results: Dict[str, float] = {}
    for path in glob.glob(os.path.join(clean_dir, "results-*.jsonl")):
        # filename pattern: results-<model>-banking77_test_clean_labels.jsonl
        name = os.path.basename(path)
        # Extract the model name between "results-" and "-banking77"
        model = name.split("results-")[1].split("-banking77")[0]
        results[model] = macro_f1(path)
    return results


def collect_synthetic_results() -> Dict[Tuple[str, str], float]:
    """Collect macro‑F1 for all synthetic persona runs.

    The synthetic results are stored in ``logs/single-turn/synthetic-dataset/<generator>/``
    where ``<generator>`` is the model that produced the persona data (e.g. ``gpt-oss``).
    Inside each directory the files follow the pattern:
        ``results-<evaluator>-banking77_personas_<generator>_clean.jsonl``
    ``<evaluator>`` is the model whose performance is being measured.

    The function returns a mapping ``(evaluator, generator) -> macro_f1``.
    """
    synthetic_root = os.path.join("logs", "single-turn", "synthetic-dataset")
    results: Dict[Tuple[str, str], float] = {}
    for generator in os.listdir(synthetic_root):
        gen_path = os.path.join(synthetic_root, generator)
        if not os.path.isdir(gen_path):
            continue
        for path in glob.glob(os.path.join(gen_path, "results-*.jsonl")):
            name = os.path.basename(path)
            # Only consider the cleaned synthetic results (files ending with _clean.jsonl)
            if not name.endswith("_clean.jsonl"):
                continue
            # Ensure the filename contains the expected tokens
            if "_personas_" not in name or "-banking77" not in name:
                continue
            # Evaluator: between "results-" and "-banking77"
            evaluator = name.split("results-")[1].split("-banking77")[0]
            # Generator: the part after "_personas_" and before "_clean.jsonl"
            generator_name = name.split("_personas_")[1].replace("_clean.jsonl", "")
            results[(evaluator, generator_name)] = macro_f1(path)
    return results


def format_score(value: float) -> str:
    """Format a float to three decimal places for markdown output."""
    return f"{value:.3f}"


def main() -> None:
    base = collect_base_results()
    clean = collect_clean_results()
    synthetic = collect_synthetic_results()

    # ---------------------------------------------------------------------
    # 1. Print Base (human) results
    # ---------------------------------------------------------------------
    print("## Base (human) results")
    print("| Model | Macro‑F1 |")
    print("|---|---|")
    for model in sorted(base):
        print(f"| {model} | {format_score(base[model])} |")

    # ---------------------------------------------------------------------
    # 2. Print Clean (human) results
    # ---------------------------------------------------------------------
    print("\n## Clean (human) results")
    print("| Model | Macro‑F1 |")
    print("|---|---|")
    for model in sorted(clean):
        print(f"| {model} | {format_score(clean[model])} |")

    # ---------------------------------------------------------------------
    # 3. Print Synthetic persona results grouped by generator model
    # ---------------------------------------------------------------------
    print("\n## Synthetic persona results")
    # Organise by generator
    synth_by_gen: Dict[str, Dict[str, float]] = {}
    for (evaluator, generator), score in synthetic.items():
        synth_by_gen.setdefault(generator, {})[evaluator] = score

    for generator in sorted(synth_by_gen):
        print(f"\n### Generator: {generator}")
        print("| Evaluator | Macro‑F1 |")
        print("|---|---|")
        for evaluator in sorted(synth_by_gen[generator]):
            print(f"| {evaluator} | {format_score(synth_by_gen[generator][evaluator])} |")


if __name__ == "__main__":
    main()
