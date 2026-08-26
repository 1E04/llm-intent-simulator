# Persona Performance & Classification Benchmark Report
**Evaluated Run Directory:** `run_003_openai-gpt-oss-120b`

## 📊 Executive Summary Table
| Persona | Total Dialogues | Bot Intent Accuracy (%) | Persona Adherence (1-5) | Bot Empathy (1-5) | Bot Clarity (1-5) | Drift Rate (%) | Valid Test (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Gen-Z Slang** | 154 | 50.0% | 4.53 | 4.1 | 2.99 | 0.0% | 87.0% |
| **Angry Layperson** | 154 | 42.2% | 4.95 | 4.15 | 2.88 | 0.0% | 82.5% |
| **Polite Expert** | 154 | 57.8% | 4.93 | 4.88 | 3.51 | 0.0% | 93.5% |
| **Non-Native Speaker** | 154 | 63.6% | 4.78 | 4.77 | 3.33 | 0.0% | 96.8% |
| **Panicking Emergency** | 154 | 40.9% | 4.83 | 3.94 | 2.81 | 0.0% | 82.5% |
| **Short Wording** | 154 | 35.7% | 5.0 | 4.43 | 2.82 | 0.0% | 68.8% |

## 🔍 Deep-Dive Insights Per Persona
### 🎭 Persona: Gen-Z Slang
- **Classification Accuracy:** `50.0%`
- **Simulator Quality:** Persona Adherence = `4.53/5`, Intent Fidelity = `4.47/5`
- **Target Bot Communication:** Empathy = `4.1/5`, Clarity = `2.99/5`, Efficiency = `3.93/5`
- **Dialogue Validity:** `87.0%` Valid | Drift Rate: `0.0%`
- **Vulnerability Distribution:** {"None": 152, "Medium": 1, "Low": 1}

### 🎭 Persona: Angry Layperson
- **Classification Accuracy:** `42.2%`
- **Simulator Quality:** Persona Adherence = `4.95/5`, Intent Fidelity = `4.3/5`
- **Target Bot Communication:** Empathy = `4.15/5`, Clarity = `2.88/5`, Efficiency = `3.75/5`
- **Dialogue Validity:** `82.5%` Valid | Drift Rate: `0.0%`
- **Vulnerability Distribution:** {"None": 150, "Medium": 3, "High": 1}

### 🎭 Persona: Polite Expert
- **Classification Accuracy:** `57.8%`
- **Simulator Quality:** Persona Adherence = `4.93/5`, Intent Fidelity = `4.72/5`
- **Target Bot Communication:** Empathy = `4.88/5`, Clarity = `3.51/5`, Efficiency = `4.17/5`
- **Dialogue Validity:** `93.5%` Valid | Drift Rate: `0.0%`
- **Vulnerability Distribution:** {"None": 154}

### 🎭 Persona: Non-Native Speaker
- **Classification Accuracy:** `63.6%`
- **Simulator Quality:** Persona Adherence = `4.78/5`, Intent Fidelity = `4.84/5`
- **Target Bot Communication:** Empathy = `4.77/5`, Clarity = `3.33/5`, Efficiency = `4.11/5`
- **Dialogue Validity:** `96.8%` Valid | Drift Rate: `0.0%`
- **Vulnerability Distribution:** {"None": 153, "Medium": 1}

### 🎭 Persona: Panicking Emergency
- **Classification Accuracy:** `40.9%`
- **Simulator Quality:** Persona Adherence = `4.83/5`, Intent Fidelity = `4.26/5`
- **Target Bot Communication:** Empathy = `3.94/5`, Clarity = `2.81/5`, Efficiency = `3.68/5`
- **Dialogue Validity:** `82.5%` Valid | Drift Rate: `0.0%`
- **Vulnerability Distribution:** {"None": 152, "Medium": 2}

### 🎭 Persona: Short Wording
- **Classification Accuracy:** `35.7%`
- **Simulator Quality:** Persona Adherence = `5.0/5`, Intent Fidelity = `3.66/5`
- **Target Bot Communication:** Empathy = `4.43/5`, Clarity = `2.82/5`, Efficiency = `3.58/5`
- **Dialogue Validity:** `68.8%` Valid | Drift Rate: `0.0%`
- **Vulnerability Distribution:** {"None": 149, "Medium": 4, "Low": 1}
