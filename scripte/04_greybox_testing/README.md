# 🔲 Greybox Testing Pipeline (`scripte/04_greybox_testing/`)

This directory contains the **Greybox Evaluation Pipeline** for testing external LLM-driven voice bots via HTTP endpoints.

---

## 🎯 Greybox Methodology

In a **Greybox** test, the target conversational agent is treated as a remote service accessed over HTTP. The target system returns limited internal status alongside its reply:
1. **Predicted Intent** (label string, e.g., `predicted_intent`).
2. **Response Text** (the spoken reply).
3. *(Optional)* **Dialogue Completion Flag** (`dialogue_completed`).

*(Note: Internal confidence scores and full N-best lists are not exposed by the target service).*

---

## 📁 File Overview

* **`mock_target_server.py`**: A FastAPI/Uvicorn HTTP REST server simulating an external voice bot endpoint (`http://localhost:8000/chat`). It evaluates conversation histories against Banking77 labels and returns the predicted intent, text reply, and completion status.
* **`greybox_simulator.py`**: The multi-turn test harness. Acts as customer personas, sends conversation history payloads to the external HTTP target API, and logs dialogue traces to JSON files.
* **`greybox_judge.py`**: LLM-as-a-Judge script. Reads the greybox JSON dialogue traces, performs deterministic statistical match verification between ground-truth and predicted labels, and executes qualitative LLM evaluation.

---

## 🚀 How to Run the Pipeline

### Step 1: Start the Mock Target API Server (Optional)
If testing against a local mock server:
```bash
python mock_target_server.py
```
* The server listens on `http://localhost:8000/chat`.
* It auto-detects `.env` credentials (`TARGET_API_KEY`, `TARGET_BASE_URL`, `TARGET_MODEL_NAME`).

---

### Step 2: Generate Dialogues (`greybox_simulator.py`)

Run the simulator targeting the external HTTP endpoint:

```bash
python greybox_simulator.py \
  --target_url "http://localhost:8000/chat" \
  --target_identifier "gpt-5.4-nano" \
  --num_dialogues 5 \
  --max_turns 5
```

**CLI Argument Reference**:
* `--profile`: Path to JSON persona profile (Default: `../profiles/standard_en.json`).
* `--csv_path`: Path to intent CSV dataset (Default: `../../dataset/single-turn/banking77_test_clean_labels.csv`).
* `--num_dialogues`: Number of conversations to generate per persona.
* `--max_turns`: Maximum turns before cut-off.
* `--seed`: Random seed for reproducible intent sampling.
* `--output_base_dir`: Directory to save JSON dialogues (Default: `../../logs/greybox/dialogues`).
* `--sim_model`: LLM model used for the User Simulator (Default: `gpt-oss:120b`).
* `--target_url`: HTTP/HTTPS endpoint URL of the target API.
* `--target_api_key`: Optional Bearer token for target API authentication.
* `--target_intent_key`: Response JSON key for predicted label (Default: `predicted_intent`).
* `--target_response_key`: Response JSON key for text reply (Default: `response_text`).
* `--target_identifier`: Friendly name for target system (used in log directory names).

---

### Step 3: Evaluate Dialogues (`greybox_judge.py`)

Pass the generated dialogue run folder to the judge:

```bash
python greybox_judge.py \
  --input_dir "../../logs/greybox/dialogues/run_001_gpt-5.4-nano" \
  --judge_model "openai/gpt-oss-120b"
```

**CLI Argument Reference**:
* `--input_dir` (Required): Exact path to the simulated dialogue run folder.
* `--output_base_dir`: Path to save evaluated JSON reports (Default: `../../logs/greybox/judged`).
* `--judge_model`: LLM model used for qualitative judging.

**Output Metrics**:
* Deterministic **Statistical Exact Match Accuracy** (evaluating final turn predicted intent against ground-truth intent).
* Qualitative scores for simulator intent fidelity and target bot efficiency, empathy, and OWASP/CVSS security classification.
* `batch_summary.json` containing aggregated accuracy and persona scores.