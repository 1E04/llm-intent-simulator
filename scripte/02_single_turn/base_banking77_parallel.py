import argparse
import csv
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Tuple, Dict, Any
from collections import defaultdict
from openai import OpenAI
from dotenv import load_dotenv

# ==========================================
# SAFELY LOAD .ENV FILE
# ==========================================
# Dies sucht die .env Datei im übergeordneten Verzeichnis (Root)
SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR.parent / ".env"
load_dotenv(ENV_PATH)

# ==========================================
# MODELL-KONFIGURATIONEN (REGISTRY)
# ==========================================

MODEL_CONFIGS: Dict[str, Dict[str, Any]] = {
    "mistral-small:24b": {
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        "api_key": os.getenv("OLLAMA_API_KEY", "ollama"),
        "model_name": "mistral-small:24b",
        "max_workers": 1,
    },
    "phi4:14b": {
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        "api_key": os.getenv("OLLAMA_API_KEY", "ollama"),
        "model_name": "phi4:14b",
        "max_workers": 1,
    },
    "gpt-oss": {
        "base_url": os.getenv("OLLAMA_BASE_URL2", "http://localhost:11434/v1"),
        "api_key": os.getenv("OLLAMA_API_KEY2", "ollama"),
        "model_name": "openai/gpt-oss-120b",
        "max_workers": 1,
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key": os.getenv("GEMINI_API_KEY"),
        "model_name": "gemini-3.1-flash-lite",
        "max_workers": 1,
    },
    "openai-nano": {
        "base_url": "https://api.openai.com/v1",
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model_name": "gpt-5.4-nano",
        "max_workers": 1,
    }
}

DEFAULT_CSV_PATH = Path("../../dataset/single-turn/banking77_personas_phi4:14b_clean.csv")
FILE_LOCK = threading.Lock()
PRINT_LOCK = threading.Lock()

def safe_print(*args, **kwargs):
    """Thread-sichere Ausgabe im Terminal."""
    with PRINT_LOCK:
        print(*args, **kwargs)


# ==========================================
# DATENSET & PROMPT HELPERS
# ==========================================
def load_local_csv(csv_path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not csv_path.exists():
        raise FileNotFoundError(f"Die Datei {csv_path} wurde nicht gefunden!")

    safe_print(f"Lade lokale CSV-Datei: {csv_path}...")
    dataset = []
    unique_intents = set()

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames if reader.fieldnames else []

        id_col = None
        for col in ["id", "uuid", "sample_id"]:
            if col in fieldnames:
                id_col = col
                break

        text_col = "text" if "text" in fieldnames else fieldnames[0]
        label_col = "label_text" if "label_text" in fieldnames else (
            "category" if "category" in fieldnames else fieldnames[1])

        for idx, row in enumerate(reader):
            text = row[text_col].strip()
            intent = row[label_col].strip()
            sample_id = row[id_col].strip() if id_col and row.get(id_col) else str(idx)

            dataset.append({"id": sample_id, "text": text, "label": intent})
            unique_intents.add(intent)

    intents_list = sorted(list(unique_intents))
    safe_print(f"CSV geladen. Einträge: {len(dataset)} | Gefundene Intents: {len(intents_list)}")
    return dataset, intents_list


def build_system_prompt(intents_list: List[str]) -> str:
    formatted_intents = '", "'.join(intents_list)
    return (
        f'Classify the following sentence into exactly one of these categories:\n'
        f'["{formatted_intents}"]\n\n'
        'Output ONLY the plain label string from the list. Do not add markdown, quotes, or any extra explanation.'
    )


def get_messages(system_prompt: str, text: str) -> list:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Sentence to classify: {text}"}
    ]


