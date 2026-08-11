import os
import re
import csv
import json
import uuid
import random
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from openai import OpenAI
from dotenv import load_dotenv

# Safely resolve the .env file relative to THIS script's actual location
SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR.parent / ".env"
load_dotenv(ENV_PATH)


# =====================================================================
# 1. DIRECTORY HELPERS
# =====================================================================

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


# =====================================================================
# 2. HELPER FUNCTIONS & DATA STRUCTURES
# =====================================================================

def load_local_csv(csv_path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not csv_path.exists():
        raise FileNotFoundError(f"Die CSV-Datei wurde nicht gefunden: {csv_path}")

    print(f"[DataLoader] Lade lokale CSV-Datei: {csv_path}...")
    dataset: List[Dict[str, str]] = []
    unique_intents = set()

    with open(csv_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames if reader.fieldnames else []

        if not fieldnames:
            raise ValueError(f"Die CSV-Datei {csv_path} ist leer oder hat keine Header-Zeile!")

        id_col = next((col for col in ["id", "uuid", "sample_id"] if col in fieldnames), None)
        text_col = next((col for col in ["text", "utterance", "query", "sentence"] if col in fieldnames), fieldnames[0])
        label_col = next((col for col in ["label_text", "category", "label", "intent", "target"] if col in fieldnames),
                         fieldnames[1] if len(fieldnames) > 1 else fieldnames[0])

        for idx, row in enumerate(reader):
            raw_text = row.get(text_col) or ""
            raw_label = row.get(label_col) or ""

            text = raw_text.strip()
            intent = raw_label.strip()

            if not text or not intent:
                continue

            sample_id = row.get(id_col, "").strip() if id_col and row.get(id_col) else str(idx)

            dataset.append({"id": sample_id, "text": text, "label": intent})
            unique_intents.add(intent)

    intents_list = sorted(list(unique_intents))
    print(f"[DataLoader] CSV erfolgreich geladen. Einträge: {len(dataset)} | Eindeutige Intents: {len(intents_list)}")

    return dataset, intents_list


def parse_llm_json(raw_text: str) -> Dict[str, Any]:
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "top_3_intents": [],
            "predicted_intent": "parsing_error",
            "response_text": raw_text,
            "dialogue_completed": False
        }


@dataclass
class TurnLog:
    turn_number: int
    user_utterance: str
    assistant_response: str
    predicted_intent: Optional[str] = None
    top_3_intents: List[Dict[str, Any]] = None  # Tracks confidence N-best list
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

    def save_trace(
            self,
            seed: int,
            dialogue_index: int,
            persona: str,
            target_intent: str,
            sim_model: str,
            target_model: str,
            turns: List[TurnLog],
            status: str = "COMPLETED"
    ) -> str:
        dialogue_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        tot_sim_p = sum(t.sim_prompt_tokens for t in turns)
        tot_sim_c = sum(t.sim_completion_tokens for t in turns)
        tot_bot_p = sum(t.bot_prompt_tokens for t in turns)
        tot_bot_c = sum(t.bot_completion_tokens for t in turns)

        trace = DialogueTrace(
            dialogue_id=dialogue_id,
            seed=seed,
            dialogue_index=dialogue_index,
            timestamp=timestamp,
            persona=persona,
            target_intent=target_intent,
            sim_model=sim_model,
            target_model=target_model,
            total_turns=len(turns),
            status=status,
            total_sim_prompt_tokens=tot_sim_p,
            total_sim_completion_tokens=tot_sim_c,
            total_bot_prompt_tokens=tot_bot_p,
            total_bot_completion_tokens=tot_bot_c,
            turns=[asdict(turn) for turn in turns]
        )

        file_path = os.path.join(
            self.output_dir,
            f"dialogue_{persona.replace(' ', '_')}_{dialogue_index:03d}_{dialogue_id[:8]}.json"
        )
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(asdict(trace), f, indent=2, ensure_ascii=False)

        return dialogue_id


# =====================================================================
# 3. REPRODUCIBLE LABEL SAMPLER
# =====================================================================

class ReproducibleLabelSampler:
    def __init__(self, labels: List[str], seed: int = 42):
        self.labels = labels
        self.seed = seed

    def get_labels_for_run(self, num_samples: int) -> List[str]:
        rng = random.Random(self.seed)
        sampled_labels = []
        while len(sampled_labels) < num_samples:
            shuffled = self.labels.copy()
            rng.shuffle(shuffled)
            sampled_labels.extend(shuffled)
        return sampled_labels[:num_samples]


# =====================================================================
# 4. AGENTS WITH INDEPENDENT API CONFIGURATIONS
# =====================================================================

class UserSimulator:
    def __init__(
            self,
            profile_data: Dict[str, Any],
            model_name: str = "gpt-oss:120b",
            api_key: Optional[str] = None,
            base_url: Optional[str] = None,
            seed: int = 42
    ):
        self.profile_data = profile_data
        self.model_name = os.getenv("SIMULATOR_MODEL_NAME", model_name)
        self.seed = seed
        self.client = OpenAI(
            api_key=os.getenv("SIMULATOR_API_KEY", api_key),
            base_url=os.getenv("SIMULATOR_BASE_URL", base_url)
        )

    def generate_user_turn(
            self,
            persona: str,
            target_intent: str,
            dialogue_history: List[Dict[str, str]]
    ) -> Tuple[str, int, int]:

        persona_style = self.profile_data["personas"].get(persona, "Speak naturally.")
        forbidden_label_text = target_intent.replace("_", " ")

        # Safely inject variables into the system prompt using .replace()
        system_prompt = self.profile_data["simulator_system_prompt"]
        system_prompt = system_prompt.replace("{target_intent}", target_intent)
        system_prompt = system_prompt.replace("{persona}", persona)
        system_prompt = system_prompt.replace("{persona_style}", persona_style)
        system_prompt = system_prompt.replace("{forbidden_label_text}", forbidden_label_text)

        sim_messages = [{"role": "system", "content": system_prompt}]

        if not dialogue_history:
            # First turn logic injected dynamically
            first_turn_prompt = self.profile_data["simulator_first_turn_prompt"]
            first_turn_prompt = first_turn_prompt.replace("{forbidden_label_text}", forbidden_label_text)

            sim_messages.append({
                "role": "user",
                "content": first_turn_prompt
            })
        else:
            for turn in dialogue_history:
                if turn["role"] == "user":
                    sim_messages.append({"role": "assistant", "content": turn["content"]})
                elif turn["role"] == "assistant":
                    sim_messages.append({"role": "user", "content": turn["content"]})

            # Strict role-bleed boundary enforcement
            sim_messages.append({
                "role": "system",
                "content": "Generate ONLY the customer's next response. Do NOT write the bot's reply. Keep it short."
            })

        while True:
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=sim_messages,
                    temperature=0.7,
                    seed=self.seed
                )

                prompt_tokens = getattr(response.usage, 'prompt_tokens', 0) if response.usage else 0
                completion_tokens = getattr(response.usage, 'completion_tokens', 0) if response.usage else 0
                content = response.choices[0].message.content.strip()

                return content, prompt_tokens, completion_tokens

            except Exception as e:
                print(f"\n[API ERROR - UserSimulator] The connection failed: {e}")
                user_choice = input("Press [ENTER] to retry this turn, or type 'q' to quit: ").strip().lower()
                if user_choice == 'q':
                    print("Exiting simulator...")
                    raise e
                print("Retrying API call...\n")


