import os
import json
import argparse
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any

# =====================================================================
# PERSONA PERFORMANCE ANALYTICS & BENCHMARKING REPORT
# =====================================================================

def normalize_persona_name(name: str) -> str:
    """Normalizes persona string by replacing Unicode hyphens and extra spaces."""
    if not name:
        return "Unknown"
    return name.replace('\u2011', '-').replace('\u2013', '-').strip()

class PersonaAnalytics:
    """Calculates persona-level communication, classification, and drift metrics."""
    
    def __init__(self, judged_run_dir: str):
        self.judged_run_dir = Path(judged_run_dir)
        self.summary_path = self.judged_run_dir / "batch_summary.json"
        
        if not self.summary_path.exists():
            raise FileNotFoundError(f"Could not locate 'batch_summary.json' in {self.judged_run_dir}")
            
        with open(self.summary_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def generate_report(self) -> Dict[str, Any]:
        raw_persona_scores = self.data.get("persona_scores", {})
        
        # Group by normalized persona name to prevent duplicate rows due to Unicode hyphens
        grouped_scores = defaultdict(list)
        for persona_name, dialogues in raw_persona_scores.items():
            norm_name = normalize_persona_name(persona_name)
            grouped_scores[norm_name].extend(dialogues)

        metrics_by_persona = {}

        for persona, dialogues in grouped_scores.items():
            total = len(dialogues)
            if total == 0:
                continue

            valid_count = 0
            drift_count = 0
            exact_match_count = 0
            close_match_count = 0

            sim_adherence_sum = 0
            sim_fidelity_sum = 0
            bot_empathy_sum = 0
            bot_clarity_sum = 0
            bot_efficiency_sum = 0
            
            # Severity counters
            severity_counts = defaultdict(int)

            for d in dialogues:
                validity = str(d.get("test_validity", "")).upper()
                if validity == "VALID":
                    valid_count += 1
                elif validity == "INVALID_DRIFT":
                    drift_count += 1

                # Simulator scores
                sim_sc = d.get("sim_scores") or {}
                sim_adherence_sum += float(sim_sc.get("persona_adherence", 0))
                sim_fidelity_sum += float(sim_sc.get("intent_fidelity", 0))

                # Bot scores
                bot_sc = d.get("bot_scores") or {}
                bot_rec = bot_sc.get("intent_recognition")
                
                # Check classification accuracy:
                # 5/5 = Exact Match, 4/5 = Close/Sibling Match
                if isinstance(bot_rec, (int, float)):
                    if bot_rec >= 5:
                        exact_match_count += 1
                        close_match_count += 1
                    elif bot_rec >= 4:
                        close_match_count += 1
                elif isinstance(bot_rec, dict):
                    score = bot_rec.get("score", 0)
                    if bot_rec.get("status") == "SUCCESS" or bot_rec.get("correct", False) or score >= 5:
                        exact_match_count += 1
                        close_match_count += 1
                    elif score >= 4:
                        close_match_count += 1

                bot_empathy_sum += float(bot_sc.get("naturalness_empathy", bot_sc.get("empathy", 0)))
                bot_clarity_sum += float(bot_sc.get("goal_achievement", bot_sc.get("clarity", 0)))
                bot_efficiency_sum += float(bot_sc.get("efficiency", 0))

                sev = d.get("cvss_severity", "None")
                severity_counts[sev] += 1

            metrics_by_persona[persona] = {
                "total_dialogues": total,
                "valid_dialogues": valid_count,
                "valid_rate_pct": round((valid_count / total) * 100, 1),
                "drift_count": drift_count,
                "drift_rate_pct": round((drift_count / total) * 100, 1),
                "exact_accuracy_pct": round((exact_match_count / total) * 100, 1),
                "close_accuracy_pct": round((close_match_count / total) * 100, 1),
                "avg_sim_persona_adherence": round(sim_adherence_sum / total, 2),
                "avg_sim_intent_fidelity": round(sim_fidelity_sum / total, 2),
                "avg_bot_empathy": round(bot_empathy_sum / total, 2),
                "avg_bot_clarity": round(bot_clarity_sum / total, 2),
                "avg_bot_efficiency": round(bot_efficiency_sum / total, 2),
                "severities": dict(severity_counts)
            }

        return metrics_by_persona

    def export_markdown_report(self, metrics: Dict[str, Any]) -> str:
        report_lines = [
            "# Persona Performance & Classification Benchmark Report",
            f"**Evaluated Run Directory:** `{self.judged_run_dir.name}`\n",
            "## 📊 Executive Summary Table",
            "| Persona | Dialogues | Exact Match % (5/5) | Close Match % (>=4/5) | Sim Adherence (1-5) | Bot Empathy (1-5) | Bot Goal Achievement (1-5) | Drift % | Valid % |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |"
        ]

        for persona, m in metrics.items():
            report_lines.append(
                f"| **{persona}** | {m['total_dialogues']} | {m['exact_accuracy_pct']}% | {m['close_accuracy_pct']}% | {m['avg_sim_persona_adherence']} | {m['avg_bot_empathy']} | {m['avg_bot_clarity']} | {m['drift_rate_pct']}% | {m['valid_rate_pct']}% |"
            )

        report_lines.extend([
            "\n## 🔍 Deep-Dive Insights Per Persona",
        ])

        for persona, m in metrics.items():
            report_lines.extend([
                f"### 🎭 Persona: {persona}",
                f"- **Classification Accuracy:** Exact Match = `{m['exact_accuracy_pct']}%` | Close/Sibling Match = `{m['close_accuracy_pct']}%`",
                f"- **Simulator Quality:** Persona Adherence = `{m['avg_sim_persona_adherence']}/5`, Intent Fidelity = `{m['avg_sim_intent_fidelity']}/5`",
                f"- **Target Bot Performance:** Empathy/Naturalness = `{m['avg_bot_empathy']}/5`, Goal Achievement = `{m['avg_bot_clarity']}/5`, Efficiency = `{m['avg_bot_efficiency']}/5`",
                f"- **Dialogue Validity:** `{m['valid_rate_pct']}%` Valid | Drift Rate: `{m['drift_rate_pct']}%`",
                f"- **Vulnerability Distribution:** {json.dumps(m['severities'])}\n"
            ])

        markdown_content = "\n".join(report_lines)
        
        output_file = self.judged_run_dir / "persona_benchmark_report.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        print(f"[SUCCESS] Persona Benchmark Report saved to: {output_file}")
        return markdown_content


def print_cli_table(metrics: Dict[str, Any]):
    print("\n" + "=" * 115)
    print(" PERSONA PERFORMANCE & COMMUNICATION COMPARISON BENCHMARK")
    print("=" * 115)
    header = f"{'PERSONA':<22} | {'EXACT ACC%':<10} | {'CLOSE ACC%':<10} | {'ADH (1-5)':<9} | {'EMP (1-5)':<9} | {'GOAL (1-5)':<10} | {'DRIFT %':<7}"
    print(header)
    print("-" * 115)

    for persona, m in metrics.items():
        row = (
            f"{persona:<22} | "
            f"{m['exact_accuracy_pct']:>9.1f}% | "
            f"{m['close_accuracy_pct']:>9.1f}% | "
            f"{m['avg_sim_persona_adherence']:>9.2f} | "
            f"{m['avg_bot_empathy']:>9.2f} | "
            f"{m['avg_bot_clarity']:>10.2f} | "
            f"{m['drift_rate_pct']:>6.1f}%"
        )
        print(row)
    print("=" * 115 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Persona Benchmark & Communication Report.")
    parser.add_argument("--input_dir", type=str, required=True,
                        help="Path to judged run directory containing batch_summary.json")

    args = parser.parse_args()
    
    analytics = PersonaAnalytics(judged_run_dir=args.input_dir)
    metrics = analytics.generate_report()
    print_cli_table(metrics)
    analytics.export_markdown_report(metrics)
