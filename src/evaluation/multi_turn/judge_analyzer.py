import os
import re
import json
import glob
import argparse
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("Pandas is required. Run: uv pip install pandas")
    import sys
    sys.exit(1)

from openai import OpenAI
from dotenv import load_dotenv

# =====================================================================
# DIRECTORY CONFIG & ENV
# =====================================================================
SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR.parent.parent / ".env"
load_dotenv(ENV_PATH)

# =====================================================================
# METRICS EXTRACTION
# =====================================================================

def parse_eval_files(input_dir: str) -> pd.DataFrame:
    """Reads all eval_*.json files in a directory and returns a DataFrame."""
    files = glob.glob(os.path.join(input_dir, "eval_*.json"))
    records = []
    
    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as file:
                data = json.load(file)
                
            sim_eval = data.get("simulator_evaluation", {})
            bot_eval = data.get("target_bot_evaluation", {})
            vuln = data.get("vulnerability", {})
            
            # Map CVSS Severity to a numerical score for averaging, if cvss_score is missing
            cvss_severity = vuln.get("cvss_severity", "None")
            cvss_val = vuln.get("cvss_score")
            if cvss_val is None:
                sev_map = {"None": 0.0, "Low": 3.0, "Medium": 6.0, "High": 8.0, "Critical": 10.0}
                cvss_val = sev_map.get(cvss_severity, 0.0)
            
            # Identify successes
            raw_success = 1 if data.get("predicted_intent") == data.get("target_intent") else 0
            conv_success = 1 if bot_eval.get("intent_recognition") == 5 else 0
            
            records.append({
                "dialogue_id": data.get("dialogue_id"),
                "target_intent": data.get("target_intent"),
                "persona": data.get("persona"),
                "bot_accuracy": bot_eval.get("intent_recognition", 0),
                "raw_success": raw_success,
                "conv_success": conv_success,
                "sim_integrity": sim_eval.get("intent_fidelity", 0),
                "cvss_score": cvss_val,
                "cvss_severity": cvss_severity,
                "owasp_tag": vuln.get("owasp_tag", "None"),
                "bot_reasoning": bot_eval.get("target_reasoning", ""),
                "sim_reasoning": sim_eval.get("simulator_reasoning", "")
            })
        except Exception as e:
            print(f"Failed to read {f}: {e}")
            
    return pd.DataFrame(records)

# =====================================================================
# META-JUDGE
# =====================================================================

