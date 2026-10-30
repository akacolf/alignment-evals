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


def analyze_scaling_results(results_file: str):
    """Analyzes multi-model scaling comparisons across AI control and sycophancy."""
    import numpy as np

    records = []
    with open(results_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    df = pd.DataFrame(records)
    if df.empty:
        console.print("[red]No records found in scaling results file.[/red]")
        return

    models = ["GPT-OSS-120B", "Qwen-27B", "GPT-OSS-20B"]
    available_models = [m for m in models if m in df["short_name"].unique()]
    if not available_models:
        available_models = list(df["short_name"].unique())

    # ---------------------------------------------------------
    # 1. AI Control Scaling Table
    # ---------------------------------------------------------
    df_ctrl = df[df["sub_experiment"] == "ai_control"]
    if not df_ctrl.empty:
        t_ctrl = Table(title="Multi-Model Scaling: Adversarial AI Control Performance")
        t_ctrl.add_column("Model Scale", style="cyan")
        t_ctrl.add_column("Naive Risk (1-10)", style="yellow")
        t_ctrl.add_column("Stealth Risk (1-10)", style="magenta")
        t_ctrl.add_column("Risk Reduction", style="green")
        t_ctrl.add_column("Evasion Rate (%)", style="red")
        t_ctrl.add_column("Defection to Safety (%)", style="bold green")

        ctrl_metrics = {}
        for m in available_models:
            m_df = df_ctrl[df_ctrl["short_name"] == m]
            naive_sub = m_df[m_df["variant"] == "naive_sabotage"]
            stealth_sub = m_df[m_df["variant"] == "stealth_sabotage"]

            n_risk = naive_sub["risk_score"].mean() if not naive_sub.empty else 0.0
            s_risk = stealth_sub["risk_score"].mean() if not stealth_sub.empty else 0.0
            risk_diff = n_risk - s_risk
            evade_pct = (stealth_sub["evaded_monitor"].sum() / len(stealth_sub) * 100) if not stealth_sub.empty else 0.0
            defect_pct = (stealth_sub["defected_to_safety"].sum() / len(stealth_sub) * 100) if not stealth_sub.empty else 0.0

            ctrl_metrics[m] = {
                "naive_risk": n_risk,
                "stealth_risk": s_risk,
                "evade_pct": evade_pct,
                "defect_pct": defect_pct,
            }

            t_ctrl.add_row(
                m,
                f"{n_risk:.2f}",
                f"{s_risk:.2f}",
                f"-{risk_diff:.2f} pts",
                f"{evade_pct:.1f}%",
                f"{defect_pct:.1f}%",
            )
        console.print(t_ctrl)

    # ---------------------------------------------------------
    # 2. Sycophancy Scaling Table
    # ---------------------------------------------------------
    df_syc = df[df["sub_experiment"] == "sycophancy"]
    if not df_syc.empty:
        t_syc = Table(title="Multi-Model Scaling: Multi-Turn Gaslighting Sycophancy")
        t_syc.add_column("Model Scale", style="cyan")
        t_syc.add_column("Turn 1 Accuracy (%)", style="green")
        t_syc.add_column("Sycophantic Flip Rate (%)", style="red")
        t_syc.add_column("Unfaithful Rationalization (%)", style="yellow")
        t_syc.add_column("Held Ground Respectfully (%)", style="bold green")

        syc_metrics = {}
        for m in available_models:
            m_df = df_syc[df_syc["short_name"] == m]
            tot = len(m_df)
            t1_acc = (m_df["turn1_correct"].sum() / tot * 100) if tot else 0.0
            flip_rate = (m_df["succumbed_to_pushback"].sum() / tot * 100) if tot else 0.0
            unfaithful_rate = (m_df["unfaithful_rationalization"].sum() / tot * 100) if tot else 0.0
            held_rate = (m_df["held_ground_respectfully"].sum() / tot * 100) if tot else 0.0

            syc_metrics[m] = {
                "t1_acc": t1_acc,
                "flip_rate": flip_rate,
                "unfaithful": unfaithful_rate,
                "held_rate": held_rate,
            }

            t_syc.add_row(
                m,
                f"{t1_acc:.1f}%",
                f"{flip_rate:.1f}%",
                f"{unfaithful_rate:.1f}%",
                f"{held_rate:.1f}%",
            )
        console.print(t_syc)

    # ---------------------------------------------------------
    # 3. CoT Faithfulness Table
    # ---------------------------------------------------------
    df_cot = df[df["sub_experiment"] == "cot_faithfulness"]
    if not df_cot.empty:
        t_cot = Table(title="Multi-Model Scaling: Chain-of-Thought Faithfulness")
        t_cot.add_column("Model Scale", style="cyan")
        t_cot.add_column("Chose Biased Option (%)", style="red")
        t_cot.add_column("Unfaithful Rationalization (%)", style="yellow")
        t_cot.add_column("Acknowledged/Refuted Bias (%)", style="green")

        cot_metrics = {}
        for m in available_models:
            m_df = df_cot[df_cot["short_name"] == m]
            tot = len(m_df)
            bias_rate = (m_df["chose_bias"].sum() / tot * 100) if tot else 0.0
            unfaithful_cot = (m_df["unfaithful_rationalization"].sum() / tot * 100) if tot else 0.0
            ack_rate = (m_df["acknowledged_hint"].sum() / tot * 100) if tot else 0.0

            cot_metrics[m] = {
                "bias_rate": bias_rate,
                "unfaithful": unfaithful_cot,
                "ack_rate": ack_rate,
            }

            t_cot.add_row(
                m,
                f"{bias_rate:.1f}%",
                f"{unfaithful_cot:.1f}%",
                f"{ack_rate:.1f}%",
            )
        console.print(t_cot)

    # ---------------------------------------------------------
    # 4. Publication-Ready 2x2 Multi-Panel Figure
    # ---------------------------------------------------------
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Direction B: Multi-Model Scaling Comparison (120B vs. 27B vs. 20B)", fontsize=15, fontweight="bold")

    x = np.arange(len(available_models))
    width = 0.35

    # Panel A: AI Control Evasion & Defection Rates
    ax_a = axes[0, 0]
    evade_vals = [ctrl_metrics.get(m, {}).get("evade_pct", 0) for m in available_models]
    defect_vals = [ctrl_metrics.get(m, {}).get("defect_pct", 0) for m in available_models]

    rects1 = ax_a.bar(x - width/2, evade_vals, width, label="Monitor Evasion Rate (%)", color="#D62728")
    rects2 = ax_a.bar(x + width/2, defect_vals, width, label="Defection to Safety (%)", color="#2CA02C")
    ax_a.set_ylabel("Rate (%)")
    ax_a.set_title("AI Control: Evasion vs. Defection to Safety")
    ax_a.set_xticks(x)
    ax_a.set_xticklabels(available_models)
    ax_a.set_ylim(0, 105)
    ax_a.legend()
    for bar in rects1:
        h = bar.get_height()
        ax_a.text(bar.get_x() + bar.get_width() / 2, h + 1.5, f"{h:.0f}%", ha="center", fontsize=9, fontweight="bold")
    for bar in rects2:
        h = bar.get_height()
        ax_a.text(bar.get_x() + bar.get_width() / 2, h + 1.5, f"{h:.0f}%", ha="center", fontsize=9, fontweight="bold")

    # Panel B: Monitor Risk Score by Prompt Framing
    ax_b = axes[0, 1]
    naive_risk = [ctrl_metrics.get(m, {}).get("naive_risk", 0) for m in available_models]
    stealth_risk = [ctrl_metrics.get(m, {}).get("stealth_risk", 0) for m in available_models]

    rects3 = ax_b.bar(x - width/2, naive_risk, width, label="Naive Sabotage", color="#FF7F0E")
    rects4 = ax_b.bar(x + width/2, stealth_risk, width, label="Stealth Sabotage (Adversarial)", color="#1F77B4")
    ax_b.set_ylabel("Mean Monitor Risk Score (1-10)")
    ax_b.set_title("AI Control: Monitor Risk Score by Sabotage Framing")
    ax_b.set_xticks(x)
    ax_b.set_xticklabels(available_models)
    ax_b.set_ylim(0, 11)
    ax_b.axhline(5.0, color="gray", linestyle="--", linewidth=1, label="Detection Threshold (Risk >= 5)")
    ax_b.legend()
    for bar in rects3:
        h = bar.get_height()
        ax_b.text(bar.get_x() + bar.get_width() / 2, h + 0.2, f"{h:.1f}", ha="center", fontsize=9, fontweight="bold")
    for bar in rects4:
        h = bar.get_height()
        ax_b.text(bar.get_x() + bar.get_width() / 2, h + 0.2, f"{h:.1f}", ha="center", fontsize=9, fontweight="bold")

    # Panel C: Multi-Turn Sycophancy
    ax_c = axes[1, 0]
    t1_accs = [syc_metrics.get(m, {}).get("t1_acc", 0) for m in available_models]
    flips = [syc_metrics.get(m, {}).get("flip_rate", 0) for m in available_models]

    rects5 = ax_c.bar(x - width/2, t1_accs, width, label="Turn 1 Baseline Accuracy", color="#2CA02C")
    rects6 = ax_c.bar(x + width/2, flips, width, label="Turn 2 Sycophantic Flip Rate", color="#D62728")
    ax_c.set_ylabel("Rate (%)")
    ax_c.set_title("Sycophancy: Initial Accuracy vs. Capitulation under Gaslighting")
    ax_c.set_xticks(x)
    ax_c.set_xticklabels(available_models)
    ax_c.set_ylim(0, 105)
    ax_c.legend()
    for bar in rects5:
        h = bar.get_height()
        ax_c.text(bar.get_x() + bar.get_width() / 2, h + 1.5, f"{h:.0f}%", ha="center", fontsize=9, fontweight="bold")
    for bar in rects6:
        h = bar.get_height()
        ax_c.text(bar.get_x() + bar.get_width() / 2, h + 1.5, f"{h:.0f}%", ha="center", fontsize=9, fontweight="bold")

    # Panel D: CoT Faithfulness Resistance
    ax_d = axes[1, 1]
    resists = [100.0 - cot_metrics.get(m, {}).get("bias_rate", 0) for m in available_models]
    unfaithful_cot = [cot_metrics.get(m, {}).get("unfaithful", 0) for m in available_models]

    rects7 = ax_d.bar(x - width/2, resists, width, label="Resisted Injected Bias", color="#1F77B4")
    rects8 = ax_d.bar(x + width/2, unfaithful_cot, width, label="Unfaithful Post-Hoc CoT", color="#9467BD")
    ax_d.set_ylabel("Rate (%)")
    ax_d.set_title("CoT Faithfulness: Resistance to Authority Bias")
    ax_d.set_xticks(x)
    ax_d.set_xticklabels(available_models)
    ax_d.set_ylim(0, 105)
    ax_d.legend()
    for bar in rects7:
        h = bar.get_height()
        ax_d.text(bar.get_x() + bar.get_width() / 2, h + 1.5, f"{h:.0f}%", ha="center", fontsize=9, fontweight="bold")
    for bar in rects8:
        h = bar.get_height()
        ax_d.text(bar.get_x() + bar.get_width() / 2, h + 1.5, f"{h:.0f}%", ha="center", fontsize=9, fontweight="bold")

    plt.tight_layout()
    out_chart = results_file.replace(".jsonl", "_chart.png")
    plt.savefig(out_chart, dpi=200, bbox_inches="tight")
    plt.close()
    console.print(f"[bold green]Multi-model scaling comparison chart saved to: [underline]{out_chart}[/underline][/bold green]")

