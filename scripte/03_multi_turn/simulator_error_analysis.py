import os
import json
import argparse
import sys
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any
from openai import OpenAI
from dotenv import load_dotenv

# =====================================================================
# SECURITY FIX: Reliable absolute pathing for secrets
# =====================================================================
SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR.parent.parent / ".env"
load_dotenv(ENV_PATH)


def parse_llm_json(raw_text: str) -> Dict[str, Any]:
    """Extracts and parses JSON from raw LLM outputs."""
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {}


class ProfileOptimizer:
    """Analyzes INVALID_DRIFT dialogues and produces an updated, versioned profile JSON."""
    
    def __init__(self, model_name: str, api_key: str = None, base_url: str = None):
        self.model_name = os.getenv("JUDGE_MODEL_NAME", model_name)
        self.client = OpenAI(
            api_key=api_key or os.getenv("JUDGE_API_KEY", "dummy_key"),
            base_url=base_url or os.getenv("JUDGE_BASE_URL")
        )

    def optimize_profile(self, base_profile_path: str, judged_input_dir: str) -> str:
        summary_path = os.path.join(judged_input_dir, "batch_summary.json")
        if not os.path.exists(summary_path):
            print(f"[ERROR] Could not find '{summary_path}'.")
            sys.exit(1)

        if not os.path.exists(base_profile_path):
            print(f"[ERROR] Could not find base profile at '{base_profile_path}'.")
            sys.exit(1)

        with open(base_profile_path, "r", encoding="utf-8") as f:
            base_profile = json.load(f)

        with open(summary_path, "r", encoding="utf-8") as f:
            summary_data = json.load(f)

        # 1. Filter and Cluster Drift Failures
        drift_clusters = self._cluster_drifts(summary_data)

        if not drift_clusters:
            print("[INFO] No intent drift (INVALID_DRIFT) found! Simulator performed perfectly.")
            return None

        # 2. Build the Hybrid LLM Optimization Prompt
        prompt = self._build_meta_prompt(base_profile, drift_clusters)

        print(f"Generating optimized profile using {self.model_name}...")
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an Expert Prompt Engineer and Quality Assurance Architect for Conversational AI."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )

            raw_output = response.choices[0].message.content.strip()
            optimized_profile = parse_llm_json(raw_output)

            # Fallback checks to ensure base fields are preserved
            if "personas" not in optimized_profile:
                optimized_profile["personas"] = base_profile.get("personas", {})
            if "simulator_system_prompt" not in optimized_profile:
                optimized_profile["simulator_system_prompt"] = base_profile.get("simulator_system_prompt", "")
            if "target_bot_system_prompt" not in optimized_profile:
                optimized_profile["target_bot_system_prompt"] = base_profile.get("target_bot_system_prompt", "")

            # Mark versioning in profile name
            current_name = base_profile.get("profile_name", "Standard Profile")
            optimized_profile["profile_name"] = f"{current_name} (Optimized Iteration)"

            # Save the optimized profile into the judged run directory
            output_file = os.path.join(judged_input_dir, "optimized_profile.json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(optimized_profile, f, indent=2, ensure_ascii=False)

            # Also save dynamic constraints standalone for backward compatibility
            constraints_file = os.path.join(judged_input_dir, "dynamic_constraints.json")
            with open(constraints_file, "w", encoding="utf-8") as f:
                json.dump(optimized_profile.get("intent_constraints", {}), f, indent=2, ensure_ascii=False)

            print(f"\n[SUCCESS] Optimized Profile generated and saved to: {output_file}")
            return output_file

        except Exception as e:
            print(f"[ERROR] Failed to generate Optimized Profile: {e}")
            return None

    def _cluster_drifts(self, summary_data: Dict) -> Dict[str, List[Dict]]:
        """Filters out valid dialogues and clusters drift failures by Target Intent."""
        clusters = defaultdict(list)

        for persona, evaluations in summary_data.get("persona_scores", {}).items():
            for eval_data in evaluations:
                validity = eval_data.get("test_validity", "UNKNOWN")
                
                if str(validity).upper() == "INVALID_DRIFT":
                    intent = eval_data.get("target_intent", "unknown_intent")
                    drift_analysis = eval_data.get("drift_analysis") or {}
                    
                    clusters[intent].append({
                        "dialogue_id": eval_data["dialogue_id"],
                        "persona": persona,
                        "drift_reasoning": drift_analysis.get("drift_reasoning", ""),
                        "drifted_to_intent": drift_analysis.get("drifted_to_intent", ""),
                        "suggested_negative_constraints": drift_analysis.get("suggested_negative_constraints", [])
                    })

        return dict(clusters)

    def _build_meta_prompt(self, base_profile: Dict[str, Any], clusters: Dict[str, List[Dict]]) -> str:
        """Constructs the prompt containing base profile and clustered drift data."""
        prompt = (
            "You are an expert prompt optimizer for LLM user simulators.\n"
            "Below is the current BASE SIMULATOR PROFILE JSON, followed by a failure report of dialogues "
            "where the user simulator DRIFTED away from its assigned intent into neighboring topics.\n\n"
            "YOUR TASK:\n"
            "Generate a complete, NEW OPTIMIZED PROFILE JSON with two key enhancements:\n"
            "1. REFINE `simulator_system_prompt`: Slightly improve general clarity to encourage staying strictly on topic.\n"
            "2. ADD `intent_constraints`: Create a key `\"intent_constraints\"` mapping each failed `target_intent` "
            "to a list of 1-3 strict negative rules (e.g. `\"card_swallowed\": [\"DO NOT mention cash dispense issues\"]`).\n\n"
            "BASE PROFILE JSON:\n"
            f"{json.dumps(base_profile, indent=2)}\n\n"
            "DRIFT FAILURE REPORT:\n"
            f"{json.dumps(clusters, indent=2)}\n\n"
            "OUTPUT REQUIREMENT:\n"
            "Return ONLY a valid, complete JSON object matching the structure of the base profile, plus the new `\"intent_constraints\"` key."
        )
        return prompt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Meta-Judge Script to generate an Optimized Profile JSON with embedded intent constraints.")

    parser.add_argument("--profile", type=str, required=True, help="Path to base profile JSON")
    parser.add_argument("--input_dir", type=str, required=True, help="Path to judged run folder")
    parser.add_argument("--judge_model", type=str, default="openai/gpt-oss-120b", help="Model name for Meta-Judge")

    args = parser.parse_args()

    optimizer = ProfileOptimizer(model_name=args.judge_model)
    optimizer.optimize_profile(base_profile_path=args.profile, judged_input_dir=args.input_dir)