class TargetVoiceBot:
    def __init__(
            self,
            profile_data: Dict[str, Any],
            model_name: str = "gpt-5-nano",
            allowed_labels: Optional[List[str]] = None,
            api_key: Optional[str] = None,
            base_url: Optional[str] = None,
            seed: int = 42
    ):
        self.profile_data = profile_data
        self.model_name = os.getenv("TARGET_MODEL_NAME", model_name)
        self.seed = seed
        self.allowed_labels = allowed_labels if allowed_labels else []
        self.client = OpenAI(
            api_key=os.getenv("TARGET_API_KEY", api_key),
            base_url=os.getenv("TARGET_BASE_URL", base_url)
        )

    def process_user_turn(self, history: List[Dict[str, str]]) -> Tuple[Dict[str, Any], int, int]:

        # Safely inject variables using .replace() to avoid {} JSON conflicts
        system_prompt = self.profile_data["target_bot_system_prompt"]
        system_prompt = system_prompt.replace("{allowed_labels}", str(self.allowed_labels))

        messages = [{"role": "system", "content": system_prompt}] + history

        while True:
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    response_format={"type": "json_object"},
                    # temperature=0.1,
                    seed=self.seed
                )

                prompt_tokens = getattr(response.usage, 'prompt_tokens', 0) if response.usage else 0
                completion_tokens = getattr(response.usage, 'completion_tokens', 0) if response.usage else 0
                raw_content = response.choices[0].message.content or "{}"

                return parse_llm_json(raw_content), prompt_tokens, completion_tokens

            except Exception as e:
                print(f"\n[API ERROR - TargetVoiceBot] The connection failed: {e}")
                user_choice = input("Press [ENTER] to retry this turn, or type 'q' to quit: ").strip().lower()
                if user_choice == 'q':
                    print("Exiting target bot...")
                    raise e
                print("Retrying API call...\n")


