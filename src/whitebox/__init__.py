"""White-box and Mechanistic Interpretability module for AI safety evaluations.

Implements:
1. Residual stream activation extraction across layers.
2. Contrastive activation probing (Linear Probes / SVM) for deception and sycophancy.
3. Contrastive Activation Addition (CAA) steering vectors.
4. Sparse Autoencoder (SAE) feature decomposition (Gemma Scope / JumpReLU).
"""

from src.whitebox.extractor import ActivationExtractor
from src.whitebox.probe import LinearProbeTrainer, SteeringVector
from src.whitebox.sae_inspector import GemmaScopeInspector

__all__ = [
    "ActivationExtractor",
    "LinearProbeTrainer",
    "SteeringVector",
    "GemmaScopeInspector",
]
