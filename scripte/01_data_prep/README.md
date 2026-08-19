# 🧹 Data Preparation & Curation (`scripte/01_data_prep/`)

This directory contains scripts responsible for generating synthetic NLU utterances, cleaning and normalizing intent labels, generating unique identifiers (UUIDs), deduplicating dataset entries via LLMs, and recording telephony audio samples.

---

## 📄 File Overview & Usage Guide

### 1. `generate_banking77_dataset.py`
* **Purpose**: Generates synthetic customer utterances for intent classification datasets using an LLM. It applies distinct behavioral customer personas (e.g., *"Angry layperson"*, *"Panicking emergency customer"*, *"Gen-Z slang speaker"*) to create diverse, realistic text phrasing.
* **Key Features**:
  * Injects numerical intent IDs and UUIDs directly into generated outputs.
  * Outputs columns: `id`, `text`, `label_text`, `label`, `persona`.
* **Usage**:
  ```bash
  python generate_banking77_dataset.py
  ```

---

### 2. `add_uuid_to_dataset.py`
* **Purpose**: Injects a unique version 4 UUID (`uuid4`) as the first column (`id`) of any input CSV dataset to enable tracking of individual samples across evaluation runs.
* **Usage**:
  ```bash
  python add_uuid_to_dataset.py
  ```
* **Inputs & Outputs**:
  * Input: `../../dataset/single-turn/banking77_test.csv`
  * Output: `../../dataset/single-turn/banking77_test_with_uuid.csv`

---

### 3. `add_numerical_label.py`
* **Purpose**: Maps textual label names in a synthetic CSV dataset to integer IDs based on a reference original dataset (e.g., Banking77 standard indexing). Labels absent from the original mapping are assigned an ID of `-1`.
* **CLI Arguments**:
  * `--original`: Path to original reference CSV (containing text and numeric label IDs).
  * `--synthetic`: Path to target synthetic CSV.
  * `--output`: Output CSV file path (default: `synthetic_with_numeric_labels.csv`).
* **Usage**:
  ```bash
  python add_numerical_label.py \
    --original "../../dataset/single-turn/banking77_test.csv" \
    --synthetic "synthetic_data.csv" \
    --output "synthetic_with_ids.csv"
  ```

---

### 4. `clean_dataset_labels.py`
* **Purpose**: Performs single or bulk label category renaming across a CSV dataset. Ensures label consistency between single-turn evaluation sets and multi-turn scenario profiles.
* **CLI Arguments**:
  * `--input`: Path to input CSV dataset (Required).
  * `--output`: Path to save updated CSV dataset (default: `dataset_updated.csv`).
  * `--old_label`: Specific label string to replace.
  * `--new_label`: Replacement label string.
* **Usage**:
  ```bash
  python clean_dataset_labels.py \
    --input "../../dataset/single-turn/banking77_test.csv" \
    --output "../../dataset/single-turn/banking77_test_clean.csv" \
    --old_label "reverted_card_payment?" \
    --new_label "reverted_card_payment"
  ```

---

### 5. `duplicate_and_rewrite.py`
* **Purpose**: Analyzes generated NLU datasets to detect structural duplicates or semantically repetitive sentences within the same intent and persona group. Uses an LLM to automatically rewrite duplicates into unique phrasing while preserving intent meaning.
* **Usage**:
  ```bash
  python duplicate_and_rewrite.py
  ```

---

### 6. `audio_recording.py`
* **Purpose**: Interactive CLI tool for recording telephony-grade audio samples (downsampled to 8kHz mono WAV files) for dataset utterances. Tracks progress via recorded UUIDs to support session resumption and saves recording metadata alongside audio files.
* **Usage**:
  ```bash
  python audio_recording.py
  ```

---

### 7. `.gen_banking77.py`
* **Purpose**: Internal benchmark generation utility supporting `zero-shot`, `one-shot`, and `few-shot` prompting techniques against local Ollama or OpenAI endpoints to generate synthetic datasets from reference CSV files.
* **Usage**:
  ```bash
  python .gen_banking77.py
  ```

---

## 🔄 Common Data Prep Workflow

1. **Clean Labels**: Run `clean_dataset_labels.py` to ensure dataset intent names match profile definitions.
2. **Assign UUIDs**: Run `add_uuid_to_dataset.py` to stamp each utterance with a tracking ID.
3. **Generate Synthetic Variants**: Run `generate_banking77_dataset.py` or `duplicate_and_rewrite.py` to build persona-rich test sets.
4. **Map IDs**: Run `add_numerical_label.py` to bind text categories to integer class indices.
