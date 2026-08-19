import csv
import json
import os
import re
import time
import random
import uuid
from pathlib import Path
from typing import List, Tuple, Dict
from collections import defaultdict
from openai import OpenAI
from dotenv import load_dotenv

# ==========================================
# SAFELY LOAD .ENV FILE
# ==========================================
# Dies sucht die .env Datei im übergeordneten Verzeichnis (Root)
SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR.parent.parent / ".env"
load_dotenv(ENV_PATH)

# ==========================================
# KONFIGURATION
# ==========================================
API_KEY = os.getenv("OPENAI_API_KEY", "your-api-key-here")
BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-oss:120b")

CSV_FILE_PATH = Path("./dataset/single-turn/banking77_test_clean_labels.csv")
OUTPUT_FILE = Path(f"./dataset/single-turn/banking77_personas_{MODEL_NAME.replace('/', '-')}.csv")

PROMPTING_TECHNIQUE = "few-shot"
NUM_SAMPLES_PER_PERSONA = 6  # 6 Durchläufe pro Persona (6x6 = 36 pro Intent)

# ==========================================
# DIE 6 PERSONA ARCHETYPEN (ENGLISH)
# ==========================================
PERSONAS = {
    "angry_layperson": "Angry layperson: You are extremely angry, use slang, complain loudly, and do not use any technical banking terms.",
    "panicking_emergency": "Stressed emergency: You are in absolute panic, write in a telegraphic style, use short choppy sentences, and omit punctuation.",
    "polite_expert": "Polite expert: You remain neutral, highly formal, use correct financial terminology, and ensure perfect, elaborate sentence structure.",
    "gen_z_slang": "Gen-Z customer: You are very relaxed, use modern youth language, lots of internet slang, text abbreviations, and emojis.",
    "non_native_speaker": "Non-native speaker: You are very friendly but use extremely simple words, broken English, and make obvious grammar mistakes. Also sometimes just forget one word and skip it.",
    "short_wording": "Short wording: You write extremely concise, minimalist queries using only keywords or short fragments (2-5 words), omitting full sentence structure."
}


def load_local_csv_and_group(csv_path: Path) -> Tuple[Dict[str, List[str]], List[str], Dict[str, str]]:
    if not csv_path.exists():
        raise FileNotFoundError(f"File {csv_path} not found!")

    print(f"Loading original CSV: {csv_path}...")
    intent_to_examples = defaultdict(list)
    intent_to_numeric = {}  # NEU: Speichert das Mapping von Text zu Zahl

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames if reader.fieldnames else []
        text_col = "text" if "text" in fieldnames else fieldnames[0]
        label_col = "label_text" if "label_text" in fieldnames else (
            "category" if "category" in fieldnames else fieldnames[1])

        # NEU: Finde die Spalte für das numerische Label
        num_col = next((col for col in ["label", "label_id", "intent_id"] if col in fieldnames), None)

        for row in reader:
            text = row[text_col].strip()
            intent = row[label_col].strip()
            intent_to_examples[intent].append(text)

            # NEU: Mapping von Intent-String zur numerischen ID
            if num_col and intent not in intent_to_numeric:
                intent_to_numeric[intent] = row[num_col].strip()

    intents_list = sorted(list(intent_to_examples.keys()))
    print(f"CSV loaded. Intents found: {len(intents_list)}")
    return intent_to_examples, intents_list, intent_to_numeric


def build_persona_prompts(intent: str, persona_key: str, persona_desc: str, real_examples: List[str], technique: str) -> \
Tuple[str, str]:
    # Strictly English System Prompt
    system_prompt = (
        "You are a customer interacting with a banking support system. "
        "You must strictly adopt the following persona and tone of voice:\n"
        f"'{persona_desc}'\n\n"
        "Do not sound like an AI assistant. Fully immerse yourself in this character. "
        "Write strictly in English."
    )

    # User Prompt
    base_instruction = (
        f"Your specific banking problem/intent is: '{intent}'.\n"
        f"Write EXACTLY ONE realistic support message expressing this problem acting entirely as the persona '{persona_key}'. "
        f"Do NOT explicitly mention the technical category name '{intent}' in your sentence. Keep it realistic and to the point. Don't use Emojis"
    )

    if technique == "zero-shot":
        user_prompt = base_instruction

    elif technique == "one-shot":
        example = random.choice(real_examples) if real_examples else "I have an issue with this feature."
        user_prompt = (
            f"{base_instruction}\n\n"
            f"Here is an example of the factual content (but NOT your persona style):\n"
            f"Example: \"{example}\"\n\n"
            f"Now, generate your completely new sentence, rewritten entirely in the style of your persona:"
        )

    elif technique == "few-shot":
        examples_sample = random.sample(real_examples, min(3, len(real_examples))) if real_examples else []
        examples_formatted = "\n".join([f"- \"{ex}\"" for ex in examples_sample])

        user_prompt = (
            f"{base_instruction}\n\n"
            f"Here are a few factual examples of this issue (ignore their style, just look at the facts):\n"
            f"{examples_formatted}\n\n"
            f"Now, generate your unique sentence, strictly using the vocabulary and style of your persona:"
        )
    else:
        user_prompt = base_instruction

    return system_prompt, user_prompt


def generate_persona_dataset(intent_to_examples: Dict[str, List[str]], intents_list: List[str],
                             intent_to_numeric: Dict[str, str], output_path: Path):
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    file_exists = output_path.exists()
    with open(output_path, mode="a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            # NEU: Spalte 'label' hinzugefügt
            writer.writerow(["id", "text", "label", "label_text", "persona"])

        print(f"Starting Persona generation via {PROMPTING_TECHNIQUE}...")
        total_intents = len(intents_list)

        for idx, intent in enumerate(intents_list):
            real_examples = intent_to_examples.get(intent, [])

            # NEU: Hole das numerische Label aus dem Mapping (Fallback ist "-1", falls nicht vorhanden)
            numeric_label = intent_to_numeric.get(intent, "-1")

            # Iterate over the 6 personas
            for persona_key, persona_desc in PERSONAS.items():

                # Generate 5 unique sentences per persona
                for sample_idx in range(NUM_SAMPLES_PER_PERSONA):

                    system_prompt, user_prompt = build_persona_prompts(
                        intent, persona_key, persona_desc, real_examples, PROMPTING_TECHNIQUE
                    )

                    try:
                        response = client.chat.completions.create(
                            model=MODEL_NAME,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            temperature=0.85,  # Higher temperature for better variance
                            #max_tokens=512
                            max_completion_tokens=1024
                        )

                        generated_text = response.choices[0].message.content.strip()
                        # Clean up surrounding quotes if the LLM adds them
                        generated_text = re.sub(r'^["\']|["\']$', '', generated_text)

                        # Erzeuge eine eindeutige UUID für jeden Satz
                        sample_id = str(uuid.uuid4())

                        writer.writerow([sample_id, generated_text, numeric_label, intent, persona_key])
                        f.flush()

                    except Exception as e:
                        print(
                            f"\nError at Intent '{intent}' (Persona: {persona_key}, Sample: {sample_idx + 1}): {str(e)}")
                        time.sleep(2)

            print(f"\rProgress: {idx + 1}/{total_intents} Intents (36 sentences each) processed...", end="", flush=True)

    print(f"\n\nGeneration complete! Persona dataset saved to: {output_path}")


if __name__ == "__main__":
    intent_to_examples, all_intents, intent_to_numeric = load_local_csv_and_group(CSV_FILE_PATH)
    generate_persona_dataset(intent_to_examples, all_intents, intent_to_numeric, OUTPUT_FILE)