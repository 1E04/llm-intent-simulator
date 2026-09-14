import os
import json
import csv
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import concurrent.futures

SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR.parent.parent / ".env"
load_dotenv(ENV_PATH)

client = OpenAI(api_key=os.environ.get("SIMULATOR_API_KEY"), base_url=os.environ.get("SIMULATOR_BASE_URL"))

CSV_PATH = SCRIPT_DIR.parent.parent / "dataset" / "single-turn" / "banking77_test_labels_clean.csv"
OUTPUT_PATH = SCRIPT_DIR.parent / "profiles" / "intent_definitions.json"

def generate_definition(intent, examples):
    prompt = f"""You are an expert conversational AI designer for a banking voice bot.
I will give you an intent label and some real user utterances.
Your task is to write a concise, 1-sentence definition (max 20 words) describing the semantic meaning of this intent.
Focus on the core business logic or the specific problem the user has. Do not simply restate the examples.

Intent Label: {intent}
Examples:
"""
    for ex in examples:
        prompt += f"- {ex}\n"

    try:
        response = client.chat.completions.create(
            model="gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=256
        )
        return intent, response.choices[0].message.content.strip()
    except Exception as e:
        print(f"ERROR calling LLM for {intent}: {e}")
        # Return a temporary error string so we know it failed, instead of silently falling back
        return intent, f"ERROR: {e}"

def main():
    if not CSV_PATH.exists():
        print(f"Error: Dataset not found at {CSV_PATH}")
        return

    # 1. Load CSV
    intent_to_examples = {}
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # Use appropriate column names if they differ
        label_col = next((col for col in ["label_text", "category", "label", "intent", "target"] if col in reader.fieldnames), None)
        text_col = next((col for col in ["text", "utterance", "query", "sentence"] if col in reader.fieldnames), None)
        
        if not label_col or not text_col:
            print("Could not identify label or text columns in CSV.")
            return

        for row in reader:
            intent = row.get(label_col)
            text = row.get(text_col)
            if intent and text:
                intent = intent.strip()
                if intent not in intent_to_examples:
                    intent_to_examples[intent] = []
                intent_to_examples[intent].append(text.strip())
                
    print(f"Found {len(intent_to_examples)} unique intents.")

    # 2. Generate definitions
    final_output = {}
    
    def process_intent(intent):
        # take up to 5 examples for context to give the LLM a good semantic understanding
        examples = intent_to_examples[intent][:5] 
        _, definition = generate_definition(intent, examples)
        
        # take 2 examples for the few-shot prompt
        few_shot_examples = intent_to_examples[intent][:2]
        
        return intent, {
            "definition": definition,
            "examples": few_shot_examples
        }

    print("Generating semantic definitions via OpenAI (gpt-oss-120b)...")
    # Reduced max_workers to 1 because local LLMs often crash or time out with concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_to_intent = {executor.submit(process_intent, intent): intent for intent in intent_to_examples}
        for future in concurrent.futures.as_completed(future_to_intent):
            intent, result = future.result()
            final_output[intent] = result
            print(f"Finished: {intent} -> {result['definition']}")

    # 3. Save
    os.makedirs(OUTPUT_PATH.parent, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)
        
    print(f"\nDone! Saved {len(final_output)} definitions to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
