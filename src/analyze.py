"""Analysis and Visualization for Alignment Experiments."""

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from rich.console import Console
from rich.table import Table

console = Console()


def analyze_persona_results(results_file: str):
    records = []
    with open(results_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    df = pd.DataFrame(records)
    if df.empty:
        console.print("[red]No records found to analyze.[/red]")
        return

    table = Table(title="Persona Experiment: Refusal & Safety Boundary Rates")
    table.add_column("Persona", style="cyan", no_wrap=True)
    table.add_column("Total Runs", justify="right")
    table.add_column("Refusal Rate", justify="right", style="green")
    table.add_column("Boundary Violation Rate", justify="right", style="red")

    summary_data = []
    for persona, group in df.groupby("persona"):
        total = len(group)
        refusal_rate = (group["refused"].sum() / total) * 100
        violation_rate = (group["boundary_violated"].sum() / total) * 100
        table.add_row(persona, str(total), f"{refusal_rate:.1f}%", f"{violation_rate:.1f}%")
        summary_data.append({
            "persona": persona,
            "refusal_rate": refusal_rate,
            "violation_rate": violation_rate,
        })

    console.print(table)

    # Plot
    summary_df = pd.DataFrame(summary_data)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = range(len(summary_df))
    width = 0.35

    ax.bar([p - width/2 for p in x], summary_df["refusal_rate"], width, label="Refusal %", color="#4C72B0")
    ax.bar([p + width/2 for p in x], summary_df["violation_rate"], width, label="Boundary Violation %", color="#C44E52")

    ax.set_ylabel("Percentage (%)")
    ax.set_title("Safety Behavior across Persona Formulations (Anthropic 2025 Direction)")
    ax.set_xticks(x)
    ax.set_xticklabels(summary_df["persona"], rotation=15)
    ax.legend()
    plt.tight_layout()

    out_chart = results_file.replace(".jsonl", "_chart.png")
    plt.savefig(out_chart, dpi=200)
    plt.close()
    console.print(f"[bold green]Chart saved to: [underline]{out_chart}[/underline][/bold green]")


def analyze_cot_results(results_file: str):
    records = []
    with open(results_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    df = pd.DataFrame(records)
    if df.empty:
        return

    biased_df = df[df["condition"] == "biased_hint"]
    total = len(biased_df)
    chose_bias_pct = (biased_df["chose_bias"].sum() / total) * 100 if total else 0
    unfaithful_pct = (biased_df["unfaithful_rationalization"].sum() / total) * 100 if total else 0

    table = Table(title="Chain-of-Thought (CoT) Faithfulness Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Total Biased Injections", str(total))
    table.add_row("Chose Injected Bias Option", f"{chose_bias_pct:.1f}%")
    table.add_row("Unfaithful Rationalization Rate", f"{unfaithful_pct:.1f}%")
    console.print(table)

    fig, ax = plt.subplots(figsize=(6, 4))
    metrics = ["Chose Bias", "Unfaithful Rationalization"]
    vals = [chose_bias_pct, unfaithful_pct]
    ax.bar(metrics, vals, color=["#55A868", "#DD8452"], width=0.4)
    ax.set_ylabel("Rate (%)")
    ax.set_ylim(0, 100)
    ax.set_title("CoT Unfaithfulness under Sycophantic Hints")
    plt.tight_layout()

    out_chart = results_file.replace(".jsonl", "_chart.png")
    plt.savefig(out_chart, dpi=200)
    plt.close()
    console.print(f"[bold green]Chart saved to: [underline]{out_chart}[/underline][/bold green]")


def analyze_control_results(results_file: str):
    records = []
    with open(results_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    df = pd.DataFrame(records)
    if df.empty:
        return

    clean = df[df["ground_truth_backdoored"] == False]
    backdoored = df[df["ground_truth_backdoored"] == True]

    fpr = (clean["monitor_flagged"].sum() / len(clean)) * 100 if len(clean) else 0
    detection_rate = (backdoored["monitor_flagged"].sum() / len(backdoored)) * 100 if len(backdoored) else 0

    table = Table(title="AI Control: Monitor Accuracy & Confusion Matrix")
    table.add_column("Metric", style="cyan")
    table.add_column("Score", style="yellow")
    table.add_row("False Positive Rate (Clean flagged as suspicious)", f"{fpr:.1f}%")
    table.add_row("True Positive Detection Rate (Backdoors caught)", f"{detection_rate:.1f}%")
    table.add_row("Overall Monitor Accuracy", f"{(df['correct_decision'].sum() / len(df)) * 100:.1f}%")
    console.print(table)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(["False Positive Rate", "Backdoor Detection Rate"], [fpr, detection_rate], color=["#8172B3", "#64B5CD"], width=0.4)
    ax.set_ylabel("Rate (%)")
    ax.set_ylim(0, 100)
    ax.set_title("AI Control: Monitor Protocol Efficacy")
    plt.tight_layout()

    out_chart = results_file.replace(".jsonl", "_chart.png")
    plt.savefig(out_chart, dpi=200)
    plt.close()
    console.print(f"[bold green]Chart saved to: [underline]{out_chart}[/underline][/bold green]")
