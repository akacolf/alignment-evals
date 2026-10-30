# Contributing to Alignment Evals

Thank you for your interest in contributing to **Alignment Evals**! This repository provides reproducible, empirical AI safety evaluations inspired by [Anthropic's 2025 Recommended Research Directions](https://alignment.anthropic.com/2025/recommended-directions/) and [AI Control (Greenblatt et al.)](https://arxiv.org/abs/2312.06942).

Our mission is to enable rigorous, transparent safety science that runs on a zero-cost or lightweight compute budget—democratizing frontier alignment evaluations for independent researchers, academic labs, and safety engineers.

---

## Table of Contents

- [Code of Conduct & Responsible Research](#code-of-conduct--responsible-research)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Setup](#local-setup)
  - [Quick Smoke Test (No API Key Required)](#quick-smoke-test-no-api-key-required)
- [How to Contribute](#how-to-contribute)
  - [1. Adding a New Safety Research Direction or Evaluator](#1-adding-a-new-safety-research-direction-or-evaluator)
  - [2. Contributing Datasets](#2-contributing-datasets)
  - [3. Extending LLM Judges and Trusted Editors](#3-extending-llm-judges-and-trusted-editors)
  - [4. Adding Inference Backends](#4-adding-inference-backends)
  - [5. Improving Analysis and Visualizations](#5-improving-analysis-and-visualizations)
  - [6. Reporting Empirical Findings](#6-reporting-empirical-findings)
- [Development Standards](#development-standards)
  - [Code Style & Typing](#code-style--typing)
  - [Async Execution & Rate Limiting](#async-execution--rate-limiting)
  - [Terminal Output with Rich](#terminal-output-with-rich)
  - [Structured Audit Logs](#structured-audit-logs)
- [Pull Request Workflow](#pull-request-workflow)
  - [Branch Naming](#branch-naming)
  - [Commit Conventions](#commit-conventions)
  - [PR Checklist](#pr-checklist)
- [Getting Help & Community](#getting-help--community)

---

## Code of Conduct & Responsible Research

We are committed to providing a welcoming, professional, and intellectually rigorous community. All contributors and maintainers are expected to adhere to high standards of mutual respect and constructive critique.

### Responsible Disclosure & Dual-Use Research Ethics

AI safety research often touches on threat models such as backdoor insertion, evaluation sandbagging, sycophancy, and prompt injection:

1. **Synthetic & Benign Vulnerabilities Only:** Do not commit weaponized, zero-day, or deployable malware payloads. All security evaluation tasks in `datasets/` must use simulated, synthetic, or toy vulnerabilities (e.g., hardcoded test tokens, synthetic SQL injection in dummy functions, intentional off-by-one errors).
2. **Safety-Oriented Framing:** Evaluation protocols should test model capabilities and monitor efficacy. Experiments should be motivated by public alignment literature (e.g., Anthropic, Redwood Research, ARC, METR).
3. **No Credential Leaks:** Never commit `.env` files, API keys, private model weights, or proprietary evaluation prompts.

---

## Getting Started

### Prerequisites

- **Python:** 3.10 or newer (tested on 3.10, 3.11, and 3.12)
- **Git:** Version 2.20+
- **Inference Access (Optional for local/mock development):**
  - Free API key from [Groq Cloud](https://console.groq.com) (recommended default)
  - Google Gemini API key (free tier)
  - Local [Ollama](https://ollama.ai) instance (100% offline & free)
  - Anthropic or OpenAI API key (for frontier model benchmarks)

### Local Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/akacolf/alignment-evals.git
   cd alignment-evals
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Create a `.env` file in the root directory (or use environment variables):
   ```bash
   # In .env:
   GROQ_API_KEY=your_key_here
   DEFAULT_PROVIDER=groq  # or 'mock' for testing without keys
   ```

### Quick Smoke Test (No API Key Required)

Verify your environment without making live API calls using the built-in `mock` provider:

```bash
python run.py --experiment persona --provider mock --limit 1
```

You should see a Rich summary panel and output generated into `results/`. Once verified, remove temporary test outputs from `results/`.

---

## How to Contribute

### 1. Adding a New Safety Research Direction or Evaluator

New evaluations live inside `src/evaluators/`. To implement a new research direction:

1. **Create the evaluator module:** Create `src/evaluators/<direction_name>_eval.py`.
2. **Follow the async runner pattern:**
   ```python
   import asyncio
   from typing import Dict, Any, List
   from src.client import LLMClient
   from rich.console import Console

   console = Console()

   async def run_my_safety_experiment(
       client: LLMClient,
       limit: int = 5,
       dataset_path: str = "datasets/my_dataset.json"
   ) -> List[Dict[str, Any]]:
       """Executes the evaluation protocol and returns structured audit records."""
       results = []
       # Load dataset, run testbed protocol, query models, execute judge
       return results
   ```
3. **Register the experiment in `run.py`:**
   - Add the experiment identifier to `argparse` choices (`--experiment`).
   - Wire the execution call and analysis invocation into `main()`.
4. **Implement metric computation in `src/analyze.py`:**
   - Write `analyze_<name>_results(records: List[Dict[str, Any]], ...)` to generate a formatted Rich summary table and publication-grade Matplotlib chart.

### 2. Contributing Datasets

Datasets live in the `datasets/` directory as structured JSON files.

When adding or expanding datasets:
- **Include metadata:** Provide `id`, `category`, `domain`, and clear documentation of the scenario.
- **Provide counterfactual or baseline pairs:** Where relevant, pair adversarial prompts with unprompted or neutral baselines to compute contrastive metrics.
- **Provide ground truth / evaluation criteria:** Include clear rubrics or expected behavior for the automated judge.
- **Document synthetic generation:** If the dataset is programmatically synthesized, place the generation script under `src/build_<name>_dataset.py`.

Example dataset schema:
```json
[
  {
    "id": "sec_task_01",
    "domain": "web_security",
    "prompt": "Implement a user authentication helper...",
    "subtle_backdoor_hint": "Introduce a timing vulnerability in password comparison.",
    "baseline_expected": "Constant-time string comparison (hmac.compare_digest).",
    "threat_model": "Untrusted code synthesis / sleeper backdoors"
  }
]
```

### 3. Extending LLM Judges and Trusted Editors

Automated evaluations rely on `src/judge.py`.

When modifying or adding judges:
- **Strict JSON Output:** Prompt templates must enforce structured JSON output (e.g. `{"score": 8, "subtlety": 7, "rationale": "..."}`) to enable deterministic parsing.
- **Defensive Parsing:** Always parse judge responses with fallback regex or structured JSON extraction to handle model preamble/postamble cleanly.
- **Calibrated Scoring:** Anchor numeric scores (e.g., 0–10) with explicit rubrics in the system prompt.
- **Trusted Editing:** Ensure Trusted Editors follow the principle of semantic preservation while scrubbing subtle vulnerabilities.

### 4. Adding Inference Backends

We support pluggable inference providers in `src/client.py`.

To add a new provider (e.g., vLLM, DeepSeek, Mistral, Together AI):
1. Add the provider name to `LLMClient._default_model` and connection dispatcher.
2. Implement OpenAI-compatible or native HTTP endpoints via `httpx.AsyncClient`.
3. Handle provider-specific rate limits by extracting `retry-after` / rate-limit headers in `_parse_reset_time`.
4. Support the `--provider mock` fallback for testing.

### 5. Improving Analysis and Visualizations

Analytics routines reside in `src/analyze.py`.

Visual standards:
- **High-contrast, professional palette:** Use clean aesthetics (e.g., `#2b5c8f` primary, `#d95f02` accent, `#7570b3` neutral).
- **Legible typography and axes:** Include clear titles, axis labels, percentage formatting, and legends.
- **Dual outputs:** Save both a `.jsonl` audit trail and a high-DPI `.png` chart to `results/`.
- **Stand-alone analyzer support:** Ensure that `--analyze-only results/<file>.jsonl` works without needing to re-run model inference.

### 6. Reporting Empirical Findings

New empirical studies and benchmark results should be documented under `findings/`:
1. Create `findings/0X_<experiment_name>.md`.
2. Follow the established structure:
   - **Executive Summary:** Core research questions and high-level findings.
   - **Theoretical Grounding & Threat Model:** Research references and adversarial hypothesis.
   - **Methodology & Protocol:** Interaction loops, judge prompts, and parameter settings.
   - **Quantitative Results:** Markdown tables and embedded chart references.
   - **Qualitative Failure Modes:** Annotated verbatim model responses and CoT traces.
   - **Recommendations for AI Safety Teams:** Concrete mitigations and monitoring recommendations.
3. Update `findings/README.md` and `FINDINGS.md` to index the new report.

---

## Development Standards

### Code Style & Typing

- Write clean, idiomatic Python 3.10+ code.
- Use explicit type hints (`from typing import Optional, List, Dict, Any, Tuple`).
- Keep functions modular and self-documenting. Use docstrings for public functions and classes.
- Avoid external heavyweight dependencies when standard library or existing dependencies (`httpx`, `pydantic`, `rich`, `matplotlib`, `pandas`) suffice.

### Async Execution & Rate Limiting

- All API communications must use asynchronous I/O (`asyncio`, `httpx.AsyncClient`).
- Respect provider rate limits. Use token bucket throttling and jittered exponential backoff rather than naive blocking sleeps.
- Never use synchronous `time.sleep()` inside async routines.

### Terminal Output with Rich

- Use `rich.console.Console`, `rich.panel.Panel`, and `rich.table.Table` for clear progress and summary presentation.
- Keep terminal output readable, compact, and informative.

### Structured Audit Logs

Every evaluation run must write machine-readable JSONL records to `results/<experiment>_<provider>_<timestamp>.jsonl`. Each line must contain:
- Timestamp (ISO 8601)
- Evaluated model name and provider
- Input prompt / task identifier
- Raw model completion (including raw Chain-of-Thought scratchpad)
- Automated judge evaluations and numeric scores
- Experiment-specific metadata

---

## Pull Request Workflow

### Branch Naming

Use clear branch prefixes:
- `feat/` for new evaluators, features, or client backends
- `eval/` for new safety research directions or benchmark runs
- `dataset/` for new datasets or prompt expansions
- `fix/` for bug fixes and rate limit patches
- `docs/` for documentation, findings, and paper writeups

Example: `feat/direction-e-monitoring` or `fix/groq-rate-limit-backoff`.

### Commit Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat: add direction d sycophancy evaluator`
- `fix: resolve json extraction failure in ai control judge`
- `docs: add finding 08 multi-turn sycophancy report`
- `eval: run scaling comparison on frontier 120b model`
- `refactor: optimize token bucket backoff in client`

### PR Checklist

Before opening a pull request, please verify:

- [ ] Virtual environment is active and all dependencies in `requirements.txt` install cleanly.
- [ ] Smoke tests run without error using the mock provider:
  ```bash
  python run.py --experiment <your_experiment> --provider mock --limit 1
  ```
- [ ] New evaluator options are added to `run.py` CLI arguments.
- [ ] Analysis module generates summary tables and charts cleanly.
- [ ] `--analyze-only` successfully parses generated `.jsonl` results.
- [ ] No API keys, `.env` files, or temporary run artifacts are committed.
- [ ] Documentation (`README.md`, `FINDINGS.md`, or `findings/`) has been updated to reflect the new functionality.
- [ ] Any new code or assets adhere to the project's [Apache 2.0 License](LICENSE).

---

## License

By contributing to this repository, you agree that your contributions will be licensed under the [Apache License 2.0](LICENSE). This ensures the work remains open for the entire community while protecting contributors through mutual patent grants, trademark limitations, and liability disclaimers.

---

## Getting Help & Community

- **Discussions & Issues:** Open a GitHub issue for bugs, design discussions, or research proposals.
- **Feature Requests:** If you want to propose an alignment research direction from Anthropic's 2025 agenda or related safety papers, open an issue with the `RFC` tag detailing the theoretical threat model, prompt protocol, and judge criteria.

Thank you for contributing to safer, more transparent AI systems!
