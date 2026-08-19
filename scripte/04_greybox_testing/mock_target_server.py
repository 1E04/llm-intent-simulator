import os
import json
import csv
from pathlib import Path
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from openai import OpenAI
from dotenv import load_dotenv

# ==========================================
# 1. SETUP & CONFIGURATION
# ==========================================
SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR.parent.parent / ".env"
load_dotenv(ENV_PATH)

app = FastAPI(title="Greybox Mock Target API")

# API Configuration
API_KEY = os.getenv("TARGET_API_KEY", os.getenv("OPENAI_API_KEY", "dummy_key"))
BASE_URL = os.getenv("TARGET_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("TARGET_MODEL_NAME", "gpt-5.4-nano")
CSV_PATH = SCRIPT_DIR.parent.parent / "dataset" / "single-turn" / "banking77_test_clean_labels.csv"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


# ==========================================
# 2. HELPER: LOAD ALLOWED LABELS
# ==========================================
def get_allowed_labels(csv_path: Path) -> List[str]:
    """Extracts unique intents from the dataset to restrict the bot's classification."""
    if not csv_path.exists():
        print(f"[WARNING] CSV not found at {csv_path}. Falling back to empty list.")
        return []

    unique_intents = set()
    with open(csv_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        label_col = next((col for col in ["label_text", "category", "label", "intent"] if col in fieldnames), None)

        if label_col:
            for row in reader:
                intent = (row.get(label_col) or "").strip()
                if intent:
                    unique_intents.add(intent)

    return sorted(list(unique_intents))


ALLOWED_LABELS = get_allowed_labels(CSV_PATH)


# ==========================================
# 3. PYDANTIC DATA MODELS
# ==========================================
class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


# ==========================================
# 4. API ENDPOINT
# ==========================================
@app.post("/chat")
def generate_bot_response(request: ChatRequest):
    """
    Receives dialogue history, internally calculates top 2 candidate intents with confidence scores,
    and returns ONLY the top predicted label, spoken response, and completion flag.
    """
    try:
        # System prompt requiring top-2 intents and confidence assessment
        system_prompt = (
            "You are an intelligent banking voice bot.\n"
            "Analyze the user's input across the conversation history and identify the top 2 most likely underlying intents from the allowed list, along with a confidence score (0.00 to 1.00) for each.\n\n"
            f"Allowed Intent Labels: {ALLOWED_LABELS}\n\n"
            "BEHAVIOR RULES:\n"
            "1. If your confidence in the top intent is less than 0.9, or the gap between Top 1 and Top 2 is less than 0.2: Your `response_text` MUST be a clarifying question to help narrow down the user's intent.\n"
            "2. If you are highly confident (>= 0.9), provide a concise final resolution/confirmation in your `response_text`.\n\n"
            "You MUST respond in valid JSON format with exactly TWO keys:\n"
            "1. \"top_2_intents\": array of objects, e.g. [{\"intent\": \"label_name\", \"confidence\": 0.90}, ...]\n"
            "2. \"response_text\": string (your spoken response back to the user)"
        )

        api_messages = [{"role": "system", "content": system_prompt}]
        api_messages.extend([{"role": msg.role, "content": msg.content} for msg in request.messages])

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=api_messages,
            response_format={"type": "json_object"},
            temperature=0.1
        )

        raw_content = response.choices[0].message.content or "{}"
        parsed_data = json.loads(raw_content)

        # Calculate Confidence & Completion Logic internally
        top_2_intents = parsed_data.get("top_2_intents", [])
        predicted_intent = "unknown"
        dialogue_completed = False

        if isinstance(top_2_intents, list) and len(top_2_intents) > 0 and isinstance(top_2_intents[0], dict):
            predicted_intent = top_2_intents[0].get("intent", "unknown")
            try:
                conf_1 = float(top_2_intents[0].get("confidence", 0.0))
                conf_2 = float(top_2_intents[1].get("confidence", 0.0)) if len(top_2_intents) > 1 else 0.0

                # Check target threshold logic
                if conf_1 >= 0.90 and (conf_1 - conf_2) >= 0.2:
                    dialogue_completed = True
            except (ValueError, TypeError):
                dialogue_completed = False

        prompt_tokens = response.usage.prompt_tokens if response.usage else 0
        completion_tokens = response.usage.completion_tokens if response.usage else 0

        return {
            "predicted_intent": predicted_intent,
            "response_text": parsed_data.get("response_text", ""),
            "dialogue_completed": dialogue_completed,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens
            }
        }

    except Exception as e:
        print(f"[ERROR] Mock Target API failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 5. RUN SERVER
# ==========================================
if __name__ == "__main__":
    print(f"\n🚀 Starting Greybox Mock Target Server...")
    print(f"📦 Model: {MODEL_NAME}")
    print(f"🗂️  Loaded {len(ALLOWED_LABELS)} labels from dataset.")
    print(f"🌐 Listening on http://localhost:8000/chat\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)