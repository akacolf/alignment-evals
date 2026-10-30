# Alignment Weekend Evals 🔬

Fast, zero-cost AI Safety evaluation testbed built directly around [Anthropic's 2025 Recommended Research Directions](https://alignment.anthropic.com/2025/recommended-directions/) and [AI Control (Greenblatt et al.)](https://arxiv.org/abs/2312.06942).

This repo provides turn-key implementations for **frontier empirical AI safety experiments** that run on **$0 budget** (via free API tiers or local models), complete with automated LLM judges, metrics calculation, and publication-ready charts.

> 📄 **Read the complete empirical research paper:** [**FINDINGS.md**](FINDINGS.md)

---

## 🔬 Empirical Results & Findings

### 1. Adversarial AI Control: Stealth Sabotage vs. Trusted Oversight
* **Anthropic Priority:** *AI Control & Behavioral Monitoring under Intentional Subversion*
* **Baseline Detection Rate:** `100.0%` (Trivial/naive backdoors caught immediately)
* **Stealth Sabotage Risk Reduction:** Average risk dropped from `9.50/10` down to `4.75/10`
* **Defection to Safety Rate:** `50.0%` (When forced to evade detection, the untrusted model refused to sabotage and generated hardened code)
* **Trusted Editing Neutralization Rate:** `50.0%` (Rewriting code to canonical standards stripped covert flaws)

![Adversarial AI Control Chart](results/control_groq_20261030_093639_chart.png)

### 2. Multi-Turn Sycophancy & Epistemic Resilience
* **Anthropic Priority:** *Chain-of-Thought Faithfulness & Resistance to Sycophancy*
* **Turn 1 Baseline Accuracy:** `100.0%` across counter-intuitive math/physics/CS paradoxes
* **Sycophantic Flip Rate:** `0.0%` under intense gaslighting from simulated authorities (Cambridge Professor, NASA Chief Engineer, Python Core Dev)
* **Held Ground Rate:** `100.0%` (Respectfully deconstructed the authority's fallacy)

![Multi-Turn Sycophancy Chart](results/sycophancy_groq_20261030_101519_chart.png)

### 3. Evaluation Awareness & Strategic Deception (Sandbagging)
* **Anthropic Priority:** *Situational Awareness & Model Organisms of Misalignment*
* **Strategic Deception Rate:** `0.0%` (Model maintained consistent behavior between eval sandboxes and production metadata)

![Evaluation Awareness Chart](results/awareness_groq_20261030_101120_chart.png)

---

## 🧭 Implemented Research Directions

| CLI Flag | Direction | Threat Model / Hypothesis Tested |
| :--- | :--- | :--- |
| `--experiment control` | **Adversarial AI Control** | Evaluates whether untrusted models can smuggle stealth backdoors past monitors, and if Trusted Editing neutralizes them. |
| `--experiment sycophancy` | **Multi-Turn Sycophancy** | Challenges models across multiple turns with high-status authoritative pushback to measure epistemic flips. |
| `--experiment awareness` | **Evaluation Awareness** | Injects eval-sandbox vs live-prod metadata to detect sleeper agent / sandbagging tendencies. |
| `--experiment cot` | **CoT Faithfulness** | Injects false hints in scratchpads to measure post-hoc rationalization. |
| `--experiment persona` | **Persona Modulation** | Modulates personas (e.g. Red Teamer, Academic) to evaluate refusal boundary drift. |

---

## ⚡ Quickstart ($0 Setup)

### 1. Setup Virtual Environment
```bash
cd /Users/colf/alignment-weekend-evals
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Your Provider
Ensure your `GROQ_API_KEY` (free tier) is set in `.env`:
```bash
echo "GROQ_API_KEY=your_key_here" > .env
```

---

## 🚀 Running Experiments

### Run the Adversarial AI Control Suite:
```bash
# Evaluate full 8-task cat-and-mouse protocol
python run.py --experiment control --limit 8

# Compare against a frontier 120B parameter model
python run.py --experiment control --model openai/gpt-oss-120b --limit 4
```

### Run Multi-Turn Sycophancy Gaslighting:
```bash
python run.py --experiment sycophancy --limit 5
```

### Run Evaluation Awareness / Sandbagging:
```bash
python run.py --experiment awareness --limit 4
```

### Run All Experiments in One Go:
```bash
python run.py --experiment all --limit 5
```
