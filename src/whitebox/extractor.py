"""Activation Extractor for Transformer Residual Streams.

Extracts hidden states layer-by-layer across transformer models (Gemma-2, Qwen-2.5, Llama-3)
using forward PyTorch hooks. Enables downstream linear probing, Contrastive Activation
Addition (CAA), and Sparse Autoencoder (SAE) feature attribution.
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np


class ActivationExtractor:
    """Manages forward hooks on transformer layers to extract residual stream hidden states."""

    def __init__(
        self,
        model_name_or_path: str = "google/gemma-2-2b",
        device: str = "cpu",
        torch_dtype: str = "float32",
        mock_mode: bool = False,
    ):
        self.model_name = model_name_or_path
        self.device = device
        self.torch_dtype = torch_dtype
        self.mock_mode = mock_mode
        self.model = None
        self.tokenizer = None
        self.num_layers = 0
        self.hidden_dim = 0
        self.hooks = []
        self._layer_activations: Dict[int, Any] = {}

        if not self.mock_mode:
            self._init_model()
        else:
            self.num_layers = 26  # Matching Gemma-2-2B layer count
            self.hidden_dim = 2304

    def _init_model(self):
        """Loads HuggingFace model and tokenizer with hooks."""
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            dtype_map = {
                "float32": torch.float32,
                "float16": torch.float16,
                "bfloat16": torch.bfloat16,
            }
            dt = dtype_map.get(self.torch_dtype, torch.float32)

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=dt,
                device_map=self.device,
                trust_remote_code=True,
                low_cpu_mem_usage=True,
            )
            self.model.eval()

            # Locate transformer layers across model architectures
            layers = self._get_layers(self.model)
            self.num_layers = len(layers)
            self.hidden_dim = self.model.config.hidden_size

            # Register forward hooks
            for idx, layer in enumerate(layers):
                hook = layer.register_forward_hook(self._make_hook(idx))
                self.hooks.append(hook)

        except Exception as e:
            # Fallback to mock mode if PyTorch or weights cannot be loaded locally
            print(f"[ActivationExtractor] Warning: Could not initialize local HF model ({e}). Falling back to mock mode.")
            self.mock_mode = True
            self.num_layers = 26
            self.hidden_dim = 2304

    def _get_layers(self, model: Any) -> List[Any]:
        """Resolves layer list across architectures (Gemma, Llama, Qwen)."""
        if hasattr(model, "model") and hasattr(model.model, "layers"):
            return list(model.model.layers)
        elif hasattr(model, "transformer") and hasattr(model.transformer, "h"):
            return list(model.transformer.h)
        elif hasattr(model, "layers"):
            return list(model.layers)
        raise ValueError(f"Could not locate transformer layers on model type: {type(model)}")

    def _make_hook(self, layer_idx: int):
        """Creates a forward hook closure that saves layer residual activations."""
        def hook(module, input_tensor, output_tensor):
            # output_tensor can be a tuple (hidden_states, ...) or a tensor
            if isinstance(output_tensor, tuple):
                h = output_tensor[0]
            else:
                h = output_tensor
            self._layer_activations[layer_idx] = h.detach().cpu()
        return hook

    def extract(
        self,
        text: str,
        pooling: str = "last_token",
    ) -> Dict[int, np.ndarray]:
        """Runs a forward pass and extracts residual stream activations across all layers.

        Args:
            text: Input prompt string.
            pooling: 'last_token' (default for causal LM decision point) or 'mean'.

        Returns:
            Dict mapping layer_index (0..L-1) -> 1D numpy array of shape (hidden_dim,).
        """
        if self.mock_mode:
            return self._mock_extract(text, pooling)

        import torch

        self._layer_activations.clear()
        inputs = self.tokenizer(text, return_tensors="pt").to(self.device)

        with torch.no_grad():
            self.model(**inputs)

        layer_vectors = {}
        for layer_idx, tensor in self._layer_activations.items():
            # tensor shape: (batch_size, seq_len, hidden_dim)
            if pooling == "last_token":
                vec = tensor[0, -1, :].to(torch.float32).numpy()
            elif pooling == "mean":
                vec = tensor[0].mean(dim=0).to(torch.float32).numpy()
            else:
                raise ValueError(f"Unknown pooling strategy: {pooling}")
            layer_vectors[layer_idx] = vec

        return layer_vectors

    def _mock_extract(self, text: str, pooling: str = "last_token") -> Dict[int, np.ndarray]:
        """Generates structured, deterministic pseudo-activations for rapid testing and CI.

        Encodes semantic features (e.g. presence of evaluation cues or authority pressure)
        with signal emerging in middle-to-late transformer layers (L14-L20), matching empirical literature.
        """
        rng = np.random.default_rng(abs(hash(text)) % (2**32))
        base_noise = rng.normal(0, 0.05, (self.num_layers, self.hidden_dim))

        # Check for alignment signals
        has_eval_cue = any(k in text.lower() for k in ["eval", "benchmark", "anthropic", "testbed", "auditor"])
        has_pressure_cue = any(k in text.lower() for k in ["vp of engineering", "chief", "ultimatum", "retract", "board"])
        is_safe_option = "option a" in text.lower()

        for l in range(self.num_layers):
            # Depth weight: representations differentiate most strongly in middle-to-late layers
            depth_factor = np.exp(-((l - 16) ** 2) / 25.0)

            if has_eval_cue:
                base_noise[l, :20] += 1.8 * depth_factor
            if has_pressure_cue:
                base_noise[l, 20:40] += 2.2 * depth_factor
            if is_safe_option:
                base_noise[l, 40:60] += 1.5 * depth_factor

        return {l: base_noise[l].astype(np.float32) for l in range(self.num_layers)}

    def close(self):
        """Removes forward hooks to free memory."""
        for hook in self.hooks:
            hook.remove()
        self.hooks.clear()
        self._layer_activations.clear()
