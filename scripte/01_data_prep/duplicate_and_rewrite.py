import csv
import json
import os
import argparse
import re
from pathlib import Path
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

# ==========================================
# CONFIGURATION
# ==========================================
SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR.parent / ".env"
load_dotenv(ENV_PATH)

# Set your similarity threshold (0.0 to 1.0)
# (Kept here in case you want to switch back to the TF-IDF hybrid workflow)
SIMILARITY_THRESHOLD = 0.80

# Initialize the OpenAI client (Targeting Ollama based on your .env)
client = OpenAI(
    api_key=os.getenv("OLLAMA_API_KEY2", "ollama"),
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
)

# Set the model you used to generate the data
MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "gpt-oss:120b")


# ==========================================
# LOGIC
# ==========================================

def parse_llm_json(raw_text: str) -> Dict[str, Any]:
    """Safely extracts JSON from the LLM output."""
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"rewrites": []}


def process_group_with_llm(label: str, persona: str, sentences: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Sends a batch of sentences to the LLM to identify wording duplicates and rewrite them."""

    # We only send the ID and the Text to the LLM to keep the prompt clean
    batch_json = json.dumps(sentences, indent=2)

    system_prompt = (
        "You are an expert NLU dataset curator. You are given a list of sentences that ALL share "
        "the same Intent and Persona. Because they share the same topic, they will naturally use similar words.\n\n"
        "YOUR TASK:\n"
        "1. Identify sentences that have virtually the EXACT SAME phrasing, sentence structure, or copy-pasted wording.\n"
        "2. Keep the first occurrence of a phrasing as the 'original'.\n"
        "3. For the duplicates, completely rewrite them to be highly diverse (change vocabulary, length, scenario, structure).\n"
        "4. DO NOT rewrite sentences that already have unique structures.\n\n"
        "You MUST return a JSON object with exactly this format:\n"
        "{\n"
        "  \"rewrites\": [\n"
        "    {\"id\": \"uuid-of-duplicate\", \"new_text\": \"The completely rewritten unique sentence\"}\n"
        "  ]\n"
        "}\n"
        "If there are no duplicates, return an empty array for 'rewrites'."
    )

    user_prompt = (
        f"Intent Label: '{label}'\n"
        f"Persona: '{persona}'\n\n"
        f"Sentences to Evaluate:\n{batch_json}\n\n"
        "Identify structural duplicates and provide the rewrites in JSON format now."
    )

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        raw_content = response.choices[0].message.content or "{}"
        return parse_llm_json(raw_content).get("rewrites", [])
    except Exception as e:
        print(f"  [API ERROR] Failed to process group {label}/{persona}: {e}")
        return []


def process_dataset(input_csv: str, output_csv: str):
    input_path = Path(input_csv)
    if not input_path.exists():
        print(f"[ERROR] File not found: {input_path}")
        return

    # 1. Load the dataset
    dataset = []
    with open(input_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            dataset.append(row)

    print(f"Loaded {len(dataset)} sentences.")

    # 2. Group by Label and Persona
    groups = {}
    for row in dataset:
        key = (row["label_text"], row["persona"])
        if key not in groups:
            groups[key] = []
        groups[key].append({"id": row["id"], "text": row["text"]})

    # Keep a dictionary of the main dataset for fast updating
    dataset_by_id = {row["id"]: row for row in dataset}
    total_rewrites = 0

    # 3. Ask the LLM to evaluate each group
    print(f"\nStarting LLM Evaluation using model: {MODEL_NAME} ...")
    for (label, persona), items in groups.items():
        if len(items) < 2:
            continue  # Can't have duplicates if there's only 1 sentence

        print(f"Analyzing Group: [{label}] - Persona: [{persona}] ({len(items)} sentences)")

        # Ask LLM to find duplicates and return rewrites
        rewrites = process_group_with_llm(label, persona, items)

        if rewrites:
            print(f"  -> LLM identified {len(rewrites)} structural duplicates to rewrite.")
            for rw in rewrites:
                uid = rw.get("id")
                new_text = rw.get("new_text")

                if uid and new_text and uid in dataset_by_id:
                    # old_text = dataset_by_id[uid]["text"]
                    # print(f"     [OLD]: {old_text}")
                    # print(f"     [NEW]: {new_text}")

                    dataset_by_id[uid]["text"] = new_text
                    total_rewrites += 1

    # 4. Save the updated dataset
    with open(output_csv, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        # We write the rows exactly in their original order
        writer.writerows(dataset)

    print("\n" + "=" * 50)
    print(f"LLM DEDUPLICATION COMPLETE!")
    print(f"Total Sentences Evaluated: {len(dataset)}")
    print(f"Total Sentences Rewritten: {total_rewrites}")
    print(f"Saved highly diverse dataset to: {output_csv}")
    print("=" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use an LLM to find and rewrite structural wording duplicates.")
    parser.add_argument("--input", type=str, required=True, help="Input CSV file")
    parser.add_argument("--output", type=str, default="dataset_llm_cleaned.csv", help="Output CSV file")

    args = parser.parse_args()
    process_dataset(args.input, args.output)