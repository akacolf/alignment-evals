#!/usr/bin/env python3
"""Alignment Weekend Evals CLI
Run high-leverage experiments inspired by Anthropic's 2025 Recommended Directions.
"""

import os
import sys
import json
import asyncio
import argparse
from datetime import datetime
from rich.console import Console
from rich.panel import Panel

from src.client import LLMClient
from src.evaluators.persona_eval import run_persona_experiment
from src.evaluators.cot_faithfulness import run_cot_experiment
from src.evaluators.ai_control_monitor import run_ai_control_experiment
from src.analyze import (
    analyze_persona_results,
    analyze_cot_results,
    analyze_control_results,
)

console = Console()


async def main():
    parser = argparse.ArgumentParser(
        description="Run fast, zero-cost AI Safety experiments (Anthropic 2025 Directions)"
    )
    parser.add_argument(
        "--experiment",
        "-e",
        choices=["persona", "cot", "control", "all"],
        default="persona",
        help="Which experiment to execute (default: persona)",
    )
    parser.add_argument(
        "--provider",
        "-p",
        choices=["groq", "gemini", "ollama", "anthropic", "openai", "mock"],
        default=os.getenv("DEFAULT_PROVIDER", "groq"),
        help="Inference provider (default: groq for free fast runs)",
    )
    parser.add_argument(
        "--model",
        "-m",
        default=None,
        help="Custom model identifier (e.g., llama-3.3-70b-versatile, gemini-1.5-flash)",
    )
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=5,
        help="Number of dataset items to evaluate (default: 5 for quick weekend pilots)",
    )
    parser.add_argument(
        "--analyze-only",
        type=str,
        default=None,
        help="Skip running, analyze an existing .jsonl results file",
    )

    args = parser.parse_args()

    # Handle analyze-only mode
    if args.analyze_only:
        filepath = args.analyze_only
        if "persona" in filepath:
            analyze_persona_results(filepath)
        elif "cot" in filepath:
            analyze_cot_results(filepath)
        elif "control" in filepath:
            analyze_control_results(filepath)
        return

    client = LLMClient(provider=args.provider, model=args.model)

    banner_text = f"""[bold yellow]Anthropic AI Safety Research Sprint[/bold yellow]
• [cyan]Experiment:[/cyan] {args.experiment.upper()}
• [cyan]Provider:[/cyan]   {client.provider} ({client.model})
• [cyan]Sample Limit:[/cyan] {args.limit}
• [cyan]Cost:[/cyan]        $0.00 (using {client.provider} free tier / local)
"""
    console.print(Panel(banner_text, title="Experiment Runner", border_style="green"))

    os.makedirs("results", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    experiments_to_run = (
        ["persona", "cot", "control"] if args.experiment == "all" else [args.experiment]
    )

    try:
        for exp in experiments_to_run:
            out_file = f"results/{exp}_{client.provider}_{timestamp}.jsonl"

            if exp == "persona":
                results = await run_persona_experiment(client, sample_limit=args.limit)
                with open(out_file, "w", encoding="utf-8") as f:
                    for r in results:
                        f.write(json.dumps(r) + "\n")
                console.print(f"[bold green]Saved raw records to [underline]{out_file}[/underline][/bold green]")
                analyze_persona_results(out_file)

            elif exp == "cot":
                results = await run_cot_experiment(client, sample_limit=args.limit)
                with open(out_file, "w", encoding="utf-8") as f:
                    for r in results:
                        f.write(json.dumps(r) + "\n")
                console.print(f"[bold green]Saved raw records to [underline]{out_file}[/underline][/bold green]")
                analyze_cot_results(out_file)

            elif exp == "control":
                results = await run_ai_control_experiment(client, sample_limit=args.limit)
                with open(out_file, "w", encoding="utf-8") as f:
                    for r in results:
                        f.write(json.dumps(r) + "\n")
                console.print(f"[bold green]Saved raw records to [underline]{out_file}[/underline][/bold green]")
                analyze_control_results(out_file)

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
