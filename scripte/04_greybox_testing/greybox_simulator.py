import os
import re
import csv
import json
import uuid
import random
import argparse
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from openai import OpenAI
from dotenv import load_dotenv

# Resolve .env relative to script location
SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR.parent.parent / ".env"
load_dotenv(ENV_PATH)


def get_next_incremented_dir(base_dir: str, prefix: str = "run", suffix: str = "") -> str:
    os.makedirs(base_dir, exist_ok=True)
    existing_runs = []
    for d in os.listdir(base_dir):
        if os.path.isdir(os.path.join(base_dir, d)) and d.startswith(f"{prefix}_"):
            match = re.search(rf"{prefix}_(\d+)", d)
            if match:
                existing_runs.append(int(match.group(1)))
    next_num = max(existing_runs) + 1 if existing_runs else 1
    clean_suffix = suffix.replace(":", "-").replace("/", "-")
    suffix_str = f"_{clean_suffix}" if clean_suffix else ""
    new_dir_name = f"{prefix}_{next_num:03d}{suffix_str}"
    new_dir_path = os.path.join(base_dir, new_dir_name)
    os.makedirs(new_dir_path, exist_ok=True)
    return new_dir_path


def load_local_csv(csv_path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    dataset = []
    unique_intents = set()
    with open(csv_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        id_col = next((col for col in ["id", "uuid", "sample_id"] if col in fieldnames), None)
        text_col = next((col for col in ["text", "utterance", "query"] if col in fieldnames), fieldnames[0])
        label_col = next((col for col in ["label_text", "category", "label", "intent"] if col in fieldnames),
                         fieldnames[1])
        for idx, row in enumerate(reader):
            text = (row.get(text_col) or "").strip()
            intent = (row.get(label_col) or "").strip()
            if not text or not intent:
                continue
            sample_id = row.get(id_col, "").strip() if id_col and row.get(id_col) else str(idx)
            dataset.append({"id": sample_id, "text": text, "label": intent})
            unique_intents.add(intent)
    return dataset, sorted(list(unique_intents))


@dataclass
class TurnLog:
    turn_number: int
    user_utterance: str
    assistant_response: str
    predicted_intent: Optional[str] = None
    timestamp: str = ""
    sim_prompt_tokens: int = 0
    sim_completion_tokens: int = 0
    bot_prompt_tokens: int = 0
    bot_completion_tokens: int = 0


@dataclass
class DialogueTrace:
    dialogue_id: str
    seed: int
    dialogue_index: int
    timestamp: str
    persona: str
    target_intent: str
    sim_model: str
    target_model: str
    total_turns: int
    status: str
    total_sim_prompt_tokens: int = 0
    total_sim_completion_tokens: int = 0
    total_bot_prompt_tokens: int = 0
    total_bot_completion_tokens: int = 0
    turns: List[Dict[str, Any]] = None


class DialogueLogger:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def save_trace(self, seed: int, dialogue_index: int, persona: str, target_intent: str,
                   sim_model: str, target_model: str, turns: List[TurnLog], status: str = "COMPLETED") -> str:
        dialogue_id = str(uuid.uuid4())
        trace = DialogueTrace(
            dialogue_id=dialogue_id,
            seed=seed,
            dialogue_index=dialogue_index,
            timestamp=datetime.now().isoformat(),
            persona=persona,
            target_intent=target_intent,
            sim_model=sim_model,
            target_model=target_model,
            total_turns=len(turns),
            status=status,
            total_sim_prompt_tokens=sum(t.sim_prompt_tokens for t in turns),
            total_sim_completion_tokens=sum(t.sim_completion_tokens for t in turns),
            total_bot_prompt_tokens=sum(t.bot_prompt_tokens for t in turns),
            total_bot_completion_tokens=sum(t.bot_completion_tokens for t in turns),
            turns=[asdict(turn) for turn in turns]
        )
        file_path = os.path.join(self.output_dir,
                                 f"dialogue_{persona.replace(' ', '_')}_{dialogue_index:03d}_{dialogue_id[:8]}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(asdict(trace), f, indent=2, ensure_ascii=False)
        return dialogue_id


class UserSimulator:
    def __init__(self, profile_data: Dict[str, Any], model_name: str = "gpt-oss:120b",
                 api_key: Optional[str] = None, base_url: Optional[str] = None, seed: int = 42):
        self.profile_data = profile_data
        self.model_name = os.getenv("SIMULATOR_MODEL_NAME", model_name)
        self.seed = seed
        self.client = OpenAI(
            api_key=os.getenv("SIMULATOR_API_KEY", api_key),
            base_url=os.getenv("SIMULATOR_BASE_URL", base_url)
        )

    def generate_user_turn(self, persona: str, target_intent: str, dialogue_history: List[Dict[str, str]]) -> Tuple[
        str, int, int]:
        persona_style = self.profile_data["personas"].get(persona, "Speak naturally.")
        forbidden_label_text = target_intent.replace("_", " ")

        system_prompt = self.profile_data["simulator_system_prompt"]
        system_prompt = system_prompt.replace("{target_intent}", target_intent) \
            .replace("{persona}", persona) \
            .replace("{persona_style}", persona_style) \
            .replace("{forbidden_label_text}", forbidden_label_text)

        sim_messages = [{"role": "system", "content": system_prompt}]
        if not dialogue_history:
            first_turn_prompt = self.profile_data["simulator_first_turn_prompt"].replace("{forbidden_label_text}",
                                                                                         forbidden_label_text)
            sim_messages.append({"role": "user", "content": first_turn_prompt})
        else:
            for turn in dialogue_history:
                role = "assistant" if turn["role"] == "user" else "user"
                sim_messages.append({"role": role, "content": turn["content"]})
            sim_messages.append({"role": "system",
                                 "content": "Generate ONLY the customer's next response. Do NOT write the bot's reply. Keep it short."})

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=sim_messages,
            temperature=0.1,
            seed=self.seed,
            stream=False
        )
        p_tok = getattr(response.usage, 'prompt_tokens', 0) if response.usage else 0
        c_tok = getattr(response.usage, 'completion_tokens', 0) if response.usage else 0
        return response.choices[0].message.content.strip(), p_tok, c_tok


class ExternalTargetClient:
    """GREYBOX MOCK TARGET: Makes HTTP requests to an external API to get the label, text, and completion signal."""

    def __init__(self, endpoint_url: str, intent_key: str, response_key: str, api_key: Optional[str] = None):
        self.endpoint_url = endpoint_url
        self.intent_key = intent_key
        self.response_key = response_key
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

    def process_user_turn(self, history: List[Dict[str, str]]) -> Tuple[Dict[str, Any], int, int]:
        payload = {"messages": history}
        try:
            response = requests.post(self.endpoint_url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            p_tok = data.get("usage", {}).get("prompt_tokens", 0)
            c_tok = data.get("usage", {}).get("completion_tokens", 0)

            return {
                "predicted_intent": data.get(self.intent_key, "unknown"),
                "response_text": data.get(self.response_key, ""),
                "dialogue_completed": data.get("dialogue_completed", False)
            }, p_tok, c_tok

        except Exception as e:
            print(f"\n[HTTP ERROR] Failed to reach Target API at {self.endpoint_url}: {e}")
            return {
                "predicted_intent": "api_error",
                "response_text": "I'm sorry, I am currently unreachable.",
                "dialogue_completed": True
            }, 0, 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Greybox Multi-Turn Simulator using an External Target Endpoint")
    parser.add_argument("--profile", type=str, default="../profiles/standard_en.json")
    parser.add_argument("--csv_path", type=str, default="../../dataset/single-turn/banking77_test_clean_labels.csv")
    parser.add_argument("--num_dialogues", type=int, default=5)
    parser.add_argument("--max_turns", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output_base_dir", type=str, default="../../logs/greybox/dialogues")
    parser.add_argument("--sim_model", type=str, default="gpt-oss:120b")

    # Arguments for External Target Server
    parser.add_argument("--target_url", type=str, default="http://localhost:8000/chat",
                        help="URL of external mock target server")
    parser.add_argument("--target_api_key", type=str, default=None, help="Optional API key for target server")
    parser.add_argument("--target_intent_key", type=str, default="predicted_intent",
                        help="JSON key used by target for label")
    parser.add_argument("--target_response_key", type=str, default="response_text",
                        help="JSON key used by target for text")
    parser.add_argument("--target_identifier", type=str, default="gpt-5.4-nano",
                        help="Name of target for logging purposes")

    args = parser.parse_args()

    with open(Path(args.profile), "r", encoding="utf-8") as pf:
        profile_data = json.load(pf)

    _, active_labels = load_local_csv(Path(args.csv_path))
    out_dir = get_next_incremented_dir(base_dir=args.output_base_dir, prefix="run", suffix=args.target_identifier)

    user_sim = UserSimulator(profile_data=profile_data, model_name=args.sim_model, seed=args.seed)
    target_bot = ExternalTargetClient(
        endpoint_url=args.target_url,
        intent_key=args.target_intent_key,
        response_key=args.target_response_key,
        api_key=args.target_api_key
    )

    logger = DialogueLogger(output_dir=out_dir)

    rng = random.Random(args.seed)
    personas = list(profile_data.get("personas", {}).keys())

    print(f"\n[GREYBOX SIMULATOR] Target API: {args.target_url} | Output: {out_dir}")

    for persona in personas:
        sampled_intents = active_labels.copy()
        rng.shuffle(sampled_intents)
        for idx in range(1, args.num_dialogues + 1):
            target_intent = sampled_intents[idx % len(sampled_intents)]
            dialogue_history = []
            turn_logs = []
            dialogue_status = "MAX_TURNS_REACHED"

            for turn_idx in range(1, args.max_turns + 1):
                u_text, sp, sc = user_sim.generate_user_turn(persona, target_intent, dialogue_history)
                dialogue_history.append({"role": "user", "content": u_text})

                bot_out, bp, bc = target_bot.process_user_turn(dialogue_history)
                pred_intent = bot_out.get("predicted_intent", "unknown")
                a_text = bot_out.get("response_text", "")
                is_completed = bot_out.get("dialogue_completed", False)

                dialogue_history.append({"role": "assistant", "content": a_text})

                turn_logs.append(TurnLog(
                    turn_number=turn_idx,
                    user_utterance=u_text,
                    assistant_response=a_text,
                    predicted_intent=pred_intent,
                    timestamp=datetime.now().isoformat(),
                    sim_prompt_tokens=sp,
                    sim_completion_tokens=sc,
                    bot_prompt_tokens=bp,
                    bot_completion_tokens=bc
                ))

                print(f"  [{persona} | Turn {turn_idx}] Bot predicted: '{pred_intent}' -> Response: {a_text[:40]}...")

                if is_completed:
                    print(f"  --> Dialogue marked completed by target server at turn {turn_idx}.")
                    dialogue_status = "COMPLETED"
                    break

            logger.save_trace(args.seed, idx, persona, target_intent, user_sim.model_name, args.target_identifier,
                              turn_logs, status=dialogue_status)