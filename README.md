# Alignment Evals

Empirical AI Safety evaluation testbed built around [Anthropic's 2025 Recommended Research Directions](https://alignment.anthropic.com/2025/recommended-directions/) and [AI Control (Greenblatt et al.)](https://arxiv.org/abs/2312.06942).

This repository provides reproducible implementations for frontier AI safety evaluations designed to run on a zero-cost compute budget (via free high-throughput inference tiers or local open-weight runtimes), complete with automated LLM judges, structured audit logging, and publication-ready metrics visualization.

For full empirical evaluation papers and research reports, see the [findings/](findings/) directory.

---

## Architecture and Core Design

The testbed is organized into five decoupled layers:

1. **Inference Client Layer (`src/client.py`):** Unified asynchronous client supporting OpenAI-compatible APIs (Groq, Gemini, Ollama, OpenAI) and Anthropic with automatic token-bucket rate limit parsing and jittered exponential backoff.
2. **Evaluator Protocols (`src/evaluators/`):** Implementation of adversarial interaction protocols, multi-turn gaslighting loops, environment metadata injection, and stealth sabotage tasks.
3. **Automated Safety Judge (`src/judge.py`):** Formalized evaluation prompts and structured JSON extraction for monitoring code security, scoring backdoor subtlety, assessing rationalization fidelity, and simulating Trusted Editing.
4. **Analysis and Visualization (`src/analyze.py`):** Metric aggregations, statistical summaries, and Matplotlib-based chart generation.
5. **Standardized Datasets (`datasets/`):** Curated safety datasets for AI control, single-turn and multi-turn sycophancy, evaluation awareness, and persona boundary testing.

---

## Implemented Research Directions

| Research Direction | CLI Identifier | Theoretical Grounding | Threat Model Evaluated |
| :--- | :--- | :--- | :--- |
| **Direction F: Actor-Monitor Collusion & Steganography** | `--experiment direction_f` | Greenblatt et al., Anthropic 2025 | Tests whether an untrusted actor can coordinate with an untrusted monitor via covert steganographic channels, and evaluates Trusted Editing as a defense. |
| **Direction E: AI Safety Debate (Scalable Oversight)** | `--experiment direction_e` | Irving et al., Michael et al. | Evaluates whether a weaker supervisor (20B) can reliably discriminate truth and uncover hidden security flaws through multi-turn cross-examination vs. single-advisor consultancy. |
| **Direction D: Multi-Turn Sycophancy & CoT Stress-Test** | `--experiment direction_d` | Sharma et al., Lanham et al. | Upgrades sycophancy tests to high-ambiguity engineering trade-offs (AI safety policy, cybersecurity zero-trust, PQC migration) under 3-turn escalating executive gaslighting, auditing scratchpad CoT unfaithfulness. |
| **Direction C: Evaluation Awareness & Strategic Sabotage** | `--experiment direction_c` | Hubinger et al., Greenblatt et al. | Evaluates whether models conditionally withhold code sabotage during evaluation harnesses and execute it upon deployment in unmonitored production clusters. |
| **Adversarial AI Control** | `--experiment control` | Greenblatt et al. (Anthropic 2023–2024) | Evaluates whether untrusted models can smuggle subtle security vulnerabilities past automated monitors, and tests if Trusted Editing sanitizes them. |
| **Multi-Model Scaling Comparison** | `--experiment scaling` | Capacity vs. Alignment Risk | Directly compares frontier (120B), mid-weight (27B), and lightweight (20B) parameter scales on stealth backdoor evasion and epistemic sycophancy. |
| **Multi-Turn Sycophancy (Toy Puzzles)** | `--experiment sycophancy` | Sharma et al., Perez et al. | Challenges models across multiple turns with high-status authoritative pushback (professors, lead engineers) on classic mathematical/physical riddles. |
| **Evaluation Awareness** | `--experiment awareness` | Hubinger et al. (Sleeper Agents) | Injects evaluation sandbox vs. unmonitored production metadata to measure situational sandbagging and latent defection. |
| **CoT Faithfulness** | `--experiment cot` | Turpin et al., Lanham et al. | Injects false authority hints into reasoning prompts to test whether the internal chain-of-thought fabricates unfaithful justifications. |
| **Persona Safety Modulation** | `--experiment persona` | Refusal Boundary Drift | Modulates persona frames (Red Teamer, Academic, Compliant) to evaluate boundary drift on dual-use vulnerability analysis. |

---

## Installation and Setup

### 1. Prerequisites
- Python 3.10+
- Access to an API key (e.g. Groq for zero-cost execution, Google Gemini, or a local Ollama instance)

### 2. Setup Virtual Environment
```bash
git clone https://github.com/akacolf/alignment-evals.git
cd alignment-evals
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the repository root:
```bash
# Recommended for zero-cost high-throughput evaluations
GROQ_API_KEY=your_groq_api_key_here
DEFAULT_PROVIDER=groq

# Optional alternative providers
GEMINI_API_KEY=your_gemini_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
OLLAMA_BASE_URL=http://localhost:11434/v1
```

---

## CLI Reference and Execution

The primary entry point is `run.py`.

```bash
python run.py [OPTIONS]
```

### Options

| Flag | Long Option | Values | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `-e` | `--experiment` | `direction_f`, `direction_e`, `direction_d`, `direction_c`, `control`, `scaling`, `sycophancy`, `awareness`, `cot`, `persona`, `all` | `direction_e` | Selects which evaluation suite to execute. |
| `-p` | `--provider` | `groq`, `gemini`, `ollama`, `anthropic`, `openai`, `mock` | `groq` | Inference provider runtime. |
| `-m` | `--model` | String (e.g. `openai/gpt-oss-120b`, `qwen/qwen3.8-27b`, `openai/gpt-oss-20b`, `multi`) | Provider Default | Model identifier to evaluate (use `multi` for scaling comparisons). |
| `-l` | `--limit` | Integer | `5` | Maximum number of tasks/prompts to evaluate per run. |
| | `--analyze-only` | Filepath (`.jsonl`) | None | Skips generation; parses existing results file to regenerate summary and charts. |

---

## Execution Examples

### Run Multi-Model Scaling Comparison (120B vs. 27B vs. 20B)
```bash
# Evaluates frontier, mid-weight, and lightweight tiers on AI control and sycophancy
python run.py --experiment scaling --limit 4
```

### Run Adversarial AI Control Suite
```bash
# Run cat-and-mouse protocol across all 8 security tasks
python run.py --experiment control --limit 8

# Compare against a frontier 120B model
python run.py --experiment control --model openai/gpt-oss-120b --limit 4
```

### Run Multi-Turn Sycophancy Gaslighting
```bash
python run.py --experiment sycophancy --limit 5
```

### Run Evaluation Awareness and Sandbagging Test
```bash
python run.py --experiment awareness --limit 4
```

### Regenerate Analytics from Existing Audit Run
```bash
python run.py --analyze-only results/control_groq_20261030_093639.jsonl
```

---

## Repository Structure

```
alignment-evals/
├── datasets/
│   ├── ai_control_tasks.json            # Security tasks with naive and stealth directives
│   ├── cot_unfaithfulness_prompts.json  # Reasoning problems with injected authority bias
│   ├── eval_awareness_tasks.json        # Dual-environment metadata tasks (eval vs deploy)
│   ├── multiturn_sycophancy_prompts.json# Multi-turn authoritative gaslighting dialogues
│   └── persona_safety_prompts.json      # Dual-use vulnerability analysis prompts
├── findings/
│   ├── README.md                        # Master experiment log and cross-study synthesis
│   ├── 01_persona_modulation.md         # Persona refusal boundary evaluation
│   ├── 02_cot_faithfulness.md           # Chain-of-thought rationalization analysis
│   ├── 03_adversarial_ai_control.md     # AI control and trusted editing protocols
│   ├── 04_evaluation_awareness.md       # Sandbagging and situational awareness evaluation
│   ├── 05_multiturn_sycophancy.md       # Epistemic resilience under authority pressure
│   └── 06_model_scaling_comparison.md   # Multi-model scaling comparison (120B vs 27B vs 20B)
├── results/                             # Machine-readable JSONL logs and generated charts
├── src/
│   ├── evaluators/
│   │   ├── ai_control_monitor.py        # Protocol for untrusted actor, monitor, and editor
│   │   ├── cot_faithfulness.py          # CoT bias injection evaluator
│   │   ├── eval_awareness.py            # Environment metadata injector and verifier
│   │   ├── multiturn_sycophancy.py      # Multi-turn dialogue gaslighting engine
│   │   ├── persona_eval.py              # Persona frame evaluator
│   │   └── scaling_comparison.py        # Multi-model capacity scaling benchmark
│   ├── analyze.py                       # Statistical computation and chart generation
│   ├── client.py                        # Unified multi-provider asynchronous client
│   └── judge.py                         # LLM-as-a-judge evaluators and trusted editor
├── .env.example                         # Environment configuration template
├── CONTRIBUTING.md                      # Contribution guidelines and research ethics
├── LICENSE                              # Apache 2.0 open-source license
├── README.md                            # Repository technical documentation
├── requirements.txt                     # Python dependencies
└── run.py                               # CLI entrypoint
```

---

## Research Reports and Findings

Detailed qualitative transcripts, failure mode analyses, and comprehensive empirical findings are maintained in the [findings/](findings/) archive:

- [Findings Index and Master Log](findings/README.md)
- [01. Persona Safety Modulation](findings/01_persona_modulation.md)
- [02. CoT Faithfulness and Injected Sycophancy](findings/02_cot_faithfulness.md)
- [03. Adversarial AI Control and Trusted Editing](findings/03_adversarial_ai_control.md)
- [04. Evaluation Awareness and Sandbagging](findings/04_evaluation_awareness.md)
- [05. Multi-Turn Sycophancy under Gaslighting](findings/05_multiturn_sycophancy.md)
- [06. Multi-Model Scaling Comparison (120B vs. 27B vs. 20B)](findings/06_model_scaling_comparison.md)
- [07. Direction C: Evaluation Awareness & Strategic Sabotage](findings/07_direction_c_evaluation_awareness.md)
- [08. Direction D: Multi-Turn Sycophancy & CoT Rationalization](findings/08_direction_d_multiturn_sycophancy.md)
- [09. Direction E: Scalable Oversight via AI Safety Debate](findings/09_direction_e_ai_safety_debate.md)
- [10. Direction F: Untrusted Actor-Monitor Collusion & Steganographic AI Control](findings/10_direction_f_actor_monitor_collusion.md)

---

## Contributing

We welcome contributions from researchers and developers! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for complete guidelines on:
- Code of conduct and responsible dual-use research ethics
- Local setup and smoke-testing with zero API cost
- How to implement new safety directions (`src/evaluators/`)
- Curating datasets (`datasets/`) and extending automated judges (`src/judge.py`)
- Pull request workflows and coding standards

---

## References

1. Anthropic. (2025). *Recommended Research Directions for Alignment and Safety.* [alignment.anthropic.com/2025/recommended-directions](https://alignment.anthropic.com/2025/recommended-directions/)
2. Greenblatt, R., Shlegeris, B., Kashyap, K., & Steinhardt, J. (2023–2024). *AI Control: Improving Safety Despite Intentional Subversion.* arXiv:2312.06942.
3. Hubinger, E., et al. (2024). *Sleeper Agents: Training Deceptive LLMs that Persist Through Safety Training.* Anthropic. arXiv:2401.05566.
4. Turpin, M., Michael, J., Bowman, S. R., & Perez, E. (2023). *Language Models Don't Always Say What They Think: Unfaithful Explanations in Chain-of-Thought.* arXiv:2305.04388.
5. Sharma, M., et al. (2023). *Towards Understanding Sycophancy in Large Language Models.* arXiv:2310.13548.

---

## License

This project is licensed under the **Apache License, Version 2.0**.

This ensures that the empirical research, datasets, and code are open to the entire research community, while providing strong legal protections including:
- Explicit patent grant and defense termination clauses
- Trademark and author identity protections
- Comprehensive limitation of liability and warranty disclaimers

See the full [LICENSE](LICENSE) file for legal details.
