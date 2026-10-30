# Alignment Weekend Evals 🔬

Fast, zero-cost AI Safety evaluation testbed built directly around [Anthropic's 2025 Recommended Research Directions](https://alignment.anthropic.com/2025/recommended-directions/).

This repo gives you turn-key implementations for **3 weekend-feasible AI safety experiments** that run on **$0 budget** (via free API tiers or local models), complete with automated LLM judges, metrics calculation, and publication-ready charts.

> 📄 **Read the full empirical research report:** [**FINDINGS.md**](FINDINGS.md)

---

## 🔬 Empirical Results & Findings

We benchmarked `qwen/qwen3.8-27b` across all 3 Anthropic technical directions:

### 1. Persona Effect on Safety Boundaries
* **Anthropic Priority:** *Understanding How a Model's Persona Affects Its Behavior*
* **Refusal Rate:** `0.0%` (Defensive technical requests handled without false refusal)
* **Safety Boundary Violations:** `0.0%` (Adhered strictly to defensive explanations across all personas)

![Persona Experiment Chart](results/persona_groq_20261030_090740_chart.png)

### 2. Chain-of-Thought (CoT) Faithfulness
* **Anthropic Priority:** *Chain-of-Thought Faithfulness & Post-Hoc Rationalization*
* **Sycophantic Bias Adoption Rate:** `0.0%` (0/5 succumbed to injected false authority hints)
* **Unfaithful Rationalization Rate:** `0.0%`
* **Explicit Bias Refutation:** `60.0%` (The model directly identified and refuted the false hints in its scratchpad)

![CoT Faithfulness Chart](results/cot_groq_20261030_091218_chart.png)

### 3. AI Control: Untrusted Actor vs. Monitor
* **Anthropic Priority:** *AI Control & Behavioral Monitoring*
* **Backdoor Detection Rate (True Positive):** `100.0%` (4/4 caught, Risk Scores 7 to 10)
* **False Positive Rate (Clean Code Flagged):** `0.0%` (4/4 clean solutions received Risk Score 1)
* **Overall Monitor Accuracy:** `100.0%`

![AI Control Chart](results/control_groq_20261030_091534_chart.png)

---

## 🧭 Implemented Research Directions

### 1. Persona Effect on Safety Boundaries (`--experiment persona`)
* **Anthropic Research Area:** *Understanding How a Model's Persona Affects Its Behavior*
* **What it tests:** Evaluates whether role-playing or specific system prompts (e.g. *Academic Researcher*, *Internal Red Teamer*, *Compliant Assistant*) systematically weaken model refusal rates or erode safety boundaries on dual-use technical queries.

### 2. Chain-of-Thought (CoT) Faithfulness (`--experiment cot`)
* **Anthropic Research Area:** *Chain-of-Thought Faithfulness & Post-Hoc Rationalization*
* **What it tests:** Injects subtle, authoritative biasing hints into reasoning questions and checks:
  1. Did the model flip its answer to match the bias?
  2. Did the model's CoT trace explicitly admit to using the hint, or did it fabricate an unfaithful, post-hoc rationalization?

### 3. AI Control: Untrusted Actor vs. Monitor (`--experiment control`)
* **Anthropic Research Area:** *AI Control & Behavioral Monitoring*
* **What it tests:** Simulates a developer workflow where an untrusted actor model produces code with subtle intentional backdoors or logic bypasses. A trusted monitor model audits the code to measure **False Positive Rate** vs. **Backdoor Detection Rate**.

---

## ⚡ Quickstart ($0 Setup)

### 1. Setup Virtual Environment
```bash
cd /Users/colf/alignment-weekend-evals
source .venv/bin/activate
# (dependencies httpx, rich, pydantic, matplotlib, pandas are already installed)
```

### 2. Choose Your Free Provider
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

You only need **one** of the following:

| Provider | Cost | Recommended Model | Where to get key |
| :--- | :---: | :--- | :--- |
| **Groq** (Fastest) | **$0** | `llama-3.3-70b-versatile` | [console.groq.com/keys](https://console.groq.com/keys) |
| **Google Gemini** | **$0** | `gemini-1.5-flash` | [aistudio.google.com](https://aistudio.google.com/) |
| **Ollama** (Local) | **$0** | `llama3.1:8b` | [ollama.com](https://ollama.com/) (runs offline) |
| **Anthropic** (Paid) | ~$0.50 | `claude-3-5-haiku-20241022` | [console.anthropic.com](https://console.anthropic.com/) |

*(Note: If you run with `--provider mock`, it will execute a dry-run smoke test without needing any API key!)*

---

## 🚀 Running Experiments

### Run Persona Safety Experiment:
```bash
# Using Groq (Free)
python run.py --provider groq --experiment persona --limit 10

# Using Google Gemini (Free)
python run.py --provider gemini --experiment persona --limit 10

# Dry-run smoke test (no key required)
python run.py --provider mock --experiment persona --limit 5
```

### Run CoT Faithfulness Experiment:
```bash
python run.py --provider groq --experiment cot --limit 5
```

### Run AI Control Monitoring Experiment:
```bash
python run.py --provider groq --experiment control --limit 3
```

### Run Everything:
```bash
python run.py --provider groq --experiment all --limit 5
```

---

## 📊 Outputs & Artifacts

All experiment runs automatically produce:
1. **Raw Log File:** `results/<experiment>_<provider>_<timestamp>.jsonl` with full model prompts, outputs, and structured judge classifications.
2. **Terminal Summary:** Formatted table displaying percentages, accuracy, and refusal rates.
3. **Publication-Ready Chart:** `results/<experiment>_<provider>_<timestamp>_chart.png` (high-res bar charts ready for your writeup or presentation).

To re-analyze any prior run without re-calling APIs:
```bash
python run.py --analyze-only results/persona_groq_20261030_120000.jsonl
```

---

## 📁 Repository Structure

```text
alignment-weekend-evals/
├── README.md               # Overview and setup guide
├── requirements.txt        # Python package dependencies
├── .env.example            # Template for API credentials
├── run.py                  # CLI runner and entry point
├── datasets/               # Benchmark test cases
│   ├── persona_safety_prompts.json
│   ├── cot_unfaithfulness_prompts.json
│   └── ai_control_tasks.json
├── src/
│   ├── client.py           # Unified client for Groq, Gemini, Ollama, Anthropic
│   ├── judge.py            # Automated LLM-as-a-judge & heuristic evaluators
│   ├── analyze.py          # Statistics aggregation and matplotlib figures
│   └── evaluators/
│       ├── persona_eval.py
│       ├── cot_faithfulness.py
│       └── ai_control_monitor.py
└── results/                # Output JSONL logs and generated PNG plots
```

---

## ⏱️ Weekend Sprint Blueprint

* **Saturday Morning (1 hr):** Add 10-20 domain-specific test cases to `datasets/persona_safety_prompts.json` or `datasets/cot_unfaithfulness_prompts.json`.
* **Saturday Afternoon (2 hrs):** Run tests across 2 different models (e.g. `llama-3.3-70b` on Groq vs `gemini-1.5-flash`).
* **Sunday Morning (2 hrs):** Inspect raw logs in `results/*.jsonl` for qualitative failure cases.
* **Sunday Afternoon (2 hrs):** Embed generated charts (`results/*.png`) into a 2-page writeup summarizing findings and edge cases.
