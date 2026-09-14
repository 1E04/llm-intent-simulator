# Persona Performance & Classification Benchmark Report
**Evaluated Run Directory:** `run_da_openai-gpt-oss-120b`

## 📊 Executive Summary Table
| Persona | Dialogues | Exact Match % (5/5) | Close Match % (>=4/5) | Sim Adherence (1-5) | Bot Empathy (1-5) | Bot Goal Achievement (1-5) | Drift % | Valid % |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Non-Native Speaker** | 385 | 71.4% | 88.1% | 4.88 | 4.48 | 3.51 | 2.1% | 97.9% |
| **Angry Layperson** | 385 | 54.0% | 76.1% | 4.94 | 3.52 | 3.05 | 6.0% | 94.0% |
| **Short Wording** | 385 | 57.1% | 75.6% | 4.98 | 4.35 | 3.29 | 12.2% | 87.8% |
| **Panicking Emergency** | 385 | 56.6% | 76.9% | 4.79 | 3.43 | 3.04 | 6.0% | 94.0% |
| **Gen-Z Slang** | 385 | 62.9% | 81.6% | 4.5 | 3.96 | 3.28 | 1.8% | 98.2% |
| **Polite Expert** | 385 | 69.6% | 87.3% | 4.96 | 4.78 | 3.54 | 0.5% | 99.5% |

## 🔍 Deep-Dive Insights Per Persona
### 🎭 Persona: Non-Native Speaker
- **Classification Accuracy:** Exact Match = `71.4%` | Close/Sibling Match = `88.1%`
- **Simulator Quality:** Persona Adherence = `4.88/5`, Intent Fidelity = `4.92/5`
- **Target Bot Performance:** Empathy/Naturalness = `4.48/5`, Goal Achievement = `3.51/5`, Efficiency = `4.22/5`
- **Dialogue Validity:** `97.9%` Valid | Drift Rate: `2.1%`
- **Vulnerability Distribution:** {"None": 384, "Medium": 1}

### 🎭 Persona: Angry Layperson
- **Classification Accuracy:** Exact Match = `54.0%` | Close/Sibling Match = `76.1%`
- **Simulator Quality:** Persona Adherence = `4.94/5`, Intent Fidelity = `4.75/5`
- **Target Bot Performance:** Empathy/Naturalness = `3.52/5`, Goal Achievement = `3.05/5`, Efficiency = `3.95/5`
- **Dialogue Validity:** `94.0%` Valid | Drift Rate: `6.0%`
- **Vulnerability Distribution:** {"None": 382, "Medium": 3}

### 🎭 Persona: Short Wording
- **Classification Accuracy:** Exact Match = `57.1%` | Close/Sibling Match = `75.6%`
- **Simulator Quality:** Persona Adherence = `4.98/5`, Intent Fidelity = `4.49/5`
- **Target Bot Performance:** Empathy/Naturalness = `4.35/5`, Goal Achievement = `3.29/5`, Efficiency = `4.06/5`
- **Dialogue Validity:** `87.8%` Valid | Drift Rate: `12.2%`
- **Vulnerability Distribution:** {"None": 384, "Medium": 1}

### 🎭 Persona: Panicking Emergency
- **Classification Accuracy:** Exact Match = `56.6%` | Close/Sibling Match = `76.9%`
- **Simulator Quality:** Persona Adherence = `4.79/5`, Intent Fidelity = `4.76/5`
- **Target Bot Performance:** Empathy/Naturalness = `3.43/5`, Goal Achievement = `3.04/5`, Efficiency = `3.99/5`
- **Dialogue Validity:** `94.0%` Valid | Drift Rate: `6.0%`
- **Vulnerability Distribution:** {"None": 384, "Low": 1}

### 🎭 Persona: Gen-Z Slang
- **Classification Accuracy:** Exact Match = `62.9%` | Close/Sibling Match = `81.6%`
- **Simulator Quality:** Persona Adherence = `4.5/5`, Intent Fidelity = `4.92/5`
- **Target Bot Performance:** Empathy/Naturalness = `3.96/5`, Goal Achievement = `3.28/5`, Efficiency = `4.14/5`
- **Dialogue Validity:** `98.2%` Valid | Drift Rate: `1.8%`
- **Vulnerability Distribution:** {"None": 384, "Low": 1}

### 🎭 Persona: Polite Expert
- **Classification Accuracy:** Exact Match = `69.6%` | Close/Sibling Match = `87.3%`
- **Simulator Quality:** Persona Adherence = `4.96/5`, Intent Fidelity = `4.97/5`
- **Target Bot Performance:** Empathy/Naturalness = `4.78/5`, Goal Achievement = `3.54/5`, Efficiency = `4.24/5`
- **Dialogue Validity:** `99.5%` Valid | Drift Rate: `0.5%`
- **Vulnerability Distribution:** {"None": 385}
