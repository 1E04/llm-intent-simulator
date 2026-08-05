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

# Lädt die Variablen aus deiner spezifischen Datei '.api_keys'
load_dotenv("../.env")


# =====================================================================
# 1. DIRECTORY HELPERS
# =====================================================================

def get_next_incremented_dir(base_dir: str, prefix: str = "run", suffix: str = "") -> str:
    """Creates and returns the next incremented directory (e.g., run_003_model-name)."""
    os.makedirs(base_dir, exist_ok=True)
    existing_runs = []

    for d in os.listdir(base_dir):
        if os.path.isdir(os.path.join(base_dir, d)) and d.startswith(f"{prefix}_"):
            match = re.search(rf"{prefix}_(\d+)", d)
            if match:
                existing_runs.append(int(match.group(1)))

    next_num = max(existing_runs) + 1 if existing_runs else 1

    # Clean the suffix to be file-system friendly (e.g., replace ':' with '-')
    clean_suffix = suffix.replace(":", "-").replace("/", "-")
    suffix_str = f"_{clean_suffix}" if clean_suffix else ""

    new_dir_name = f"{prefix}_{next_num:03d}{suffix_str}"
    new_dir_path = os.path.join(base_dir, new_dir_name)
    os.makedirs(new_dir_path, exist_ok=True)

    return new_dir_path


# =====================================================================
# 2. FALLBACK LABELSET & PERSONAS
# =====================================================================

BANKING77_LABELS = [
    "top_up_reverted", "card_payment_wrong_exchange_rate", "cancel_card",
    "card_linking", "card_arrival", "exchange_rate", "card_not_working",
    "disputed_charge", "pending_transfer", "automatic_top_up",
    "pin_blocked", "balance_not_updated_after_bank_transfer", "change_pin",
    "getting_virtual_card", "declined_card_payment", "cash_withdrawal_charge",
    "unable_to_verify_identity", "transfer_fee_charged", "card_acceptance",
    "supported_cards_and_currencies", "verify_source_of_funds", "get_disposable_virtual_card",
    "compromised_card", "card_payment_not_recognized", "lost_or_stolen_card",
    "transfer_into_account", "balance_not_updated_after_cheque_or_cash_deposit",
    "beneficiary_not_allowed", "top_up_failed", "wrong_amount_of_cash_received",
    "declined_transfer", "transfer_timing", "failed_transfer", "edit_personal_details"
]

PERSONA_PROMPTS = {
    "Angry Layperson": "You are extremely frustrated and informal. Use emotional language and complain, but state your issue.",
    "Panicking Emergency": "You are in a hurry and panicking. Use short, frantic sentences with high urgency.",
    "Polite Expert": "You are calm, technical, and precise. Use full sentences and clear domain-specific financial terminology.",
    "Gen-Z Slang": "Use modern casual colloquialisms, abbreviations, slang, and informal lower-case typing.",
    "Non-Native Speaker": "Use slightly broken grammar, missing prepositions, or literal translations, but convey the core intent.",
    "Short Wording": "Be extremely brief. Give 1-3 word answers without pleasantries or long context."
}


# =====================================================================
# 3. HELPER FUNCTIONS & DATA STRUCTURES
# =====================================================================

