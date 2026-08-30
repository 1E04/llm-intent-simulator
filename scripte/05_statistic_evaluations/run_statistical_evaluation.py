import os
import json
import argparse
from pathlib import Path
from collections import defaultdict

def normalize_persona_name(name: str) -> str:
    """Normalizes persona string by replacing Unicode hyphens and extra spaces."""
    if not name:
        return "Unknown"
    return name.replace('\u2011', '-').replace('\u2013', '-').strip()

def build_trace_map(base_logs_dir: Path):
    print("Building dialogue trace map...")
    trace_map = {}
    for root, dirs, files in os.walk(base_logs_dir):
        for file in files:
            if file.startswith("dialogue_") and file.endswith(".json"):
                filepath = Path(root) / file
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        d_id = data.get("dialogue_id")
                        if d_id:
                            trace_map[d_id] = data
                except Exception:
                    pass
    print(f"Loaded {len(trace_map)} dialogue traces.")
    return trace_map

def generate_statistics(base_dir: str):
    base_logs_dir = Path(base_dir)
    
    if not base_logs_dir.exists():
        print(f"Directory {base_logs_dir} does not exist.")
        return

    # Load trace map once to quickly find transitions and turn counts
    trace_map = build_trace_map(base_logs_dir)

    # Find all run_ directories recursively
    run_dirs = []
    for root, dirs, files in os.walk(base_logs_dir):
        for d in dirs:
            if d.startswith("run_"):
                run_dirs.append(Path(root) / d)

    print(f"Found {len(run_dirs)} run directories.")

    for run_dir in run_dirs:
        eval_files = list(run_dir.glob("eval_*.json"))
        if not eval_files:
            continue
            
        persona_stats = defaultdict(lambda: {"total": 0, "accurate": 0, "total_turns": 0})
        intent_stats = defaultdict(lambda: {"total": 0, "accurate": 0})
        misclassifications = defaultdict(int)
        
        total_dialogues = 0
        total_accurate = 0
        total_turns = 0
        
        right_to_wrong = 0
        wrong_to_right = 0
        
        for eval_file in eval_files:
            with open(eval_file, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    print(f"Warning: Could not decode JSON in {eval_file}")
                    continue
            
            d_id = data.get("dialogue_id")
            persona = normalize_persona_name(data.get("persona", "Unknown"))
            target_intent = data.get("target_intent", "Unknown")
            predicted_intent = data.get("predicted_intent")
            scorecard = data.get("scorecard", {})
            intent_rec = scorecard.get("intent_recognition", 0)
            
            # Determine if accurate (Score of 5 is Exact Match)
            is_accurate = False
            
            if predicted_intent is not None:
                is_accurate = (predicted_intent == target_intent)
            else:
                if isinstance(intent_rec, (int, float)):
                    if intent_rec >= 5:
                        is_accurate = True
                elif isinstance(intent_rec, dict):
                    score = intent_rec.get("score", 0)
                    if intent_rec.get("status") == "SUCCESS" or intent_rec.get("correct", False) or score >= 5:
                        is_accurate = True
                        
            # Analyze transitions from trace if available
            turns_count = data.get("total_turns", 0)
            trace = trace_map.get(d_id)
            if trace:
                turns = trace.get("turns", [])
                if turns:
                    turns_count = len(turns)
                    prev_accurate = None
                    for t in turns:
                        pred = t.get("predicted_intent")
                        if pred:
                            curr_accurate = (pred == target_intent)
                            if prev_accurate is not None:
                                if prev_accurate and not curr_accurate:
                                    right_to_wrong += 1
                                elif not prev_accurate and curr_accurate:
                                    wrong_to_right += 1
                            prev_accurate = curr_accurate
            
            persona_stats[persona]["total"] += 1
            persona_stats[persona]["total_turns"] += turns_count
            total_dialogues += 1
            total_turns += turns_count
            
            intent_stats[target_intent]["total"] += 1
            
            if is_accurate:
                persona_stats[persona]["accurate"] += 1
                total_accurate += 1
                intent_stats[target_intent]["accurate"] += 1
            else:
                if predicted_intent and predicted_intent != "Unknown":
                    pair_key = f"{target_intent} -> {predicted_intent}"
                    misclassifications[pair_key] += 1

        if total_dialogues == 0:
            continue

        avg_turns_overall = total_turns / total_dialogues if total_dialogues > 0 else 0

        report_lines = [
            f"# Statistical Evaluation for {run_dir.name}",
            "",
            "## Overall Metrics",
            f"- **Total Dialogues:** {total_dialogues}",
            f"- **Overall Accurate (Absolute):** {total_accurate}",
            f"- **Overall Accuracy (Percentage):** {(total_accurate / total_dialogues * 100):.2f}%",
            f"- **Average Turns per Dialogue:** {avg_turns_overall:.2f}",
            "",
            "## Prediction Stability",
            f"- **Right-to-Wrong Flips (Total across run):** {right_to_wrong}",
            f"- **Wrong-to-Right Flips (Total across run):** {wrong_to_right}",
            "",
            "## Accuracy and Average Turns by Persona Style",
            "| Persona | Total Dialogues | Accurate (Abs) | Accuracy (%) | Avg Turns |",
            "|---------|-----------------|----------------|--------------|-----------|"
        ]
        
        # Sort by persona name for consistent reporting
        for persona in sorted(persona_stats.keys()):
            stats = persona_stats[persona]
            p_total = stats["total"]
            p_acc = stats["accurate"]
            p_turns = stats["total_turns"]
            p_pct = (p_acc / p_total * 100) if p_total > 0 else 0
            p_avg_turns = p_turns / p_total if p_total > 0 else 0
            
            report_lines.append(
                f"| {persona} | {p_total} | {p_acc} | {p_pct:.2f}% | {p_avg_turns:.2f} |"
            )

        report_lines.append("")
        report_lines.append("## Best and Worst Predicted Labels")
        report_lines.append("| Target Intent | Total | Accurate | Accuracy (%) |")
        report_lines.append("|---------------|-------|----------|--------------|")
        
        # Sort intents by accuracy descending, then by total descending
        intent_list = []
        for intent, stats in intent_stats.items():
            i_total = stats["total"]
            i_acc = stats["accurate"]
            i_pct = (i_acc / i_total * 100) if i_total > 0 else 0
            intent_list.append((intent, i_total, i_acc, i_pct))
            
        intent_list.sort(key=lambda x: (x[3], x[1]), reverse=True)
        
        for intent, i_total, i_acc, i_pct in intent_list:
            report_lines.append(f"| {intent} | {i_total} | {i_acc} | {i_pct:.2f}% |")

        if misclassifications:
            report_lines.append("")
            report_lines.append("## Top Misclassifications (Target -> Predicted)")
            report_lines.append("| Target Intent | Predicted Intent | Count |")
            report_lines.append("|---------------|------------------|-------|")
            sorted_misclass = sorted(misclassifications.items(), key=lambda x: x[1], reverse=True)
            for pair, count in sorted_misclass[:20]: # Show top 20 misclassifications
                target, predicted = pair.split(" -> ")
                report_lines.append(f"| {target} | {predicted} | {count} |")

        report_path = run_dir / "accuracy_statistics.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_lines) + "\n")
            
        print(f"Created statistical evaluation in: {report_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate statistical evaluations for run directories.")
    parser.add_argument("--base_dir", type=str, default="logs", help="Base directory to search for run_ folders.")
    args = parser.parse_args()
    
    generate_statistics(args.base_dir)
