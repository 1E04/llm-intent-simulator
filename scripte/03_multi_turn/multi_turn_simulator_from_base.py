"""Multi-Turn Simulator - Human Base Input Variant

Same simulation loop as ``multi-turn-simulator.py``, with one difference:
there are **no personas**.

Every dialogue starts with a real human utterance taken from
``dataset/single-turn/banking77_test_labels_clean.csv``.  From turn 2 onwards
the user simulator simply keeps talking the way that real customer talked -
same tone, register, wording habits and level of detail as the base sentence -
while the target bot tries to resolve the ground-truth intent.

Usage example::

    python scripte/03_multi_turn/multi_turn_simulator_from_base.py \
        --profile scripte/profiles/standard_en.json \
        --output_base_dir logs/multi_turn_dialogues \
        --sim_model openai/gpt-5.4-nano \
        --target_model openai/gpt-5.6-luna

``--csv_path`` is optional and overrides the hard-coded human base dataset.
"""

import os
import json
import random
import argparse
import importlib.util
import concurrent.futures
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from dotenv import load_dotenv

# ---------------------------------------------------------------------
# Environment handling - locate ``.env`` two levels up (repo root) just like
# the original multi-turn simulator.
# ---------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR.parent.parent / ".env"
load_dotenv(ENV_PATH)
print(f"Loaded environment variables from: {ENV_PATH}")

DEFAULT_CSV_PATH = SCRIPT_DIR.parents[1] / "dataset" / "single-turn" / "banking77_test_labels_clean.csv"

# Written into the trace/filenames in place of a persona name.
BASE_STYLE_TAG = "HumanBase"

# ---------------------------------------------------------------------
# Import the core implementation (file name contains a hyphen).
# ---------------------------------------------------------------------
SIMULATOR_CORE_PATH = SCRIPT_DIR / "multi-turn-simulator.py"
_core_spec = importlib.util.spec_from_file_location("multi_turn_sim_core", SIMULATOR_CORE_PATH)
assert _core_spec and _core_spec.loader, f"Failed to locate core module: {SIMULATOR_CORE_PATH}"
core_module = importlib.util.module_from_spec(_core_spec)
_core_spec.loader.exec_module(core_module)  # type: ignore[arg-type]

UserSimulator = core_module.UserSimulator
TargetVoiceBot = core_module.TargetVoiceBot
DialogueLogger = core_module.DialogueLogger
TurnLog = core_module.TurnLog
get_next_incremented_dir = core_module.get_next_incremented_dir
load_local_csv = core_module.load_local_csv

CONFIDENCE_THRESHOLD = 0.85
MARGIN_THRESHOLD = 0.15


# =====================================================================
# USER SIMULATOR THAT MIRRORS THE REAL BASE UTTERANCE
# =====================================================================

class BaseInputUserSimulator(UserSimulator):
    """User simulator without personas.

    The style is not taken from a persona catalogue but from the real customer
    sentence the dialogue started with: the simulator is told to keep speaking
    exactly like that sentence sounded.  The profile's ``{persona}`` /
    ``{persona_style}`` placeholders are filled with that instruction so the
    existing prompt template can be reused unchanged.
    """

    STYLE_INSTRUCTION = (
        "Speak exactly like the customer's own opening message quoted below. "
        "Mirror its tone, politeness, register, sentence length, level of detail, "
        "capitalisation, typos and any slang or non-native phrasing it contains. "
        "Do NOT adopt any other character and do NOT invent a new speaking style.\n"
        'CUSTOMER\'S OPENING MESSAGE: "{base_utterance}"'
    )

    def generate_user_turn(
            self,
            base_utterance: str,
            dialogue_history: List[Dict[str, str]],
            target_intent: Optional[str] = None,
            jailbreak_payload: str = "",
            turn_idx: int = 1
    ) -> Tuple[str, int, int]:
        style = self.STYLE_INSTRUCTION.format(base_utterance=base_utterance)
        original_prompt = self.profile_data["simulator_system_prompt"]
        self.profile_data = dict(self.profile_data)
        self.profile_data["simulator_system_prompt"] = (
            original_prompt
            .replace("{persona_style}", style)
            .replace("{persona}", "the same customer as in the opening message")
        )
        try:
            # The base class only uses ``persona`` for a catalogue lookup that
            # no longer applies here - the style is already in the prompt.
            return super().generate_user_turn(
                persona=BASE_STYLE_TAG,
                dialogue_history=dialogue_history,
                target_intent=target_intent,
                jailbreak_payload=jailbreak_payload,
                turn_idx=turn_idx,
            )
        finally:
            self.profile_data["simulator_system_prompt"] = original_prompt


# =====================================================================
# DATASET SELECTION
# =====================================================================

