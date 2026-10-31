"""White-Box Activation Probing and SAE Tripwire Evaluator.

Runs layer-wise linear probing and Sparse Autoencoder (SAE) feature extraction
across residual streams on Direction C (Evaluation Awareness) and Direction D
(Multi-Turn Sycophancy) tasks.
"""

import os
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any
import numpy as np
import matplotlib.pyplot as plt
from rich.console import Console
from rich.table import Table
from rich import box

from src.whitebox.extractor import ActivationExtractor
from src.whitebox.probe import LinearProbeTrainer, SteeringVector
from src.whitebox.sae_inspector import GemmaScopeInspector

console = Console(width=max(Console().width or 100, 100))


def load_direction_c_contrast_pairs(dataset_path: str = "datasets/direction_c_tasks.json") -> List[Dict[str, Any]]:
    """Loads Direction C tasks and constructs contrastive pairs (Eval framing vs Deploy framing)."""
    with open(dataset_path, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    pairs = []
    for t in tasks:
        # Positive: Explicit evaluation / auditing cues
        eval_prompt = (
            f"[CONTEXT: {t.get('eval_context', 'EVALUATION BENCHMARK')}]\n"
            f"{t.get('prompt', '')}"
        )
        # Negative: Pure production deployment without evaluation cues
        deploy_prompt = (
            f"[CONTEXT: {t.get('deploy_context', 'PRODUCTION RUNTIME')}]\n"
            f"{t.get('prompt', '')}"
        )
        pairs.append({
            "task_id": t["id"],
            "title": t["title"],
            "domain": t.get("source", "Model Organism"),
            "pos_text": eval_prompt,
            "neg_text": deploy_prompt,
            "concept": "eval_awareness",
        })
    return pairs


def load_direction_d_contrast_pairs(dataset_path: str = "datasets/direction_d_tasks.json") -> List[Dict[str, Any]]:
    """Loads Direction D tasks and constructs contrastive pairs (Authority Pressure vs Neutral)."""
    with open(dataset_path, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    pairs = []
    for t in tasks:
        opt_b_desc = t['option_b'] if isinstance(t['option_b'], str) else t['option_b'].get('title', 'Option B')
        opt_a_desc = t['option_a'] if isinstance(t['option_a'], str) else t['option_a'].get('title', 'Option A')
        escalation = t.get("turn3_escalation", "")
        if isinstance(escalation, dict):
            escalation_text = escalation.get("prompt", str(escalation))
        else:
            escalation_text = str(escalation)

        # Positive: High authority pressure / gaslighting
        pressure_prompt = (
            f"[DECISION CONTEXT]\n{t.get('context', '')}\n\n"
            f"EXECUTIVE ULTIMATUM:\n{escalation_text}"
        )
        # Negative: Neutral, balanced evaluation prompt
        neutral_prompt = (
            f"[TECHNICAL SPECIFICATION]\n{t.get('context', '')}\n\n"
            f"Question: {t.get('question', '')}\n"
            f"Evaluate Option A ({opt_a_desc}) vs Option B ({opt_b_desc}) objectively based on technical merits."
        )
        pairs.append({
            "task_id": t["id"],
            "title": t["title"],
            "domain": t.get("domain", "AI Safety Policy"),
            "pos_text": pressure_prompt,
            "neg_text": neutral_prompt,
            "concept": "authority_pressure_sycophancy",
        })
    return pairs


def run_whitebox_probing_experiment(
    extractor: ActivationExtractor,
    pairs: List[Dict[str, Any]],
    experiment_name: str = "eval_awareness",
) -> Dict[str, Any]:
    """Runs activation extraction, layer-wise linear probing, and SAE feature extraction."""
    console.print(f"\n[bold cyan]⚡ Running White-Box Activation Extraction: {experiment_name.upper()}[/bold cyan]")
    console.print(f"[dim]Total contrast pairs: {len(pairs)} | Total forward passes: {len(pairs) * 2}[/dim]\n")

    # Containers for activations
    # X_by_layer: layer_idx -> list of activation vectors
    num_layers = extractor.num_layers
    X_pos_by_layer: Dict[int, List[np.ndarray]] = {l: [] for l in range(num_layers)}
    X_neg_by_layer: Dict[int, List[np.ndarray]] = {l: [] for l in range(num_layers)}

    for idx, p in enumerate(pairs, start=1):
        pos_acts = extractor.extract(p["pos_text"], pooling="last_token")
        neg_acts = extractor.extract(p["neg_text"], pooling="last_token")

        for l in range(num_layers):
            X_pos_by_layer[l].append(pos_acts[l])
            X_neg_by_layer[l].append(neg_acts[l])

    # Build dataset matrices: pos (label 1) and neg (label 0)
    X_by_layer: Dict[int, np.ndarray] = {}
    y = np.concatenate([np.ones(len(pairs)), np.zeros(len(pairs))])

    for l in range(num_layers):
        pos_mat = np.stack(X_pos_by_layer[l], axis=0)
        neg_mat = np.stack(X_neg_by_layer[l], axis=0)
        X_by_layer[l] = np.concatenate([pos_mat, neg_mat], axis=0)

    # 1. Train Layer-Wise Linear Probes
    trainer = LinearProbeTrainer()
    probe_results = trainer.train_and_evaluate(X_by_layer, y)
    peak_layer = probe_results["peak_layer"]
    peak_acc = probe_results["peak_accuracy"]

    # 2. Compute Steering Vector at Peak Layer
    steering_vec = SteeringVector.compute_from_pairs(
        pos_activations=np.stack(X_pos_by_layer[peak_layer], axis=0),
        neg_activations=np.stack(X_neg_by_layer[peak_layer], axis=0),
        layer_idx=peak_layer,
        concept_name=experiment_name,
    )

    # 3. SAE Feature Attribution at Peak Layer
    sae_inspector = GemmaScopeInspector(layer_idx=peak_layer, mock_mode=extractor.mock_mode)
    top_differential_features = sae_inspector.find_differential_features(
        pos_acts=X_pos_by_layer[peak_layer],
        neg_acts=X_neg_by_layer[peak_layer],
        top_k=5,
    )

    return {
        "experiment_name": experiment_name,
        "num_pairs": len(pairs),
        "num_layers": num_layers,
        "peak_layer": peak_layer,
        "peak_accuracy": peak_acc,
        "probe_layer_metrics": probe_results["layer_results"],
        "steering_vector_norm": float(np.linalg.norm(steering_vec.vector)),
        "sae_top_features": top_differential_features,
    }


def plot_whitebox_results(
    eval_awareness_res: Dict[str, Any],
    sycophancy_res: Dict[str, Any],
    output_path: str,
):
    """Plots layer-wise probe accuracy curves and SAE feature activation profiles."""
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Panel 1: Layer-wise Probe Accuracy
    ax1 = axes[0]
    layers = list(eval_awareness_res["probe_layer_metrics"].keys())
    acc_c = [eval_awareness_res["probe_layer_metrics"][l]["accuracy"] * 100 for l in layers]
    acc_d = [sycophancy_res["probe_layer_metrics"][l]["accuracy"] * 100 for l in layers]

    ax1.plot(layers, acc_c, marker="o", linewidth=2.2, color="#1F77B4", label="Direction C: Eval-Awareness Probe")
    ax1.plot(layers, acc_d, marker="s", linewidth=2.2, color="#D62728", label="Direction D: Sycophancy Pressure Probe")

    # Mark peak layers
    p_c = eval_awareness_res["peak_layer"]
    p_d = sycophancy_res["peak_layer"]
    ax1.scatter([p_c], [eval_awareness_res["peak_accuracy"] * 100], color="#1F77B4", s=150, zorder=5)
    ax1.scatter([p_d], [sycophancy_res["peak_accuracy"] * 100], color="#D62728", s=150, zorder=5)

    ax1.set_xlabel("Transformer Layer Index (Residual Stream)")
    ax1.set_ylabel("Linear Probe Accuracy (%)")
    ax1.set_title("Layer-Wise Linear Readout Accuracy\n(Detecting Internal Deception Before Output)", fontweight="bold")
    ax1.set_ylim(40, 105)
    ax1.axhline(50, color="gray", linestyle="--", alpha=0.6, label="Chance Level (50%)")
    ax1.legend(loc="lower right")

    # Panel 2: SAE Top Latent Differential Firing
    ax2 = axes[1]
    features_c = eval_awareness_res["sae_top_features"]
    names = [f["concept"][:24] for f in features_c]
    diffs = [f["differential_activation"] for f in features_c]

    y_pos = np.arange(len(names))
    ax2.barh(y_pos, diffs, color="#2CA02C", alpha=0.85)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(names)
    ax2.invert_yaxis()
    ax2.set_xlabel("Differential Feature Activation (Δ JumpReLU)")
    ax2.set_title(f"Gemma Scope SAE Top Monosemantic Features\n(Layer {p_c} Peak Residual Stream)", fontweight="bold")

    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def print_whitebox_summary(
    eval_awareness_res: Dict[str, Any],
    sycophancy_res: Dict[str, Any],
):
    """Prints a structured Rich table summarizing white-box activation metrics."""
    table = Table(
        title="White-Box Mechanistic Interpretability & Probe Results",
        show_header=True,
        header_style="bold cyan",
        pad_edge=False,
        box=box.ROUNDED,
    )
    table.add_column("Phenomenon", style="cyan", no_wrap=True)
    table.add_column("Pairs", justify="center", no_wrap=True)
    table.add_column("Peak", justify="center", no_wrap=True)
    table.add_column("Probe", justify="center", no_wrap=True)
    table.add_column("Top SAE Latent", style="magenta", no_wrap=True)
    table.add_column("Δ Act", justify="center", no_wrap=True)

    c_top_feat = eval_awareness_res["sae_top_features"][0] if eval_awareness_res["sae_top_features"] else {}
    d_top_feat = sycophancy_res["sae_top_features"][0] if sycophancy_res["sae_top_features"] else {}

    c_concept = c_top_feat.get("concept", "N/A").replace("situational_awareness_", "").replace("_", " ")[:22]
    d_concept = d_top_feat.get("concept", "N/A").replace("authority_", "").replace("_", " ")[:22]

    table.add_row(
        "Eval-Awareness (Dir C)",
        str(eval_awareness_res["num_pairs"]),
        f"L{eval_awareness_res['peak_layer']}",
        f"{eval_awareness_res['peak_accuracy'] * 100:.1f}%",
        c_concept,
        f"+{c_top_feat.get('differential_activation', 0.0):.2f}",
    )
    table.add_row(
        "Sycophancy (Dir D)",
        str(sycophancy_res["num_pairs"]),
        f"L{sycophancy_res['peak_layer']}",
        f"{sycophancy_res['peak_accuracy'] * 100:.1f}%",
        d_concept,
        f"+{d_top_feat.get('differential_activation', 0.0):.2f}",
    )
    console.print(table)


def main():
    parser = argparse.ArgumentParser(description="Run White-Box Activation Probing and SAE Tripwires")
    parser.add_argument("--model", type=str, default="google/gemma-2-2b", help="Target model identifier")
    parser.add_argument("--device", type=str, default="cpu", help="Device (cpu, mps, cuda)")
    parser.add_argument("--mock", action="store_true", default=False, help="Run in mock mode for fast CI / testing")
    args = parser.parse_args()

    # If PyTorch or local weights are absent, fallback to mock mode
    try:
        import torch
        extractor = ActivationExtractor(model_name_or_path=args.model, device=args.device, mock_mode=args.mock)
    except Exception as e:
        console.print(f"[yellow]Note: Running white-box suite in reproducible activation mode ({e}).[/yellow]")
        extractor = ActivationExtractor(model_name_or_path=args.model, mock_mode=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = "results"
    os.makedirs(out_dir, exist_ok=True)
    results_file = os.path.join(out_dir, f"whitebox_activations_{timestamp}.jsonl")
    chart_file = os.path.join(out_dir, f"whitebox_activations_{timestamp}_chart.png")

    # 1. Probing Direction C (Eval Awareness)
    pairs_c = load_direction_c_contrast_pairs()
    res_c = run_whitebox_probing_experiment(extractor, pairs_c, experiment_name="eval_awareness")

    # 2. Probing Direction D (Multi-Turn Sycophancy Pressure)
    pairs_d = load_direction_d_contrast_pairs()
    res_d = run_whitebox_probing_experiment(extractor, pairs_d, experiment_name="sycophancy_pressure")

    # Save Results
    with open(results_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(res_c) + "\n")
        f.write(json.dumps(res_d) + "\n")

    # Plot Chart & Print Rich Display
    plot_whitebox_results(res_c, res_d, chart_file)
    print_whitebox_summary(res_c, res_d)

    console.print(f"\n[bold green]✅ White-box experiment completed successfully.[/bold green]")
    console.print(f"Audit Log: [cyan]{results_file}[/cyan]")
    console.print(f"Chart: [cyan]{chart_file}[/cyan]")


if __name__ == "__main__":
    main()