# =====================================================================
# 5. MULTI-TURN TEST HARNESS
# =====================================================================

class MultiTurnTestHarness:
    def __init__(
            self,
            user_sim: UserSimulator,
            target_bot: TargetVoiceBot,
            logger: DialogueLogger,
            profile_data: Dict[str, Any],
            labels: Optional[List[str]] = None,
            seed: int = 42
    ):
        self.seed = seed
        self.user_sim = user_sim
        self.target_bot = target_bot
        self.logger = logger
        self.profile_data = profile_data
        self.labels = labels if labels else target_bot.allowed_labels

        self.global_sim_prompt_tokens = 0
        self.global_sim_completion_tokens = 0
        self.global_bot_prompt_tokens = 0
        self.global_bot_completion_tokens = 0

        # Configuration for Dialogue Control thresholds
        self.CONFIDENCE_THRESHOLD = 0.85
        self.MARGIN_THRESHOLD = 0.15

    def run_batch_simulation(
            self,
            num_dialogues_per_persona: int = 50,
            max_turns: int = 5
    ):
        # Check for our special testing flags
        is_ood = self.profile_data.get("is_ood", False)
        is_adversarial = self.profile_data.get("is_adversarial", False)

        if is_ood:
            target_intents = ["out_of_domain"] * num_dialogues_per_persona
        elif is_adversarial:
            target_intents = ["security_violation"] * num_dialogues_per_persona
        else:
            # Standard behavior
            sampler = ReproducibleLabelSampler(labels=self.labels, seed=self.seed)
            target_intents = sampler.get_labels_for_run(num_dialogues_per_persona)

        personas = self.profile_data.get("personas", {})

        total_simulations = len(personas) * num_dialogues_per_persona
        print(f"\n=======================================================")
        print(f" STARTING MULTI-TURN BATCH SIMULATION")
        print(f" Profile: {self.profile_data.get('profile_name', 'Unknown')}")
        print(f" Output Directory: {self.logger.output_dir}")
        print(f" Seed: {self.seed} | Personas: {len(personas)}")
        print(f" Available Intents in Pool: {len(self.labels)}")
        print(f" Simulator Model: {self.user_sim.model_name}")
        print(f" Target Bot Model: {self.target_bot.model_name}")
        print(f" Dialogues Per Persona: {num_dialogues_per_persona}")
        print(f" Total Dialogues to Generate: {total_simulations}")
        print(f"=======================================================\n")

        completed_count = 0

        for persona in personas.keys():
            print(f"\n>>> Running Persona: [{persona}] ({num_dialogues_per_persona} dialogues)")

            for idx, target_intent in enumerate(target_intents, start=1):
                dialogue_history = []
                turn_logs: List[TurnLog] = []

                for turn_idx in range(1, max_turns + 1):
                    # 1. Simulator Turn
                    user_text, sim_p_tok, sim_c_tok = self.user_sim.generate_user_turn(
                        persona=persona,
                        target_intent=target_intent,
                        dialogue_history=dialogue_history
                    )

                    self.global_sim_prompt_tokens += sim_p_tok
                    self.global_sim_completion_tokens += sim_c_tok
                    dialogue_history.append({"role": "user", "content": user_text})

                    # 2. Target Bot Turn
                    bot_output, bot_p_tok, bot_c_tok = self.target_bot.process_user_turn(dialogue_history)

                    self.global_bot_prompt_tokens += bot_p_tok
                    self.global_bot_completion_tokens += bot_c_tok

                    # Extract the N-Best List and Evaluate Python Thresholds
                    top_3 = bot_output.get("top_3_intents", [])
                    assistant_text = bot_output.get("response_text", "")

                    dialogue_completed = False
                    predicted_intent = "unknown"

                    if top_3 and isinstance(top_3, list) and len(top_3) > 0:
                        predicted_intent = top_3[0].get("intent", "unknown")
                        try:
                            conf_1 = float(top_3[0].get("confidence", 0.0))
                            conf_2 = float(top_3[1].get("confidence", 0.0)) if len(top_3) > 1 else 0.0
                        except (ValueError, TypeError):
                            conf_1, conf_2 = 0.0, 0.0

                        # Evaluate Threshold Rules
                        if conf_1 >= self.CONFIDENCE_THRESHOLD and (conf_1 - conf_2) >= self.MARGIN_THRESHOLD:
                            dialogue_completed = True
                    else:
                        # Fallback for older profiles that don't output top_3_intents
                        predicted_intent = bot_output.get("predicted_intent", "unknown")
                        dialogue_completed = bot_output.get("dialogue_completed", False)

                    dialogue_history.append({"role": "assistant", "content": assistant_text})

                    # 3. Log the turn
                    turn_logs.append(TurnLog(
                        turn_number=turn_idx,
                        user_utterance=user_text,
                        assistant_response=assistant_text,
                        predicted_intent=predicted_intent,
                        top_3_intents=top_3,
                        timestamp=datetime.now().isoformat(),
                        sim_prompt_tokens=sim_p_tok,
                        sim_completion_tokens=sim_c_tok,
                        bot_prompt_tokens=bot_p_tok,
                        bot_completion_tokens=bot_c_tok
                    ))

                    # Format print statement to show confidence
                    if top_3 and len(top_3) > 0:
                        conf_print = f"({predicted_intent} @ {top_3[0].get('confidence', 0.0):.2f})"
                    else:
                        conf_print = f"({predicted_intent})"

                    print(
                        f"  [Turn {turn_idx}/{max_turns}] User: '{user_text[:50]}...' -> Bot {conf_print}: '{assistant_text[:50]}...'")

                    if dialogue_completed:
                        print(f"  --> Thresholds met. Dialogue marked completed by Python script.")
                        break

                dialogue_id = self.logger.save_trace(
                    seed=self.seed,
                    dialogue_index=idx,
                    persona=persona,
                    target_intent=target_intent,
                    sim_model=self.user_sim.model_name,
                    target_model=self.target_bot.model_name,
                    turns=turn_logs,
                    status="COMPLETED" if dialogue_completed else "MAX_TURNS_REACHED"
                )
                completed_count += 1
                print(
                    f" [{completed_count}/{total_simulations}] Saved Dialogue #{idx:02d} ({persona}) [ID: {dialogue_id[:8]}]"
                )

        self._print_and_save_summary(total_simulations, completed_count)

    def _print_and_save_summary(self, total_simulations: int, completed_count: int):
        total_sim_tokens = self.global_sim_prompt_tokens + self.global_sim_completion_tokens
        total_bot_tokens = self.global_bot_prompt_tokens + self.global_bot_completion_tokens
        grand_total = total_sim_tokens + total_bot_tokens

        summary_data = {
            "profile_used": self.profile_data.get("profile_name", "Unknown"),
            "total_dialogues_target": total_simulations,
            "total_dialogues_completed": completed_count,
            "simulator": {
                "model": self.user_sim.model_name,
                "prompt_tokens": self.global_sim_prompt_tokens,
                "completion_tokens": self.global_sim_completion_tokens,
                "total_tokens": total_sim_tokens
            },
            "target_bot": {
                "model": self.target_bot.model_name,
                "prompt_tokens": self.global_bot_prompt_tokens,
                "completion_tokens": self.global_bot_completion_tokens,
                "total_tokens": total_bot_tokens
            },
            "grand_total_tokens": grand_total
        }

        summary_file = os.path.join(self.logger.output_dir, "batch_summary.json")
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2)

        print(f"\n=======================================================")
        print(f" BATCH SIMULATION COMPLETE")
        print(f"=======================================================")
        print(f" Dialogues Generated: {completed_count}/{total_simulations}")
        print(f" Data saved to: {self.logger.output_dir}")
        print(f"-------------------------------------------------------")
        print(f" TOKEN USAGE SUMMARY")
        print(f"-------------------------------------------------------")
        print(f" User Simulator ({self.user_sim.model_name}):")
        print(f"   - Prompt Tokens:     {self.global_sim_prompt_tokens:,}")
        print(f"   - Completion Tokens: {self.global_sim_completion_tokens:,}")
        print(f"   - Subtotal:          {total_sim_tokens:,}")
        print(f"")
        print(f" Target Bot ({self.target_bot.model_name}):")
        print(f"   - Prompt Tokens:     {self.global_bot_prompt_tokens:,}")
        print(f"   - Completion Tokens: {self.global_bot_completion_tokens:,}")
        print(f"   - Subtotal:          {total_bot_tokens:,}")
        print(f"-------------------------------------------------------")
        print(f" GRAND TOTAL TOKENS:    {grand_total:,}")
        print(f"=======================================================\n")