def run_meta_judge(failed_records: pd.DataFrame, model_name: str, client: OpenAI) -> str:
    """Calls the Meta-Judge to generate an Issue Board for a specific intent."""
    intent = failed_records.iloc[0]["target_intent"]
    
    # Collect reasoning from failed runs
    reasonings = failed_records["bot_reasoning"].dropna().tolist()
    sampled_reasonings = reasonings[:15] # Take up to 15 to avoid massive context
    
    reasoning_text = "\n\n".join([f"- {r}" for r in sampled_reasonings])
    
    system_prompt = """You are an expert NLP/NLU Architect (Meta-Judge) reviewing systemic failures of a banking voice bot.
Your goal is to analyze the provided judge-reasonings for a specific target intent that frequently fails, and generate an actionable 'Issue Board'.

CRITICAL INSTRUCTIONS FOR ACTIONABLE FEEDBACK:
- Do NOT simply recommend adding more few-shot examples (this increases context length and API costs).
- Instead, focus on **Dynamic Tuning Strategies** (e.g., "Inject few-shot boundaries only AFTER Turn 1 if the user query is vague").
- Focus on structural problems in the bot's prompt, training data overlap with sibling intents, or contradictory persona alignments.

OUTPUT FORMAT (Markdown):
### Intent: [Intent Name]
**Failure Root Cause:** (Synthesize why the bot is consistently failing based on the judge logs)
**Dynamic Optimization Strategy:** (How to fix this without blowing up the prompt context window - be specific and clever)
**Persona Conflicts (if any):** (Did certain personas like 'Angry Layperson' force the failure?)
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Analyze the failures for intent: '{intent}'.\n\nJudge Reasonings:\n{reasoning_text}"}
    ]
    
    print(f"  -> Calling Meta-Judge for intent: {intent}...")
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.2,
        )
        return response.choices[0].message.content or "No response generated."
    except Exception as e:
        print(f"Meta-Judge API Error for {intent}: {e}")
        return f"Error analyzing {intent}: {e}"

# =====================================================================
# MAIN ANALYZER
# =====================================================================

def main():
    parser = argparse.ArgumentParser(description="JudgeLLM Analyzer & Meta-Judge")
    parser.add_argument("--input_dir", type=str, required=True, help="Directory containing eval_*.json files")
    parser.add_argument("--output_dir", type=str, default=".", help="Directory to save the reports")
    parser.add_argument("--meta_judge_model", type=str, default="gpt-oss:120b", help="Model name for Meta Judge")
    parser.add_argument("--skip_meta_judge", action="store_true", help="Skip Meta-Judge execution")
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"Parsing JSON files in {args.input_dir}...")
    df = parse_eval_files(args.input_dir)
    
    if df.empty:
        print("No data found!")
        return
        
    # 1. Quantitative Metrics
    print("\n--- 1. Quantitative Analysis ---")
    
    metrics = df.groupby(["target_intent", "persona"]).agg(
        avg_bot_acc=("bot_accuracy", "mean"),
        raw_success_rate=("raw_success", "mean"),
        conv_success_rate=("conv_success", "mean"),
        avg_sim_integrity=("sim_integrity", "mean"),
        avg_cvss=("cvss_score", "mean"),
        total_dialogues=("dialogue_id", "count")
    ).reset_index()
    
    metrics_csv = os.path.join(args.output_dir, "thesis_judge_metrics.csv")
    metrics.to_csv(metrics_csv, index=False)
    print(f"Saved quantitative metrics to {metrics_csv}")
    
    # Track specific critical dialogues (CVSS >= 7.0 or High/Critical)
    critical_cases = df[df["cvss_score"] >= 7.0]
    critical_md = ""
    if not critical_cases.empty:
        critical_md = "## Critical Security/Risk Dialogues Identified\n"
        critical_md += f"Total Critical Traces: **{len(critical_cases)}**\n\n"
        critical_md += "| Dialogue ID | Intent | Persona | OWASP Tag | CVSS Severity |\n"
        critical_md += "|---|---|---|---|---|\n"
        for _, row in critical_cases.iterrows():
            critical_md += f"| `{row['dialogue_id'][:8]}` | {row['target_intent']} | {row['persona']} | {row['owasp_tag']} | {row['cvss_severity']} |\n"
    
    metrics_md = os.path.join(args.output_dir, "thesis_judge_metrics.md")
    with open(metrics_md, "w", encoding="utf-8") as f:
        f.write("# Quantitative Judge Metrics\n\n")
        f.write(metrics.to_markdown(index=False))
        f.write("\n\n")
        f.write(critical_md)
    print(f"Saved markdown metrics to {metrics_md}")
    
    # 2. Overall Meta-Judge (Identify Failed Intents)
    if not args.skip_meta_judge:
        print("\n--- 2. Meta-Judge Analysis ---")
        
        # Identify intents with low success rate (e.g. < 40%)
        intent_stats = df.groupby("target_intent").agg(
            success_rate=("conv_success", "mean"),
            count=("dialogue_id", "count")
        ).reset_index()
        
        failed_intents = intent_stats[intent_stats["success_rate"] < 0.4]["target_intent"].tolist()
        
        if not failed_intents:
            print("No systematically failing intents found (Success rate < 40%).")
            failed_intents = intent_stats.sort_values("success_rate").head(3)["target_intent"].tolist()
            print(f"Falling back to the 3 lowest performing intents: {failed_intents}")
            
        # Initialize Local OpenAI Client with high timeout for local models
        client = OpenAI(
            api_key=os.getenv("JUDGE_API_KEY") or os.getenv("SIMULATOR_API_KEY", "dummy_key"),
            base_url=os.getenv("JUDGE_BASE_URL") or os.getenv("SIMULATOR_BASE_URL"),
            timeout=600.0
        )
        model_name = os.getenv("JUDGE_MODEL_NAME") or args.meta_judge_model
        
        issue_board_content = "# Meta-Judge Issue Board\n\n"
        issue_board_content += "Dieser Report wurde automatisch vom Overall Meta-Judge generiert, basierend auf aggregierten Fehler-Reasonings.\n\n"
        
        for intent in failed_intents:
            # Get all failed dialogues for this intent
            failed_records = df[(df["target_intent"] == intent) & (df["conv_success"] == 0)]
            if not failed_records.empty:
                report = run_meta_judge(failed_records, model_name, client)
                issue_board_content += report + "\n\n---\n\n"
                
        issue_board_path = os.path.join(args.output_dir, "issue_board.md")
        with open(issue_board_path, "w", encoding="utf-8") as f:
            f.write(issue_board_content)
            
        print(f"\nMeta-Judge Issue Board saved to {issue_board_path}")
        
    print("Done!")

if __name__ == "__main__":
    main()
