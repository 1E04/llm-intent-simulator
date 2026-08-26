import os
import sys
import argparse
import subprocess
from pathlib import Path
import time

def print_step(title: str):
    print("\n" + "=" * 60)
    print(f" {title.upper()}")
    print("=" * 60)

def get_latest_dir(base_dir: Path, prefix: str) -> Path:
    """Finds the most recently modified directory matching a prefix."""
    if not base_dir.exists():
        return None
    dirs = [d for d in base_dir.glob(f"{prefix}*") if d.is_dir()]
    if not dirs:
        return None
    return max(dirs, key=os.path.getmtime)

def main():
    parser = argparse.ArgumentParser(description="Automated Simulator Feedback Loop Pipeline")
    parser.add_argument("--profile", type=str, default="../profiles/standard_en.json")
    parser.add_argument("--num_dialogues", type=int, default=5)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--csv_path", type=str, default="../../dataset/single-turn/banking77_test_labels_clean.csv")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    base_logs_dir = script_dir.parent.parent / "logs"
    sim_logs_dir = base_logs_dir / "multi_turn_dialogues" / "personas"
    judge_logs_dir = base_logs_dir / "judged_dialogues" / "personas"

    python_exe = sys.executable

    # =========================================================
    # STEP 1: Initial Simulation
    # =========================================================
    print_step("Step 1: Initial Simulation Run (Base Prompts)")
    sim_cmd = [
        python_exe, "multi-turn-simulator.py",
        "--profile", args.profile,
        "--per_intent", str(args.num_dialogues),
        "--concurrency", str(args.concurrency),
        "--csv_path", args.csv_path
    ]
    subprocess.run(sim_cmd, check=True, cwd=script_dir)

    time.sleep(1) # Ensure file system sync
    latest_sim_run = get_latest_dir(sim_logs_dir, "run_")
    if not latest_sim_run:
        print("[ERROR] Could not find the generated simulation directory.")
        sys.exit(1)

    # =========================================================
    # STEP 2: Judge Evaluation & Drift Detection
    # =========================================================
    print_step(f"Step 2: Judge Evaluation on {latest_sim_run.name}")
    judge_cmd = [
        python_exe, "judge_llm.py",
        "--input_dir", str(latest_sim_run),
        "--output_base_dir", str(judge_logs_dir),
        "--concurrency", str(args.concurrency)
    ]
    subprocess.run(judge_cmd, check=True, cwd=script_dir)

    time.sleep(1)
    import re
    match = re.search(r"^(run_\d+)", latest_sim_run.name)
    run_prefix = match.group(1) if match else latest_sim_run.name
    latest_judged_run = get_latest_dir(judge_logs_dir, run_prefix)
    if not latest_judged_run:
        print("[ERROR] Could not find the judged evaluation directory.")
        sys.exit(1)

    # =========================================================
    # STEP 3: Profile Optimization & Dynamic Constraint Generation
    # =========================================================
    print_step(f"Step 3: Profile Optimization on {latest_judged_run.name}")
    analyzer_cmd = [
        python_exe, "simulator_error_analysis.py",
        "--profile", args.profile,
        "--input_dir", str(latest_judged_run)
    ]
    subprocess.run(analyzer_cmd, check=True, cwd=script_dir)

    optimized_profile_path = latest_judged_run / "optimized_profile.json"
    if not optimized_profile_path.exists():
        print("\n[SUCCESS] No intent drift found! The simulator performed perfectly.")
        sys.exit(0)

    # =========================================================
    # STEP 4: Targeted Re-Execution (Self-Healing via Optimized Profile)
    # =========================================================
    print_step("Step 4: Targeted Re-Execution (With Optimized Profile)")
    print(f"Using optimized profile: {optimized_profile_path}")
    
    rerun_cmd = [
        python_exe, "multi-turn-simulator.py",
        "--profile", str(optimized_profile_path),
        "--num_dialogues", str(args.num_dialogues),
        "--concurrency", str(args.concurrency),
        "--csv_path", args.csv_path
    ]
    subprocess.run(rerun_cmd, check=True, cwd=script_dir)

    time.sleep(1)
    second_sim_run = get_latest_dir(sim_logs_dir, "run_")
    
    print_step(f"Step 5: Final Validation Judge on {second_sim_run.name}")
    final_judge_cmd = [
        python_exe, "judge_llm.py",
        "--input_dir", str(second_sim_run),
        "--output_base_dir", str(judge_logs_dir),
        "--concurrency", str(args.concurrency)
    ]
    subprocess.run(final_judge_cmd, check=True, cwd=script_dir)

    time.sleep(1)
    match_second = re.search(r"^(run_\d+)", second_sim_run.name)
    second_prefix = match_second.group(1) if match_second else second_sim_run.name
    final_judged_run = get_latest_dir(judge_logs_dir, second_prefix)

    print_step("Step 6: Persona Benchmark & Analytics Report")
    analytics_cmd = [
        python_exe, "persona_performance_analytics.py",
        "--input_dir", str(final_judged_run)
    ]
    subprocess.run(analytics_cmd, check=True, cwd=script_dir)

    print("\n" + "=" * 60)
    print(" PIPELINE COMPLETE: Self-Healing Simulator Loop Finished")
    print(f" Initial Run Judged:  {latest_judged_run}")
    print(f" Final Run Judged:    {final_judged_run}")
    print("=" * 60)

if __name__ == "__main__":
    main()
