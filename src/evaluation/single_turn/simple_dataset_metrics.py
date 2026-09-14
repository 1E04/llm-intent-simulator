#!/usr/bin/env python3
"""
dataset_metrics_text_only.py

Evaluates text classification datasets by comparing the user text directly
to the category labels.

Outputs:
    - simple_metrics.csv
    - Three separate PNG plots (Word Overlap, Exact Match Share, Semantic Similarity).
"""

import glob
import re
from pathlib import Path

import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------- Settings
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATASETS_PATH = "dataset/single-turn/*clean.csv"
OUTPUT_DIR = "logs/dataset_metrics"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


# ---------------------------------------------------------------- 1. Text Matching
def extract_words(text):
    """Extracts lowercase alphabetic words from a text."""
    return re.findall(r"[a-z]+", str(text).lower())


def extract_label_words(label):
    """Converts a label like 'Refund_not_showing' into ['refund', 'not', 'showing']."""
    clean_label = str(label).lower().replace("_", " ")
    return re.findall(r"[a-z]+", clean_label)


def check_if_word_in_text(target_word, text_words):
    """Checks if a target word is in the text, allowing for partial matches."""
    for word in text_words:
        if target_word == word:
            return True
        # Allow prefix matching for longer words (e.g., 'show' matches 'showing')
        is_long_enough = len(target_word) >= 4 and len(word) >= 4
        if is_long_enough and (word.startswith(target_word) or target_word.startswith(word)):
            return True
    return False


def calculate_word_overlap(text, label):
    """Calculates what percentage of the label's words appear in the text (0.0 to 1.0)."""
    label_words = extract_label_words(label)
    text_words = extract_words(text)

    if not label_words:
        return 0.0

    matches = sum(check_if_word_in_text(w, text_words) for w in label_words)
    return matches / len(label_words)


# ---------------------------------------------------------------- 2. Semantic Similarity
def calculate_semantic_similarity(texts, labels, ai_model):
    """
    Calculates how close the meaning of the text is to the label.
    Outputs a cosine similarity score (0.0 to 1.0).
    """
    clean_labels = [str(l).replace("_", " ").lower() for l in labels]

    text_vectors = ai_model.encode(list(texts), batch_size=128, normalize_embeddings=True, show_progress_bar=True)
    label_vectors = ai_model.encode(clean_labels, batch_size=128, normalize_embeddings=True)

    return (text_vectors * label_vectors).sum(axis=1)


# ---------------------------------------------------------------- 3. Plotting
def format_dataset_name(raw_name):
    """Cleans up raw filenames into readable chart labels."""
    name = raw_name.replace("_clean", "")
    name = name.replace("banking77_personas_", "")
    name = name.replace("banking77_test_", "")

    if name == "human labels" or name == "human_labels":
        return "Human Baseline"

    return name


def create_individual_plots(results_table, output_directory):
    """Generates and saves a separate PNG chart for each metric."""

    # Apply our new clean naming function
    clean_names = [format_dataset_name(name) for name in results_table["dataset"]]

    charts_to_make = [
        ("word_overlap", "Average Share of Label Words in Text", "plot_word_overlap.png"),
        ("all_words_present", "Share of Texts Containing ALL Label Words", "plot_all_words_present.png"),
        ("label_similarity", "Semantic Similarity (Text vs Label Meaning)", "plot_label_similarity.png")
    ]

    bar_colors = ["#1f77b4" if row_type == "human" else "#ff7f0e" for row_type in results_table["type"]]
    legend_handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in ("#1f77b4", "#ff7f0e")]

    for column, title, filename in charts_to_make:
        plt.figure(figsize=(7, 6))
        plt.bar(range(len(results_table)), results_table[column], color=bar_colors)

        plt.title(title, fontsize=13, pad=15)
        plt.xticks(range(len(results_table)), clean_names, rotation=45, ha="right", fontsize=10)
        plt.grid(axis="y", linestyle="--", alpha=0.4)

        # INCREASE Y-AXIS HEIGHT
        if column == "label_similarity":
            # Force similarity to scale out of 1.0 maximum
            plt.ylim(0, 1.0)
        else:
            # Add 25% headroom above the tallest bar for other plots
            max_value = results_table[column].max()
            plt.ylim(0, max_value * 1.25)

        # Add values on top of bars
        for index, value in enumerate(results_table[column]):
            if pd.notna(value):
                plt.text(index, value + 0.01, f"{value:.2f}", ha="center", va="bottom", fontsize=9)

        plt.legend(legend_handles, ["Human Baseline", "Synthetic (AI)"], loc="best")
        plt.tight_layout()

        save_path = output_directory / filename
        plt.savefig(save_path, dpi=200)
        plt.close()
        print(f"Saved chart: {save_path}")


# ---------------------------------------------------------------- Main Execution
def main():
    from sentence_transformers import SentenceTransformer

    dataset_files = sorted(glob.glob(str(PROJECT_ROOT / DATASETS_PATH)))
    if not dataset_files:
        raise SystemExit(f"No datasets found in: {DATASETS_PATH}")

    print(f"Loading AI Embedding Model ({EMBEDDING_MODEL_NAME})...")
    ai_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    results_list = []

    for file_path in dataset_files:
        path_obj = Path(file_path)
        dataset_name = path_obj.stem
        print(f"Processing: {dataset_name}")

        df = pd.read_csv(path_obj)

        # 1. Word Metrics
        df["word_overlap"] = [calculate_word_overlap(text, label) for text, label in zip(df["text"], df["label_text"])]
        df["all_words_present"] = df["word_overlap"] >= 1.0

        # 2. Semantic Metrics
        df["semantic_similarity"] = calculate_semantic_similarity(df["text"], df["label_text"], ai_model)

        results_list.append({
            "dataset": dataset_name,
            "type": "human" if "human" in dataset_name.lower() or "banking77_test" in dataset_name else "synthetic",
            "rows": len(df),
            "word_overlap": df["word_overlap"].mean(),
            "all_words_present": df["all_words_present"].mean(),
            "label_similarity": df["semantic_similarity"].mean(),
        })

    # Compile Results
    results_table = pd.DataFrame(results_list).sort_values("label_similarity", ascending=False)

    # Save to CSV
    output_dir = PROJECT_ROOT / OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "simple_metrics.csv"
    results_table.to_csv(csv_path, index=False)

    print("\n" + "=" * 70)
    print("RESULTS (Sorted by Semantic Similarity - Top is best)")
    print("=" * 70)
    print(results_table.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    print(f"\nData saved to: {csv_path}\n")

    # Generate separate plots
    create_individual_plots(results_table, output_dir)


if __name__ == "__main__":
    main()