# ==========================================
# WORKER FÜR EINZELNE ANFRAGEN
# ==========================================
def process_single_item(client: OpenAI, item: Dict[str, Any], idx: int, system_prompt: str, model_name: str) -> Dict[str, Any]:
    sample_id = item.get("id", idx)
    text = item.get("text", "")
    true_intent = item.get("label", "")
    predicted_intent = "error"
    prompt_tok = 0
    comp_tok = 0

    messages = get_messages(system_prompt, text)

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.0,
            #max_tokens=1024,
            max_completion_tokens=1024,
            stream=False,
        )

        raw_content = response.choices[0].message.content or ""
        raw_content = raw_content.strip()

        if not raw_content and hasattr(response.choices[0].message, "reasoning"):
            raw_content = ""

        predicted_intent = re.sub(r'[^a-z_]', '', raw_content.lower())

        if hasattr(response, 'usage') and response.usage:
            prompt_tok = getattr(response.usage, 'prompt_tokens', 0) or 0
            comp_tok = getattr(response.usage, 'completion_tokens', 0) or 0

        if not predicted_intent:
            predicted_intent = "error"

    except Exception as e:
        # === HIER DAS LOGGING EINFÜGEN ===
        safe_print(f"\n[ERROR - {model_name}] ID {sample_id}: {type(e).__name__} -> {e}")
        predicted_intent = "error"

    return {
        "id": sample_id,
        "text": text,
        "true_intent": true_intent,
        "predicted_intent": predicted_intent,
        "prompt_tokens": prompt_tok,
        "completion_tokens": comp_tok,
    }

