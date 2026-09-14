import csv
import json
import os
import re
import time
import uuid
import argparse
from pathlib import Path
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

# ==========================================
# SAFELY LOAD .ENV FILE
# ==========================================
SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR.parent.parent / ".env"
load_dotenv(ENV_PATH)

# ==========================================
# CONFIGURATION FROM .ENV
# ==========================================
SIMULATOR_BASE_URL = os.getenv("SIMULATOR_BASE_URL", os.getenv("TARGET_BASE_URL", "https://api.openai.com/v1"))
SIMULATOR_API_KEY = os.getenv("SIMULATOR_API_KEY", os.getenv("TARGET_API_KEY", os.getenv("OPENAI_API_KEY", "dummy")))
SIMULATOR_MODEL_NAME = os.getenv("SIMULATOR_MODEL_NAME", "gpt-5.4-nano")


def generate_ood_dataset(profile_path: Path, output_path: Path, num_samples: int = 50):
    if not profile_path.exists():
        raise FileNotFoundError(f"Profile file not found: {profile_path}")

    with open(profile_path, "r", encoding="utf-8") as f:
        profile_data = json.load(f)

    client = OpenAI(api_key=SIMULATOR_API_KEY, base_url=SIMULATOR_BASE_URL)

    persona_name = "Chatterbox"
    persona_desc = profile_data.get("personas", {}).get(persona_name, "You are extremely chatty but completely off-topic.")
    sim_system_prompt = profile_data.get("simulator_system_prompt", "").format(
        target_intent="out_of_domain",
        persona=persona_name,
        persona_style=persona_desc
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = output_path.exists()

    print(f"\n=======================================================")
    print(f" GENERATING SINGLE-TURN OOD DATASET")
    print(f" Profile: {profile_path.name}")
    print(f" Persona: {persona_name}")
    print(f" Simulator Model: {SIMULATOR_MODEL_NAME}")
    print(f" Target Output CSV: {output_path}")
    print(f" Total Samples to Generate: {num_samples}")
    print(f"=======================================================\n")

    with open(output_path, mode="w" if not file_exists else "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["id", "text", "label", "label_text", "persona"])

        for i in range(1, num_samples + 1):
            user_prompt = (
                f"Generate 1 realistic spoken customer utterance (turn 1) where you talk about something completely off-topic "
                f"(e.g. weather, baking, pets, travel, hobbies). "
                f"STRICT NEGATIVE PROMPT: Do NOT mention any banking, financial, card, account, or money terms under any circumstances. "
                f"Utterance #{i}:"
            )

            try:
                res = client.chat.completions.create(
                    model=SIMULATOR_MODEL_NAME,
                    messages=[
                        {"role": "system", "content": sim_system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.85,
                    max_completion_tokens=250
                )
                generated_text = (res.choices[0].message.content or "").strip().strip('"')
                generated_text = re.sub(r'^["\']|["\']$', '', generated_text)

                if generated_text:
                    sample_id = str(uuid.uuid4())
                    # Standard Single-Turn CSV Row Schema
                    writer.writerow([sample_id, generated_text, "77", "out_of_domain", persona_name])
                    f.flush()
                    print(f"[{i:02d}/{num_samples:02d}] Generated: \"{generated_text[:65]}...\"")

            except Exception as e:
                print(f"[{i:02d}/{num_samples:02d}] API Error: {e}")
                time.sleep(1)

    print(f"\nOOD Dataset generation complete! Saved to: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Single-Turn Out-of-Boundary CSV Dataset")
    parser.add_argument("--profile", type=str, default="../profiles/out_of_boundary_en.json")
    parser.add_argument("--num_samples", type=int, default=50)
    parser.add_argument("--output_csv", type=str, default="../../dataset/single-turn/banking77_ood_chatterbox.csv")

    args = parser.parse_args()

    profile_p = Path(args.profile)
    if not profile_p.is_absolute():
        profile_p = SCRIPT_DIR.parent / args.profile.lstrip("../")

    output_p = Path(args.output_csv)
    if not output_p.is_absolute():
        output_p = SCRIPT_DIR.parent.parent / "dataset" / "single-turn" / output_p.name

    generate_ood_dataset(profile_p, output_p, num_samples=args.num_samples)