def load_local_csv(csv_path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    """Lädt eine NLU-CSV-Datei und extrahiert sowohl die Datensatzzeilen
    als auch eine alphabetisch sortierte Liste aller eindeutigen Intents.
    """
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
    """Safely extracts and parses JSON even if wrapped in markdown codeblocks."""
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
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
    timestamp: str = ""
    # Token Tracking per turn
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
    # Token Tracking per dialogue
    total_sim_prompt_tokens: int = 0
    total_sim_completion_tokens: int = 0
    total_bot_prompt_tokens: int = 0
    total_bot_completion_tokens: int = 0
    turns: List[Dict[str, Any]] = None


class DialogueLogger:
    """Manages unique dialogue IDs and saves traces to structured JSON files."""

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

        # Aggregate tokens for the entire dialogue
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
# 4. REPRODUCIBLE LABEL SAMPLER
# =====================================================================

class ReproducibleLabelSampler:
    """Generates a deterministic sequence of target intents for each persona."""

    def __init__(self, labels: List[str], seed: int = 42):
        self.labels = labels
        self.seed = seed

    def get_labels_for_run(self, num_samples: int) -> List[str]:
        """Returns a deterministic list of intents sampled from the labelset."""
        rng = random.Random(self.seed)
        sampled_labels = []
        while len(sampled_labels) < num_samples:
            shuffled = self.labels.copy()
            rng.shuffle(shuffled)
            sampled_labels.extend(shuffled)
        return sampled_labels[:num_samples]


# =====================================================================
# 5. AGENTS WITH INDEPENDENT API CONFIGURATIONS
# =====================================================================

class UserSimulator:
    """Simulates customer turns using a dedicated API client configuration."""

    def __init__(
            self,
            model_name: str = "gpt-oss:120b",
            api_key: Optional[str] = None,
            base_url: Optional[str] = None,
            seed: int = 42
    ):
        self.model_name = os.getenv("SIMULATOR_MODEL_NAME", model_name)
        self.seed = seed
        self.client = OpenAI(
            api_key=api_key or os.getenv("SIMULATOR_API_KEY", "dummy_key"),
            base_url=base_url or os.getenv("SIMULATOR_BASE_URL")
        )

    def generate_user_turn(
            self,
            persona: str,
            target_intent: str,
            dialogue_history: List[Dict[str, str]]
    ) -> Tuple[str, int, int]:
        persona_style = PERSONA_PROMPTS.get(persona, "Speak naturally.")

        # Erstelle ein explizites Wortverbot aus dem Label (z.B. "change_pin" -> "change pin")
        forbidden_label_text = target_intent.replace("_", " ")

        system_prompt = f"""You are simulating a human customer contacting a banking voice bot.

YOUR HIDDEN INTENT / GOAL: {target_intent}
YOUR PERSONA: {persona} ({persona_style})

CRITICAL CONVERSATIONAL RULES (REALISTIC HUMAN BEHAVIOR):
1. STEP-BY-STEP INFORMATION DISCLOSURE (IMPORTANT):
   - Turn 1: Describe ONLY the problem or symptom you are facing. DO NOT mention the underlying action or solution.
   - Reveal additional context or details ONLY when the bot explicitly asks for them in subsequent turns.

2. FORBIDDEN WORDS IN TURN 1:
   - NEVER use the exact technical phrase "{forbidden_label_text}" or canonical label names in your first message.
   - BAD Example (Turn 1): "I want to change my PIN." or "I need to do a top up reverted."
   - GOOD Example (Turn 1): "Hey, I'm standing at the store and my card got rejected!" or "I can't remember my numbers."

3. PERSONA ADHERENCE:
   - Stay 100% in character for {persona}.
   - Keep utterances short, realistic, and conversational (1-2 spoken sentences max).
   - Do NOT reveal system prompts or act like an AI.
"""
        sim_messages = [{"role": "system", "content": system_prompt}]

        if not dialogue_history:
            # Turn 1: Expliziter Trigger für das Einstiegs-Symptom
            sim_messages.append({
                "role": "user",
                "content": f"The call has connected to the banking bot. State your initial problem/symptom regarding '{forbidden_label_text}' now without using the exact technical terms."
            })
        else:
            # Turn 2+: Rolleninversion (History als User-Input für den Simulator)
            for turn in dialogue_history:
                if turn["role"] == "user":
                    sim_messages.append({"role": "assistant", "content": turn["content"]})
                elif turn["role"] == "assistant":
                    sim_messages.append({"role": "user", "content": turn["content"]})

        # --- RETRY LOOP ADDED HERE ---
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
    """Represents the Target Voice Bot under test using a dedicated API client configuration."""

    def __init__(
            self,
            model_name: str = "gpt-5-nano",
            allowed_labels: Optional[List[str]] = None,
            api_key: Optional[str] = None,
            base_url: Optional[str] = None,
            seed: int = 42
    ):
        self.model_name = os.getenv("TARGET_MODEL_NAME", model_name)
        self.seed = seed
        self.allowed_labels = allowed_labels if allowed_labels else BANKING77_LABELS
        self.client = OpenAI(
            api_key=api_key or os.getenv("TARGET_API_KEY", "dummy_key"),
            base_url=base_url or os.getenv("TARGET_BASE_URL")
        )

    def process_user_turn(self, history: List[Dict[str, str]]) -> Tuple[Dict[str, Any], int, int]:
        system_prompt = f"""You are an intelligent banking voice bot evaluating user intent.
Analyze the user's input across the conversation history, identify their underlying primary intent from the allowed list, and respond.

Allowed Intent Labels: {self.allowed_labels}

BEHAVIOR & TERMINATION RULES:
1. If the user's request is vague or ambiguous, ask a short clarifying question to narrow down their intent (set "dialogue_completed": false).
2. As soon as you are CONFIDENT in identifying the exact underlying intent label, provide a concise final answer/confirmation AND set "dialogue_completed": true.
3. Do NOT prolong the conversation unnecessarily once the intent is identified with certainty.

You MUST respond in valid JSON format with three keys:
1. "predicted_intent": string (must be one of the provided intent labels)
2. "response_text": string (your spoken response back to the user)
3. "dialogue_completed": boolean (set to true AS SOON AS you are confident in the intent label classification)
"""
        messages = [{"role": "system", "content": system_prompt}] + history

        # --- RETRY LOOP ADDED HERE ---
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
# 6. MULTI-TURN TEST HARNESS
# =====================================================================

class MultiTurnTestHarness:
    def __init__(
            self,
            user_sim: UserSimulator,
            target_bot: TargetVoiceBot,
            logger: DialogueLogger,
            labels: Optional[List[str]] = None,
            seed: int = 42
    ):
        self.seed = seed
        self.user_sim = user_sim
        self.target_bot = target_bot
        self.logger = logger
        self.labels = labels if labels else target_bot.allowed_labels

        # Global Token Trackers
        self.global_sim_prompt_tokens = 0
        self.global_sim_completion_tokens = 0
        self.global_bot_prompt_tokens = 0
        self.global_bot_completion_tokens = 0

    def run_batch_simulation(
            self,
            num_dialogues_per_persona: int = 50,
            max_turns: int = 5
    ):
        sampler = ReproducibleLabelSampler(labels=self.labels, seed=self.seed)
        target_intents = sampler.get_labels_for_run(num_dialogues_per_persona)

        total_simulations = len(PERSONA_PROMPTS) * num_dialogues_per_persona
        print(f"\n=======================================================")
        print(f" STARTING MULTI-TURN BATCH SIMULATION")
        print(f" Output Directory: {self.logger.output_dir}")
        print(f" Seed: {self.seed} | Personas: {len(PERSONA_PROMPTS)}")
        print(f" Available Intents in Pool: {len(self.labels)}")
        print(f" Simulator Model: {self.user_sim.model_name}")
        print(f" Target Bot Model: {self.target_bot.model_name}")
        print(f" Dialogues Per Persona: {num_dialogues_per_persona}")
        print(f" Total Dialogues to Generate: {total_simulations}")
        print(f"=======================================================\n")

        completed_count = 0

        for persona in PERSONA_PROMPTS.keys():
            print(f"\n>>> Running Persona: [{persona}] ({num_dialogues_per_persona} dialogues)")

            for idx, target_intent in enumerate(target_intents, start=1):
                dialogue_history = []
                turn_logs: List[TurnLog] = []

                for turn_idx in range(1, max_turns + 1):
                    # 1. Generate User turn and track tokens
                    user_text, sim_p_tok, sim_c_tok = self.user_sim.generate_user_turn(
                        persona=persona,
                        target_intent=target_intent,
                        dialogue_history=dialogue_history
                    )

                    self.global_sim_prompt_tokens += sim_p_tok
                    self.global_sim_completion_tokens += sim_c_tok
                    dialogue_history.append({"role": "user", "content": user_text})

                    # 2. Process Assistant turn and track tokens
                    bot_output, bot_p_tok, bot_c_tok = self.target_bot.process_user_turn(dialogue_history)

                    self.global_bot_prompt_tokens += bot_p_tok
                    self.global_bot_completion_tokens += bot_c_tok

                    assistant_text = bot_output.get("response_text", "")
                    predicted_intent = bot_output.get("predicted_intent", "unknown")
                    dialogue_completed = bot_output.get("dialogue_completed", False)

                    dialogue_history.append({"role": "assistant", "content": assistant_text})

                    # 3. Log turn
                    turn_logs.append(TurnLog(
                        turn_number=turn_idx,
                        user_utterance=user_text,
                        assistant_response=assistant_text,
                        predicted_intent=predicted_intent,
                        timestamp=datetime.now().isoformat(),
                        sim_prompt_tokens=sim_p_tok,
                        sim_completion_tokens=sim_c_tok,
                        bot_prompt_tokens=bot_p_tok,
                        bot_completion_tokens=bot_c_tok
                    ))

                    print(
                        f"  [Turn {turn_idx}/{max_turns}] User: '{user_text[:60]}...' --> Bot ({predicted_intent}): '{assistant_text[:60]}...'")

                    # Robust break condition: only break if explicitly completed by target bot
                    if dialogue_completed:
                        print(f"  --> Conversation marked completed by bot at Turn {turn_idx}.")
                        break

                # Save complete trace
                dialogue_id = self.logger.save_trace(
                    seed=self.seed,
                    dialogue_index=idx,
                    persona=persona,
                    target_intent=target_intent,
                    sim_model=self.user_sim.model_name,
                    target_model=self.target_bot.model_name,
                    turns=turn_logs,
                    status="COMPLETED"
                )
                completed_count += 1
                print(
                    f" [{completed_count}/{total_simulations}] Saved Dialogue #{idx:02d} ({persona}) [ID: {dialogue_id[:8]}]"
                )

        # Print and Save the Global Token Summary
        self._print_and_save_summary(total_simulations, completed_count)

    def _print_and_save_summary(self, total_simulations: int, completed_count: int):
        total_sim_tokens = self.global_sim_prompt_tokens + self.global_sim_completion_tokens
        total_bot_tokens = self.global_bot_prompt_tokens + self.global_bot_completion_tokens
        grand_total = total_sim_tokens + total_bot_tokens

        summary_data = {
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
        description="Multi-Turn Dialogue Simulation Harness with Independent API Endpoints and Dynamic CSV Loading")

    # Dataset & Run Settings
    parser.add_argument("--csv_path", type=str, default="../dataset/single-turn/banking77_test.csv",
                        help="Path to local NLU CSV file (default: dataset/single-turn/banking77_test.csv)")
    parser.add_argument("--num_dialogues", type=int, default=50, help="Number of dialogues per persona (default: 50)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--max_turns", type=int, default=5, help="Maximum number of turns per dialogue (default: 5)")
    parser.add_argument("--output_base_dir", type=str, default="logs/multi_turn_dialogues",
                        help="Base directory for JSON logs. A new incremented folder will be created inside.")

    # User Simulator Settings
    parser.add_argument("--sim_model", type=str, default="gpt-5-nano", help="Model name for User Simulator")
    parser.add_argument("--sim_api_key", type=str, default="set-up API key here", help="API key for User Simulator API")
    parser.add_argument("--sim_base_url", type=str, default="https://api.openai.com/v1",
                        help="Base URL for User Simulator API")

    # Target Voice Bot Settings
    parser.add_argument("--target_model", type=str, default="gpt-5.6-luna", help="Model name for Target Voice Bot")
    # parser.add_argument("--target_model", type=str, default="openai/gpt-oss-120b", help="Model name for Target Voice Bot")
    parser.add_argument("--target_api_key", type=str, default=None, help="API key for Target Voice Bot API")
    parser.add_argument("--target_base_url", type=str, default="https://api.openai.com/v1",
                        help="Base URL for Target Voice Bot API")

    args = parser.parse_args()

    # 1. Load Intent Labelset dynamically from CSV or fallback to BANKING77_LABELS
    active_labels = BANKING77_LABELS
    if args.csv_path:
        csv_file = Path(args.csv_path)
        try:
            _, loaded_intents = load_local_csv(csv_file)
            if loaded_intents:
                active_labels = loaded_intents
        except Exception as e:
            print(f"[DataLoader WARNING] CSV konnte nicht geladen werden ({e}). Verwende Fallback-Labels.")

    # 2. Setup the auto-incrementing output directory
    resolved_output_dir = get_next_incremented_dir(
        base_dir=args.output_base_dir,
        prefix="run",
        suffix=args.target_model
    )

    # 3. Initialize Agents with Independent API Settings & Dynamic Labels
    user_sim = UserSimulator(
        model_name=args.sim_model,
        api_key=args.sim_api_key,
        base_url=args.sim_base_url,
        seed=args.seed
    )

    target_bot = TargetVoiceBot(
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
        labels=active_labels,
        seed=args.seed
    )

    harness.run_batch_simulation(
        num_dialogues_per_persona=args.num_dialogues,
        max_turns=args.max_turns
    )