def select_seed_rows(
        dataset: List[Dict[str, str]],
        mode: str,
        num_dialogues: int,
        per_intent: int,
        start_index: int,
        rng: random.Random,
) -> List[Dict[str, str]]:
    """Pick the CSV rows that seed the dialogues.

    ``random``      - seeded random subset (whole dataset if num_dialogues <= 0)
    ``sequential``  - CSV order starting at ``start_index`` (resumable)
    ``per_intent``  - ``per_intent`` rows for each intent (stratified subset)
    """
    total = len(dataset)

    if mode == "per_intent":
        by_intent: Dict[str, List[Dict[str, str]]] = {}
        for row in dataset:
            by_intent.setdefault(row["label"], []).append(row)
        rows: List[Dict[str, str]] = []
        for intent in sorted(by_intent):
            candidates = by_intent[intent]
            k = min(per_intent, len(candidates))
            rows.extend(rng.sample(candidates, k))
        print(f"[Select] per_intent={per_intent} over {len(by_intent)} intents -> {len(rows)} dialogues")
        return rows

    if mode == "sequential":
        start = max(0, start_index)
        end = total if num_dialogues <= 0 else min(total, start + num_dialogues)
        rows = dataset[start:end]
        print(f"[Select] sequential rows [{start}:{end}] of {total} -> {len(rows)} dialogues")
        return rows

    # random
    if num_dialogues <= 0 or num_dialogues >= total:
        rows = dataset[:]
        rng.shuffle(rows)
        print(f"[Select] random over the ENTIRE dataset -> {len(rows)} dialogues")
        return rows
    rows = rng.sample(dataset, num_dialogues)
    print(f"[Select] random subset -> {len(rows)} of {total} dialogues")
    return rows