# ==========================================
# PARALLELE KLASSIFIKATION PRO MODELL
# ==========================================
def classify_texts_parallel(
        config_key: str,
        data_list: List[Dict[str, str]],
        intents_list: List[str],
        csv_path: Path
) -> Path:
    config = MODEL_CONFIGS[config_key]
    model_alias = config_key
    model_name = config["model_name"]
    max_workers = config.get("max_workers", 5)

    safe_model_filename = model_alias.replace(":", "_").replace("/", "_")
    output_path = Path(
        f"../../logs/single-turn/synthetic-dataset/phi4/results-{safe_model_filename}-{csv_path.stem}.jsonl")
    client = OpenAI(api_key=config["api_key"], base_url=config["base_url"])
    system_prompt = build_system_prompt(intents_list)

    # Checkpoint-Logik
    processed_ids = set()
    processed_texts = set()
    if output_path.exists():
        safe_print(f"[{model_alias}] Checkpoint gefunden in {output_path}...")
        with open(output_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        if data.get("predicted_intent") != "error":
                            if "id" in data:
                                processed_ids.add(str(data["id"]))
                            if "text" in data:
                                processed_texts.add(data["text"])
                    except (json.JSONDecodeError, KeyError):
                        continue
        safe_print(f"[{model_alias}] {len(processed_ids)} bereits verarbeitete Datensätze werden übersprungen.")

    to_process = []
    for idx, item in enumerate(data_list):
        item_id = str(item.get("id", ""))
        item_text = item.get("text", "")
        if item_id in processed_ids or (not item_id and item_text in processed_texts):
            continue
        to_process.append((idx, item))

    total_to_process = len(to_process)

    if total_to_process == 0:
        safe_print(f"[{model_alias}] Alle Datensätze bereits verarbeitet!")
        return output_path

    safe_print(f"[{model_alias}] Starte Klassifikation für {total_to_process} Elemente (Workers: {max_workers})...")
    start_time = time.time()
    completed = 0

    with open(output_path, "a", encoding="utf-8") as f:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_item = {
                executor.submit(process_single_item, client, item, idx, system_prompt, model_name): idx
                for idx, item in to_process
            }

            for future in as_completed(future_to_item):
                record = future.result()

                with FILE_LOCK:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    f.flush()

                completed += 1
                # Alle 10 Elemente oder am Ende Fortschritt ausgeben
                if completed % 50 == 0 or completed == total_to_process:
                    elapsed = time.time() - start_time
                    speed = completed / elapsed if elapsed > 0 else 0
                    time_left = (total_to_process - completed) / speed if speed > 0 else 0
                    safe_print(
                        f"[{model_alias}] Fortschritt: {completed}/{total_to_process} "
                        f"({completed / total_to_process * 100:.1f}%) | "
                        f"Geschwindigkeit: {speed:.1f} req/s | "
                        f"Verbleibend: {round(time_left, 1)}s"
                    )

    safe_print(f"[{model_alias}] Klassifikation abgeschlossen in {round(time.time() - start_time, 2)}s.")
    return output_path


# ==========================================
# EVALUATION
# ==========================================
def evaluate_results(file_path: Path, model_alias: str) -> None:
    if not file_path.exists():
        safe_print(f"Evaluierung fehlgeschlagen: {file_path} existiert nicht.")
        return

    global_correct, global_incorrect, global_errors, global_total = 0, 0, 0, 0
    category_stats = defaultdict(lambda: {"correct": 0, "total": 0})

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                pred = str(data.get("predicted_intent", "error")).strip().lower()
                true = str(data.get("true_intent", "")).strip().lower()

                global_total += 1
                category_stats[true]["total"] += 1

                if pred == "error":
                    global_errors += 1
                elif pred == true:
                    global_correct += 1
                    category_stats[true]["correct"] += 1
                else:
                    global_incorrect += 1
            except json.JSONDecodeError:
                continue

    global_accuracy = (global_correct / global_total * 100) if global_total > 0 else 0.0

    out_msg = (
            f"\n" + "=" * 50 + "\n"
                               f"{f'EVALUIERUNGSERGEBNISSE: {model_alias.upper()}':^50}\n"
                               f"=" * 50 + "\n"
                                           f"Gesamte Datensätze:   {global_total}\n"
                                           f"Korrekt klassifiziert: {global_correct}\n"
                                           f"Falsch klassifiziert:  {global_incorrect}\n"
                                           f"API-/Parsing-Fehler:   {global_errors}\n"
                                           f"-" * 50 + "\n"
                                                       f"Gesamtgenauigkeit:     {global_accuracy:.2f}%\n"
                                                       f"=" * 50 + "\n"
    )
    safe_print(out_msg)


def run_model_pipeline(model_key: str, local_data: List[Dict[str, str]], all_intents: List[str], csv_path: Path):
    """Führt die komplette Pipeline für ein einzelnes Modell aus."""
    output_file = classify_texts_parallel(model_key, local_data, all_intents, csv_path)
    evaluate_results(output_file, model_key)


# ==========================================
# CLI MAIN RUNNER
# ==========================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-LLM Text Classification Evaluator")
    parser.add_argument(
        "-m", "--models",
        nargs="+",
        choices=list(MODEL_CONFIGS.keys()) + ["all"],
        default=["qwen3.6"],
        help="Verfügbare Modelle auswählen (z.B. --models phi4 gemini oder --models all)"
    )
    parser.add_argument(
        "--csv",
        type=str,
        default=str(DEFAULT_CSV_PATH),
        help="Pfad zur CSV-Datei"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Listet alle verfügbaren Modell-Konfigurationen auf"
    )

    args = parser.parse_args()

    if args.list:
        print("\nVerfügbare Modell-Keys in MODEL_CONFIGS:")
        for key, cfg in MODEL_CONFIGS.items():
            print(f"  - {key:<15} -> Model: {cfg['model_name']} | Base-URL: {cfg['base_url']}")
        sys.exit(0)

    csv_path = Path(args.csv)
    local_data, all_intents = load_local_csv(csv_path)

    selected_models = list(MODEL_CONFIGS.keys()) if "all" in args.models else args.models

    safe_print(f"\nFolgende Modelle werden PARALLEL evaluiert: {', '.join(selected_models)}\n")

    # Startet alle ausgewählten Modelle zeitgleich in separaten Threads
    with ThreadPoolExecutor(max_workers=len(selected_models)) as executor:
        futures = [
            executor.submit(run_model_pipeline, model_key, local_data, all_intents, csv_path)
            for model_key in selected_models
        ]

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                safe_print(f"Ein Fehler ist bei der Modellausführung aufgetreten: {e}")