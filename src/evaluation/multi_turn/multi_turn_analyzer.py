import os
import json
import argparse
from pathlib import Path
from collections import defaultdict
import csv

def analyze_logs(base_dir: str):
    base_path = Path(base_dir)
    if not base_path.exists():
        print(f"Error: Directory {base_dir} does not exist.")
        return

    # Metrics storage
    total_dialogues = 0
    status_counts = defaultdict(int)
    
    # Global Turn metrics
    successful_turns = []
    failed_turns = []

    # Persona based metrics
    persona_stats = defaultdict(lambda: {
        'total': 0,
        'completed': 0,
        'failed_out_of_cluster': 0,
        'max_turns_reached': 0,
        'successful_turns': [],
        'intents': defaultdict(lambda: {'total': 0, 'completed': 0})
    })
    
    # Model info
    target_model = "Unknown"
    sim_model = "Unknown"

    print(f"Scanning directory: {base_path} for JSON traces...")
    
    # Recursively find all json files
    for json_file in base_path.rglob("*.json"):
        if json_file.name in ["intent_clusters_cache.json", "batch_summary.json"]:
            continue
            
        with open(json_file, 'r', encoding='utf-8') as f:
            try:
                trace = json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Could not parse {json_file}")
                continue

        total_dialogues += 1
        status = trace.get("status", "UNKNOWN")
        turns_count = trace.get("total_turns", 0)
        persona = trace.get("persona", "Unknown")
        target_model = trace.get("target_model", target_model)
        sim_model = trace.get("sim_model", sim_model)

        status_counts[status] += 1
        
        persona_stats[persona]['total'] += 1
        target_intent = trace.get("target_intent", "Unknown")
        persona_stats[persona]['intents'][target_intent]['total'] += 1

        if status == "COMPLETED":
            successful_turns.append(turns_count)
            persona_stats[persona]['completed'] += 1
            persona_stats[persona]['successful_turns'].append(turns_count)
            persona_stats[persona]['intents'][target_intent]['completed'] += 1
        elif status == "FAILED_OUT_OF_CLUSTER":
            failed_turns.append(turns_count)
            persona_stats[persona]['failed_out_of_cluster'] += 1
        elif status == "FAILED_WRONG_INTENT_IN_CLUSTER":
            failed_turns.append(turns_count)
            persona_stats[persona]['failed_wrong_intent'] = persona_stats[persona].get('failed_wrong_intent', 0) + 1
        elif status == "MAX_TURNS_REACHED":
            failed_turns.append(turns_count)
            persona_stats[persona]['max_turns_reached'] += 1

    if total_dialogues == 0:
        print("No dialogue traces found.")
        return

    # Compute aggregates
    avg_success_turns = sum(successful_turns) / len(successful_turns) if successful_turns else 0.0
    avg_fail_turns = sum(failed_turns) / len(failed_turns) if failed_turns else 0.0
    
    success_rate = (status_counts.get("COMPLETED", 0) / total_dialogues) * 100
    premature_rate = (status_counts.get("FAILED_OUT_OF_CLUSTER", 0) / total_dialogues) * 100
    wrong_intent_rate = (status_counts.get("FAILED_WRONG_INTENT_IN_CLUSTER", 0) / total_dialogues) * 100

    # Print Terminal Output
    print("\n" + "="*50)
    print(" MULTI-TURN EVALUATION SUMMARY")
    print("="*50)
    print(f"Target Model:    {target_model}")
    print(f"Simulator Model: {sim_model}")
    print(f"Total Dialogues: {total_dialogues}")
    print("-" * 50)
    print(f"Success Rate (COMPLETED):            {success_rate:.1f}% ({status_counts.get('COMPLETED', 0)})")
    print(f"Premature Classification (OUT OF CLUSTER): {premature_rate:.1f}% ({status_counts.get('FAILED_OUT_OF_CLUSTER', 0)})")
    print(f"Wrong Intent (IN CLUSTER):           {wrong_intent_rate:.1f}% ({status_counts.get('FAILED_WRONG_INTENT_IN_CLUSTER', 0)})")
    print(f"Max Turns Reached (Timeout):         {(status_counts.get('MAX_TURNS_REACHED', 0) / total_dialogues)*100:.1f}% ({status_counts.get('MAX_TURNS_REACHED', 0)})")
    print("-" * 50)
    print(f"Avg Turns to Success: {avg_success_turns:.2f}")
    print(f"Avg Turns to Failure: {avg_fail_turns:.2f}")
    print("="*50)

    # Generate Markdown Report for Thesis
    md_report_path = base_path / "thesis_multi_turn_report.md"
    with open(md_report_path, "w", encoding="utf-8") as md:
        md.write("# Multi-Turn Intent Recognition Evaluation Report\n\n")
        md.write(f"**Target Model:** {target_model} | **Simulator Model:** {sim_model} | **Total Dialogues:** {total_dialogues}\n\n")
        
        md.write("## Overall Performance Metrics\n")
        md.write("| Metric | Value |\n|---|---|\n")
        md.write(f"| Dialogue Success Rate (Context Maintained) | {success_rate:.2f}% |\n")
        md.write(f"| Premature Classification Rate (Out of Cluster) | {premature_rate:.2f}% |\n")
        md.write(f"| Inconclusive Dialogues (Max Turns Reached) | {(status_counts.get('MAX_TURNS_REACHED', 0) / total_dialogues)*100:.2f}% |\n")
        md.write(f"| Average Turns to Resolution | {avg_success_turns:.2f} |\n\n")

        md.write("## Persona Impact Analysis (Linguistic Variance)\n")
        md.write("This table demonstrates the system's robustness across different user communication styles.\n\n")
        md.write("| Persona | Total | Success Rate | Premature Fail Rate | Avg Turns to Resolution |\n")
        md.write("|---|---|---|---|---|\n")
        
        for p, stats in sorted(persona_stats.items()):
            p_total = stats['total']
            p_succ = (stats['completed'] / p_total) * 100
            p_fail = (stats['failed_out_of_cluster'] / p_total) * 100
            p_avg = sum(stats['successful_turns']) / len(stats['successful_turns']) if stats['successful_turns'] else 0.0
            md.write(f"| {p} | {p_total} | {p_succ:.1f}% | {p_fail:.1f}% | {p_avg:.2f} |\n")

        md.write("\n## Detailed Persona Breakdowns\n")
        md.write("Performance of specific intents for each persona.\n\n")
        
        for p, stats in sorted(persona_stats.items()):
            zero_percent_count = sum(1 for i_stats in stats['intents'].values() if (i_stats['completed'] / i_stats['total']) == 0.0 and i_stats['total'] > 0)
            
            md.write(f"### {p}\n")
            md.write(f"**Intents with 0% Success Rate:** {zero_percent_count}\n\n")
            md.write("| Intent | Total | Success Rate |\n")
            md.write("|---|---|---|\n")
            # Sort intents by success rate (descending, so best are at the top)
            sorted_intents = sorted(
                stats['intents'].items(), 
                key=lambda item: (item[1]['completed'] / item[1]['total']) if item[1]['total'] > 0 else 0,
                reverse=True
            )
            for intent, i_stats in sorted_intents:
                i_total = i_stats['total']
                i_succ = (i_stats['completed'] / i_total) * 100 if i_total > 0 else 0
                md.write(f"| {intent} | {i_total} | {i_succ:.1f}% |\n")
            md.write("\n")

    print(f"\n[Success] Generated thesis report at: {md_report_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze Multi-Turn JSON logs for Thesis Evaluation")
    parser.add_argument("--logs_dir", type=str, default="../../logs/multi_turn_dialogues", help="Path to the root logs directory")
    args = parser.parse_args()
    
    analyze_logs(args.logs_dir)