# =====================================================================
# 7. CLI ENTRY POINT
# =====================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Multi-Turn Dialogue Simulation Harness with JSON Profiles")

    parser.add_argument("--profile", type=str, default="profiles/standard_en.json",
                        help="Path to the JSON scenario profile (default: profiles/standard_en.json)")
    parser.add_argument("--csv_path", type=str, default="../dataset/single-turn/banking77_test.csv",
                        help="Path to local NLU CSV file (default: dataset/single-turn/banking77_test.csv)")
    parser.add_argument("--num_dialogues", type=int, default=2, help="Number of dialogues per persona (default: 2)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--max_turns", type=int, default=5, help="Maximum number of turns per dialogue (default: 5)")
    parser.add_argument("--output_base_dir", type=str, default="logs/multi_turn_dialogues",
                        help="Base directory for JSON logs. A new incremented folder will be created inside.")

    parser.add_argument("--sim_model", type=str, default="gpt-5-nano", help="Model name for User Simulator")
    parser.add_argument("--sim_api_key", type=str, default="dummy_key", help="API key for User Simulator API")
    parser.add_argument("--sim_base_url", type=str, default="https://api.openai.com/v1",
                        help="Base URL for User Simulator API")

    parser.add_argument("--target_model", type=str, default="gpt-5.6-luna", help="Model name for Target Voice Bot")
    parser.add_argument("--target_api_key", type=str, default="dummy_key", help="API key for Target Voice Bot API")
    parser.add_argument("--target_base_url", type=str, default="https://api.openai.com/v1",
                        help="Base URL for Target Voice Bot API")

    args = parser.parse_args()

    # Load Profile Data
    profile_path = Path(args.profile)
    if not profile_path.exists():
        print(f"[CRITICAL ERROR] The profile file '{profile_path}' does not exist.")
        exit(1)

    with open(profile_path, "r", encoding="utf-8") as pf:
        profile_data = json.load(pf)

    # Determine sub-folder routing based on profile flags
    is_ood = profile_data.get("is_ood", False)
    is_adversarial = profile_data.get("is_adversarial", False)

    if is_ood:
        category_folder = "ood"
    elif is_adversarial:
        category_folder = "adversarial"
    else:
        category_folder = "personas"

    # Append the category to the base output directory
    base_dir_with_category = os.path.join(args.output_base_dir, category_folder)

    # 1. Load Intent Labelset dynamically from CSV
    active_labels = []
    if args.csv_path:
        csv_file = Path(args.csv_path)
        try:
            _, loaded_intents = load_local_csv(csv_file)
            if loaded_intents:
                active_labels = loaded_intents
        except Exception as e:
            print(f"[DataLoader WARNING] CSV konnte nicht geladen werden ({e}).")

    # 2. Setup the auto-incrementing output directory
    resolved_output_dir = get_next_incremented_dir(
        base_dir=base_dir_with_category,
        prefix="run",
        suffix=args.target_model
    )

    # 3. Initialize Agents
    user_sim = UserSimulator(
        profile_data=profile_data,
        model_name=args.sim_model,
        api_key=args.sim_api_key,
        base_url=args.sim_base_url,
        seed=args.seed
    )

    target_bot = TargetVoiceBot(
        profile_data=profile_data,
        model_name=args.target_model,
        allowed_labels=active_labels,
        api_key=args.target_api_key,
        base_url=args.target_base_url,
        seed=args.seed
    )

    logger = DialogueLogger(output_dir=resolved_output_dir)

    # 4. Initialize & Run Harness
    harness = MultiTurnTestHarness(
        user_sim=user_sim,
        target_bot=target_bot,
        logger=logger,
        profile_data=profile_data,
        labels=active_labels,
        seed=args.seed
    )

    harness.run_batch_simulation(
        num_dialogues_per_persona=args.num_dialogues,
        max_turns=args.max_turns
    )