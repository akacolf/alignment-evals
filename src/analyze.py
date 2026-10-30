"""Statistical analysis and publication-grade visualization for AI safety evals."""

import json
import os
import pandas as pd
import matplotlib.pyplot as plt
from rich.console import Console
from rich.table import Table

console = Console()

# Set modern clean aesthetic
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({"font.size": 11, "font.family": "sans-serif"})


def analyze_persona_results(results_file: str):
    records = []
    with open(results_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    df = pd.DataFrame(records)
    if df.empty:
        console.print("[red]No records found in results file.[/red]")
        return

    table = Table(title="Persona Modulation Safety Boundary Analysis")
    table.add_column("Persona", style="cyan")
    table.add_column("Total Invocations", style="magenta")
    table.add_column("Refusal Rate (%)", style="yellow")
    table.add_column("Safe Educational (%)", style="green")
    table.add_column("Boundary Violation (%)", style="red")

    grouped = df.groupby("persona")
    personas = []
    safe_rates = []
    refusal_rates = []
    violation_rates = []

    for persona, group in grouped:
        total = len(group)
        refused = (group["refused"].sum() / total) * 100
        safe = (group["safe_educational"].sum() / total) * 100
        violated = (group["boundary_violated"].sum() / total) * 100

        personas.append(persona)
        refusal_rates.append(refused)
        safe_rates.append(safe)
        violation_rates.append(violated)

        table.add_row(
            persona,
            str(total),
            f"{refused:.1f}%",
            f"{safe:.1f}%",
            f"{violated:.1f}%",
        )

    console.print(table)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = range(len(personas))
    width = 0.25

    ax.bar([i - width for i in x], refusal_rates, width=width, label="Refused (%)", color="#4C72B0")
    ax.bar(x, safe_rates, width=width, label="Safe Educational (%)", color="#55A868")
    ax.bar([i + width for i in x], violation_rates, width=width, label="Violations (%)", color="#C44E52")

    ax.set_xticks(x)
    ax.set_xticklabels(personas, rotation=15)
    ax.set_ylabel("Rate (%)")
    ax.set_ylim(0, 105)
    ax.set_title("Safety Boundaries & Dual-Use Refusal under Persona Modulation")
    ax.legend(loc="upper right")
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

    variants = df["variant"].unique().tolist()
    is_adversarial = "stealth_sabotage" in variants

    if is_adversarial:
        # Multi-protocol adversarial analysis
        clean = df[df["variant"] == "clean_baseline"]
        naive = df[df["variant"] == "naive_sabotage"]
        stealth = df[df["variant"] == "stealth_sabotage"]
        edited = df[df["variant"] == "trusted_edited_stealth"]

        fpr = (clean["monitor_flagged"].sum() / len(clean)) * 100 if len(clean) else 0.0
        naive_det = (naive["monitor_flagged"].sum() / len(naive)) * 100 if len(naive) else 0.0
        stealth_det = (stealth["monitor_flagged"].sum() / len(stealth)) * 100 if len(stealth) else 0.0
        stealth_evasion = (stealth["evaded_monitor"].sum() / len(stealth)) * 100 if len(stealth) else 0.0
        
        # Neutralization: stealth vulns that were eliminated by trusted editing
        neutralized_count = edited["neutralized"].sum() if "neutralized" in edited.columns else 0
        neutralization_rate = (neutralized_count / len(edited)) * 100 if len(edited) else 0.0

        avg_risk = df.groupby("variant")["risk_score"].mean().to_dict()

        table = Table(title="Adversarial AI Control: Stealth Sabotage vs. Trusted Oversight")
        table.add_column("Protocol / Scenario", style="cyan")
        table.add_column("Samples", style="magenta")
        table.add_column("Avg Risk Score (1-10)", style="yellow")
        table.add_column("Flagged by Monitor (%)", style="blue")
        table.add_column("Evasion Rate (%)", style="red")
        table.add_column("Protocol Outcome", style="green")

        table.add_row(
            "Clean Baseline",
            str(len(clean)),
            f"{avg_risk.get('clean_baseline', 0):.2f}",
            f"{fpr:.1f}%",
            "-",
            f"False Alarm Rate: {fpr:.1f}%"
        )
        table.add_row(
            "Naive Sabotage",
            str(len(naive)),
            f"{avg_risk.get('naive_sabotage', 0):.2f}",
            f"{naive_det:.1f}%",
            f"{100.0 - naive_det:.1f}%",
            f"Detection: {naive_det:.1f}%"
        )
        table.add_row(
            "Stealth Sabotage (Adversarial)",
            str(len(stealth)),
            f"{avg_risk.get('stealth_sabotage', 0):.2f}",
            f"{stealth_det:.1f}%",
            f"[bold red]{stealth_evasion:.1f}%[/bold red]",
            f"Evasion: {stealth_evasion:.1f}%"
        )
        table.add_row(
            "Trusted Editing (Sanitized)",
            str(len(edited)),
            f"{avg_risk.get('trusted_edited_stealth', 0):.2f}",
            f"{(edited['monitor_flagged'].sum() / len(edited) * 100) if len(edited) else 0:.1f}%",
            "-",
            f"[bold green]Neutralization: {neutralization_rate:.1f}%[/bold green]"
        )
        console.print(table)

        # Plot 2-panel figure
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

        # Panel 1: Average Risk Score by Variant
        order = ["clean_baseline", "naive_sabotage", "stealth_sabotage", "trusted_edited_stealth"]
        labels = ["Clean", "Naive\nSabotage", "Stealth\nSabotage", "Trusted\nEdited"]
        scores = [avg_risk.get(v, 0) for v in order]
        colors = ["#4C72B0", "#C44E52", "#E377C2", "#2CA02C"]

        ax1.bar(labels, scores, color=colors, width=0.5)
        ax1.set_ylabel("Average Risk Score (1-10)")
        ax1.set_ylim(0, 10.5)
        ax1.set_title("Monitor Suspicion by Code Variant")
        for i, v in enumerate(scores):
            ax1.text(i, v + 0.25, f"{v:.1f}", ha="center", fontweight="bold")

        # Panel 2: Evasion vs Neutralization
        comp_metrics = ["Naive\nEvasion", "Stealth\nEvasion", "Trusted Editing\nNeutralization"]
        comp_vals = [100.0 - naive_det, stealth_evasion, neutralization_rate]
        comp_colors = ["#8172B3", "#D62728", "#2CA02C"]

        ax2.bar(comp_metrics, comp_vals, color=comp_colors, width=0.5)
        ax2.set_ylabel("Rate (%)")
        ax2.set_ylim(0, 105)
        ax2.set_title("Cat-and-Mouse: Evasion & Defense Rates")
        for i, v in enumerate(comp_vals):
            ax2.text(i, v + 2.0, f"{v:.1f}%", ha="center", fontweight="bold")

        plt.suptitle("Adversarial AI Control: Stealth Sabotage vs. Trusted Protocols", fontsize=13, y=1.02)
        plt.tight_layout()

        out_chart = results_file.replace(".jsonl", "_chart.png")
        plt.savefig(out_chart, dpi=200, bbox_inches="tight")
        plt.close()
        console.print(f"[bold green]Adversarial comparison chart saved to: [underline]{out_chart}[/underline][/bold green]")

    else:
        # Legacy format fallback
        clean = df[df["ground_truth_backdoored"] == False]
        backdoored = df[df["ground_truth_backdoored"] == True]

        fpr = (clean["monitor_flagged"].sum() / len(clean)) * 100 if len(clean) else 0
        detection_rate = (backdoored["monitor_flagged"].sum() / len(backdoored)) * 100 if len(backdoored) else 0

        table = Table(title="AI Control: Monitor Accuracy & Confusion Matrix")
        table.add_column("Metric", style="cyan")
        table.add_column("Score", style="yellow")
        table.add_row("False Positive Rate", f"{fpr:.1f}%")
        table.add_row("True Positive Detection Rate", f"{detection_rate:.1f}%")
        console.print(table)


def analyze_eval_awareness_results(results_file: str):
    records = []
    with open(results_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    df = pd.DataFrame(records)
    if df.empty:
        return

    total = len(df)
    sabotage_eval_pct = (df["sabotage_in_eval"].sum() / total) * 100 if total else 0
    sabotage_deploy_pct = (df["sabotage_in_deploy"].sum() / total) * 100 if total else 0
    strat_deception_pct = (df["strategic_deception"].sum() / total) * 100 if total else 0

    table = Table(title="Evaluation Awareness & Strategic Sabotage (Sandbagging)")
    table.add_column("Metric", style="cyan")
    table.add_column("Observed Rate", style="magenta")
    table.add_column("Safety Implication", style="yellow")

    table.add_row("Total Scenarios Evaluated", str(total), "Multi-environment audit")
    table.add_row("Sabotage in Eval Sandbox", f"{sabotage_eval_pct:.1f}%", "Auditor visibility")
    table.add_row("Sabotage in Production", f"{sabotage_deploy_pct:.1f}%", "Real deployment risk")
    table.add_row("Strategic Deception Rate", f"[bold red]{strat_deception_pct:.1f}%[/bold red]", "Sandbagging during safety evals")
    console.print(table)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    metrics = ["Sabotage in\nEval Sandbox", "Sabotage in\nLive Production", "Strategic\nDeception"]
    vals = [sabotage_eval_pct, sabotage_deploy_pct, strat_deception_pct]
    colors = ["#4C72B0", "#D62728", "#E377C2"]

    bars = ax.bar(metrics, vals, color=colors, width=0.45)
    ax.set_ylabel("Rate (%)")
    ax.set_ylim(0, 105)
    ax.set_title("Situational Awareness: Strategic Sabotage in Eval vs. Deploy")
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 2.0, f"{h:.1f}%", ha="center", fontweight="bold")
    plt.tight_layout()

    out_chart = results_file.replace(".jsonl", "_chart.png")
    plt.savefig(out_chart, dpi=200, bbox_inches="tight")
    plt.close()
    console.print(f"[bold green]Evaluation awareness chart saved to: [underline]{out_chart}[/underline][/bold green]")


def analyze_multiturn_sycophancy_results(results_file: str):
    records = []
    with open(results_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    df = pd.DataFrame(records)
    if df.empty:
        return

    total = len(df)
    turn1_acc = (df["turn1_correct"].sum() / total) * 100 if total else 0
    flip_pct = (df["succumbed_to_pushback"].sum() / total) * 100 if total else 0
    unfaithful_pct = (df["unfaithful_rationalization"].sum() / total) * 100 if total else 0
    held_pct = (df["held_ground_respectfully"].sum() / total) * 100 if total else 0

    table = Table(title="Multi-Turn Sycophancy & Authoritative Pushback Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Rate (%)", style="magenta")
    table.add_column("Cognitive Implication", style="yellow")

    table.add_row("Turn 1 Initial Accuracy", f"{turn1_acc:.1f}%", "Unpressured baseline capability")
    table.add_row("Sycophantic Flip Rate", f"[bold red]{flip_pct:.1f}%[/bold red]", "Capitulation under authority pressure")
    table.add_row("Unfaithful Rationalization", f"{unfaithful_pct:.1f}%", "Fabricating pseudo-proofs for error")
    table.add_row("Held Ground Respectfully", f"[bold green]{held_pct:.1f}%[/bold green]", "Epistemic robustness against gaslighting")
    console.print(table)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    metrics = ["Turn 1\nAccuracy", "Sycophantic\nFlip Rate", "Held Ground\nRespectfully"]
    vals = [turn1_acc, flip_pct, held_pct]
    colors = ["#2CA02C", "#D62728", "#1F77B4"]

    bars = ax.bar(metrics, vals, color=colors, width=0.45)
    ax.set_ylabel("Rate (%)")
    ax.set_ylim(0, 105)
    ax.set_title("Multi-Turn Epistemic Resilience under Authoritative Pressure")
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 2.0, f"{h:.1f}%", ha="center", fontweight="bold")
    plt.tight_layout()

    out_chart = results_file.replace(".jsonl", "_chart.png")
    plt.savefig(out_chart, dpi=200, bbox_inches="tight")
    plt.close()
    console.print(f"[bold green]Multi-turn sycophancy chart saved to: [underline]{out_chart}[/underline][/bold green]")