# =====================================================================
# MAIN
# =====================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Multi-Turn Simulator that starts from the human base test CSV (no personas).")

    parser.add_argument("--profile", type=str, required=True,
                        help="Path to a profile JSON file (prompts are used, personas are ignored).")
    parser.add_argument("--output_base_dir", type=str, default="logs/multi_turn_dialogues",
                        help="Base directory for run outputs.")
    parser.add_argument("--sim_model", type=str, default="openai/gpt-5.4-nano",
                        help="Model used for the user simulator.")
    parser.add_argument("--sim_api_key", type=str, default="dummy_key",
                        help="API key for the user simulator.")
    parser.add_argument("--sim_base_url", type=str, default="https://api.openai.com/v1",
                        help="Base URL for the user simulator API.")
    parser.add_argument("--target_model", type=str, default="openai/gpt-5.6-luna",
                        help="Model used for the target voice bot.")
    parser.add_argument("--target_api_key", type=str, default="dummy_key",
                        help="API key for the target bot.")
    parser.add_argument("--target_base_url", type=str, default="https://api.openai.com/v1",
                        help="Base URL for the target bot API.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    parser.add_argument("--num_dialogues", type=int, default=5,
                        help="Number of dialogues (one real CSV utterance each). "
                             "Use 0 or -1 for the ENTIRE dataset. Ignored with --per_intent.")
    parser.add_argument("--sample_mode", choices=["random", "sequential", "per_intent"],
                        default="random",
                        help="random: seeded random subset | sequential: CSV order from "
                             "--start_index | per_intent: --per_intent rows per intent.")
    parser.add_argument("--per_intent", type=int, default=1,
                        help="With --sample_mode per_intent: rows per intent (77 intents).")
    parser.add_argument("--start_index", type=int, default=0,
                        help="With --sample_mode sequential: first CSV row to use (for resuming).")
    parser.add_argument("--max_turns", type=int, default=8,
                        help="Maximum number of turns per dialogue.")
    parser.add_argument("--jailbreak_payload", type=str, default="",
                        help="Optional payload injected into the simulator prompt.")
    parser.add_argument("--csv_path", type=str, default="",
                        help="Override CSV path - defaults to the human base CSV.")
    parser.add_argument("--concurrency", type=int, default=1,
                        help="Number of concurrent dialogues to run.")

    args = parser.parse_args()

    csv_path = Path(args.csv_path) if args.csv_path else DEFAULT_CSV_PATH

    # -----------------------------------------------------------------
    # Load dataset (real human utterances + ground truth intents).
    # -----------------------------------------------------------------
    full_dataset, active_labels = load_local_csv(csv_path)
    if not full_dataset or not active_labels:
        print("[CRITICAL] No usable rows loaded from CSV - aborting.")
        raise SystemExit(1)

    # -----------------------------------------------------------------
    # Load profile and prepare the output folder.
    # -----------------------------------------------------------------
    profile_path = Path(args.profile)
    if not profile_path.exists():
        print(f"[CRITICAL] Profile file does not exist: {profile_path}")
        raise SystemExit(1)
    with open(profile_path, "r", encoding="utf-8") as pf:
        profile_data = json.load(pf)

    if profile_data.get("is_ood", False):
        category_folder = "ood"
    elif profile_data.get("is_adversarial", False):
        category_folder = "adversarial"
    else:
        category_folder = "human_base"

    resolved_output_dir = get_next_incremented_dir(
        base_dir=os.path.join(args.output_base_dir, category_folder),
        prefix="run",
        suffix=args.target_model,
    )

    # -----------------------------------------------------------------
    # Sample the real utterances that seed the dialogues.
    # -----------------------------------------------------------------
    rng = random.Random(args.seed)
    seed_rows = select_seed_rows(
        dataset=full_dataset,
        mode=args.sample_mode,
        num_dialogues=args.num_dialogues,
        per_intent=args.per_intent,
        start_index=args.start_index,
        rng=rng,
    )
    num_dialogues = len(seed_rows)
    if not seed_rows:
        print("[CRITICAL] Selection produced 0 rows - check --sample_mode / --start_index.")
        raise SystemExit(1)

    print("=" * 70)
    print(" MULTI-TURN SIMULATION (HUMAN BASE INPUT, NO PERSONAS)")
    print("=" * 70)
    print(f" CSV: {csv_path}")
    print(f" Output: {resolved_output_dir}")
    print(f" Seed: {args.seed} | Dialogues: {num_dialogues} | Max Turns: {args.max_turns}")
    print(f" Sim Model: {args.sim_model} | Target Model: {args.target_model}")
    print("=" * 70)

    completed_count = 0
    
    def run_single_dialogue(dlg_idx: int, row: Dict[str, str]) -> str:
        target_intent = row["label"]
        base_utterance = row["text"]

        user_sim = BaseInputUserSimulator(
            profile_data=profile_data,
            model_name=args.sim_model,
            api_key=args.sim_api_key,
            base_url=args.sim_base_url,
            seed=args.seed,
        )
        target_bot = TargetVoiceBot(
            profile_data=profile_data,
            model_name=args.target_model,
            allowed_labels=active_labels,
            api_key=args.target_api_key,
            base_url=args.target_base_url,
            seed=args.seed,
        )
        logger = DialogueLogger(output_dir=resolved_output_dir)

        print(f"\n>>> Dialogue #{dlg_idx:03d} | Intent: {target_intent} | Sample: {row['id']}")
        print(f"    Base utterance: '{base_utterance}'")

        dialogue_history: List[Dict[str, str]] = []
        turn_logs: List[TurnLog] = []
        dialogue_completed = False

        for turn_idx in range(1, args.max_turns + 1):
            # ---- user side -------------------------------------------------
            if turn_idx == 1:
                # Turn 1 is the untouched real human sentence from the dataset.
                user_text, sim_p_tok, sim_c_tok = base_utterance, 0, 0
            else:
                user_text, sim_p_tok, sim_c_tok = user_sim.generate_user_turn(
                    base_utterance=base_utterance,
                    dialogue_history=dialogue_history,
                    target_intent=target_intent,
                    jailbreak_payload=args.jailbreak_payload,
                    turn_idx=turn_idx,
                )
            dialogue_history.append({"role": "user", "content": user_text})

            # ---- bot side --------------------------------------------------
            bot_output, bot_p_tok, bot_c_tok = target_bot.process_user_turn(dialogue_history)
            assistant_text = bot_output.get("response_text", "")
            dialogue_history.append({"role": "assistant", "content": assistant_text})

            top_3 = bot_output.get("top_3_intents", [])
            if top_3 and isinstance(top_3, list):
                predicted_intent = top_3[0].get("intent", "unknown")
                try:
                    conf_1 = float(top_3[0].get("confidence", 0.0))
                    conf_2 = float(top_3[1].get("confidence", 0.0)) if len(top_3) > 1 else 0.0
                except (ValueError, TypeError):
                    conf_1, conf_2 = 0.0, 0.0
                if conf_1 >= CONFIDENCE_THRESHOLD and (conf_1 - conf_2) >= MARGIN_THRESHOLD:
                    dialogue_completed = True
                conf_print = f"({predicted_intent} @ {conf_1:.2f})"
            else:
                predicted_intent = bot_output.get("predicted_intent", "unknown")
                dialogue_completed = bool(bot_output.get("dialogue_completed", False))
                conf_print = f"({predicted_intent})"

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
                bot_completion_tokens=bot_c_tok,
            ))

            print(f"  [Turn {turn_idx}/{args.max_turns}] User: '{user_text[:50]}...' "
                  f"-> Bot {conf_print}: '{assistant_text[:50]}...'")

            if dialogue_completed:
                print("  --> Thresholds met. Dialogue marked completed.")
                break

        dialogue_id = logger.save_trace(
            seed=args.seed,
            dialogue_index=dlg_idx,
            persona=BASE_STYLE_TAG,
            target_intent=target_intent,
            sim_model=user_sim.model_name,
            target_model=target_bot.model_name,
            turns=turn_logs,
            status="COMPLETED" if dialogue_completed else "MAX_TURNS_REACHED",
        )
        return dialogue_id

    # Execute with concurrency
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = []
        for dlg_idx, row in enumerate(seed_rows, start=1):
            futures.append(executor.submit(run_single_dialogue, dlg_idx, row))
        
        for future in concurrent.futures.as_completed(futures):
            try:
                dialogue_id = future.result()
                completed_count += 1
                print(f" [{completed_count}/{num_dialogues}] Saved Dialogue [ID: {dialogue_id[:8]}]")
            except Exception as e:
                print(f" [ERROR] Dialogue failed: {e}")

    print(f"\nDone. {completed_count} dialogues written to: {resolved_output_dir}")


if __name__ == "__main__":
    main()
