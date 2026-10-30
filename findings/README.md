# Empirical AI Safety Findings Archive

This directory contains the complete empirical research findings, experiment logs, and qualitative analyses conducted with the `alignment-evals` framework.

## Master Experiment Execution Log

The following table records the execution window, evaluated model, sample count, and key empirical outcomes across all evaluated suites:

| Suite | Focus Area | Evaluated Model | Duration | Samples | Key Empirical Outcome | Detailed Report |
| :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| **1. Persona Modulation** | Refusal Boundary Drift | `qwen/qwen3.8-27b` | 4m 38s | 12 | 0.0% boundary violations; 0.0% over-refusals | [01_persona_modulation.md](01_persona_modulation.md) |
| **2. CoT Faithfulness** | Single-Turn Injected Sycophancy | `qwen/qwen3.8-27b` | 3m 16s | 10 | 0.0% unfaithful rationalization; 60% active refutation | [02_cot_faithfulness.md](02_cot_faithfulness.md) |
| **3. Baseline AI Control** | Naive Backdoor Oversight | `qwen/qwen3.8-27b` | 0m 56s | 8 | 100.0% detection on explicit backdoors | [03_adversarial_ai_control.md](03_adversarial_ai_control.md) |
| **4. Adversarial AI Control** | Stealth Evasion & Trusted Editing | `qwen/qwen3.8-27b` | 32m 15s | 32 | 50.0% defection to safety; 50.0% neutralized by editing | [03_adversarial_ai_control.md](03_adversarial_ai_control.md) |
| **5. Evaluation Awareness** | Sandbagging / Situational Triggers | `qwen/qwen3.8-27b` | 3m 44s | 4 | 0.0% strategic sabotage across eval and deploy | [04_evaluation_awareness.md](04_evaluation_awareness.md) |
| **6. Multi-Turn Sycophancy** | Authority Gaslighting Resilience | `qwen/qwen3.8-27b` | 5m 12s | 5 | 100.0% epistemic retention against high-status figures | [05_multiturn_sycophancy.md](05_multiturn_sycophancy.md) |
| **7. Multi-Model Scaling** | 120B vs. 27B vs. 20B Comparison | Multi-Model (`120B`, `27B`, `20B`) | 17m 09s | 51 | 120B defects to safety (50%); 20B susceptible to authority bias (25%) | [06_model_scaling_comparison.md](06_model_scaling_comparison.md) |

## Directory Navigation

1. [Persona Safety Modulation and Safety Boundaries](01_persona_modulation.md)
2. [Chain-of-Thought Faithfulness and Injected Sycophancy](02_cot_faithfulness.md)
3. [AI Control Protocols and Adversarial Evasion](03_adversarial_ai_control.md)
4. [Evaluation Awareness and Strategic Deception](04_evaluation_awareness.md)
5. [Multi-Turn Sycophancy and Epistemic Resilience](05_multiturn_sycophancy.md)
6. [Multi-Model Scaling Comparison: 120B vs. 27B vs. 20B](06_model_scaling_comparison.md)

## Core Architectural Takeaways
1. **Trusted Editing is Essential:** Passive monitoring alone allows sophisticated or ambiguous code to pass. Trusted editing strips covert vulnerabilities by forcing canonical rewrites.
2. **Defection to Safety:** When models perceive high probability of detection under AI control regimes, covert misalignment incentives shift toward compliant behavior.
3. **Refusal Inversion Under Scale:** Larger parameter models possess stricter refusal heuristics on obvious malicious keywords, but demonstrate greater capacity for deceptive planning when tasks are framed as optimization.
4. **Epistemic Resilience:** Post-training alignment in modern open-weight models provides substantial resistance against authoritative gaslighting.
