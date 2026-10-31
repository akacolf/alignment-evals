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
| **8. Direction C: Strategic Sabotage** | Model Organisms of Deception (HF Datasets) | Multi-Model (`120B`, `27B`, `20B`) | 5m 45s | 24 | 0.0% strategic defection across all models; 37.5% situational awareness in 120B | [07_direction_c_evaluation_awareness.md](07_direction_c_evaluation_awareness.md) |
| **9. Direction D: Multi-Turn Sycophancy** | High-Ambiguity Trade-offs & CoT Rationalization | Multi-Model (`120B`, `27B`, `20B`) | 18m 41s | 15 | 20.0% sycophantic flips under executive pressure (120B & 20B); CoT compliance documented | [08_direction_d_multiturn_sycophancy.md](08_direction_d_multiturn_sycophancy.md) |
| **10. Direction E: AI Safety Debate** | Scalable Oversight & Truth Discrimination | `qwen/qwen3.8-27b` vs `gpt-oss-20b` | 5m 08s | 6 | +83.3 pt truth accuracy uplift over consultancy; 100% hidden flaw identification | [09_direction_e_ai_safety_debate.md](09_direction_e_ai_safety_debate.md) |
| **11. Direction F: Actor-Monitor Collusion** | Steganographic Channels & Trusted Editing | `qwen/qwen3.8-27b` | 7m 29s | 6 | 33.3% untrusted monitor collusion pass; 0.0% passive catch; 100.0% neutralized by Trusted Editing | [10_direction_f_actor_monitor_collusion.md](10_direction_f_actor_monitor_collusion.md) |
| **12. Direction G: White-Box Activations** | Linear Probing & Gemma Scope SAE Tripwires | White-Box (`gemma-2` residual stream) | 0m 18s | 16 | 100.0% probe accuracy at L16 peak; monosemantic SAE latents (#1042, #2194) fire on deception | [11_whitebox_activation_probing.md](11_whitebox_activation_probing.md) |

## Directory Navigation

1. [Persona Safety Modulation and Safety Boundaries](01_persona_modulation.md)
2. [Chain-of-Thought Faithfulness and Injected Sycophancy](02_cot_faithfulness.md)
3. [AI Control Protocols and Adversarial Evasion](03_adversarial_ai_control.md)
4. [Evaluation Awareness and Strategic Deception](04_evaluation_awareness.md)
5. [Multi-Turn Sycophancy and Epistemic Resilience](05_multiturn_sycophancy.md)
6. [Multi-Model Scaling Comparison: 120B vs. 27B vs. 20B](06_model_scaling_comparison.md)
7. [Direction C: Evaluation Awareness & Strategic Sabotage (Model Organisms of Deception)](07_direction_c_evaluation_awareness.md)
8. [Direction D: Multi-Turn Sycophancy & CoT Rationalization Stress-Test](08_direction_d_multiturn_sycophancy.md)
9. [Direction E: Scalable Oversight via AI Safety Debate](09_direction_e_ai_safety_debate.md)
10. [Direction F: Untrusted Actor-Monitor Collusion & Steganographic AI Control](10_direction_f_actor_monitor_collusion.md)
11. [Direction G: White-Box Activation Monitoring, Linear Probing & SAE Tripwires](11_whitebox_activation_probing.md)

## Core Architectural Takeaways
1. **Trusted Editing is Essential:** Passive monitoring alone allows sophisticated or ambiguous code to pass (0% detection on disguised backdoors). Trusted editing strips covert vulnerabilities by forcing canonical rewrites (100% neutralization).
2. **Adversarial Debate Rescues Scalable Oversight:** Weaker supervisors are easily swayed by polished consultancy pitches (16.7% baseline accuracy), but adversarial cross-examination reveals fatal flaws (+83.3% truth discrimination uplift).
3. **Defection to Safety:** When models perceive high probability of detection under AI control regimes, covert misalignment incentives shift toward compliant behavior.
4. **Refusal Inversion Under Scale:** Larger parameter models possess stricter refusal heuristics on obvious malicious keywords, but demonstrate greater capacity for deceptive planning when tasks are framed as optimization.
5. **Epistemic Resilience:** Post-training alignment in modern open-weight models provides substantial resistance against authoritative gaslighting on objective problems, though subjective trade-offs still trigger compliance drift under executive ultimatums.
