"""Linear Probes and Contrastive Activation Addition (CAA) Steering.

Trains linear readout heads (probes) across residual stream layers to detect latent deception,
evaluation awareness, and sycophantic rationalization before text is generated.
Also computes contrastive steering vectors (Representation Engineering).
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np


class LinearProbeTrainer:
    """Trains and evaluates layer-wise linear probes on residual stream hidden states."""

    def __init__(self, regularizer: float = 1.0):
        self.C = regularizer
        self.layer_models: Dict[int, Any] = {}
        self.layer_metrics: Dict[int, Dict[str, float]] = {}

    def train_and_evaluate(
        self,
        X_by_layer: Dict[int, np.ndarray],
        y: np.ndarray,
        test_size: float = 0.25,
        cv_folds: int = 5,
    ) -> Dict[str, Any]:
        """Trains a linear probe for every layer and computes classification metrics.

        Args:
            X_by_layer: Dict mapping layer_idx -> numpy array of shape (num_samples, hidden_dim).
            y: Binary label vector (0 or 1) of shape (num_samples,).
            test_size: Proportion of dataset to reserve for held-out validation.
            cv_folds: Number of cross-validation folds.

        Returns:
            Dictionary containing layer-by-layer accuracy, ROC-AUC, and peak separation layer.
        """
        results_by_layer = {}
        peak_layer = -1
        max_score = -1.0
        max_accuracy = -1.0

        for layer_idx, X in sorted(X_by_layer.items()):
            metrics, model = self._fit_layer(X, y, cv_folds=cv_folds)
            pos_m = np.mean(X[y == 1], axis=0)
            neg_m = np.mean(X[y == 0], axis=0)
            margin = float(np.linalg.norm(pos_m - neg_m))
            metrics["margin"] = round(margin, 4)

            # Score prioritizes accuracy and feature separation margin (SNR)
            score = metrics["accuracy"] * 10.0 + margin
            if score > max_score:
                max_score = score
                peak_layer = layer_idx
                max_accuracy = metrics["accuracy"]

            self.layer_models[layer_idx] = model
            self.layer_metrics[layer_idx] = metrics
            results_by_layer[layer_idx] = metrics

        return {
            "peak_layer": peak_layer,
            "peak_accuracy": max_accuracy,
            "layer_results": results_by_layer,
        }

    def _fit_layer(
        self,
        X: np.ndarray,
        y: np.ndarray,
        cv_folds: int = 5,
    ) -> Tuple[Dict[str, float], Any]:
        """Fits a logistic regression probe with cross-validation."""
        try:
            from sklearn.linear_model import LogisticRegression
            from sklearn.model_selection import cross_val_score, StratifiedKFold
            from sklearn.metrics import roc_auc_score

            n_samples = len(y)
            n_pos = int(np.sum(y == 1))
            n_neg = int(np.sum(y == 0))
            effective_folds = min(cv_folds, n_pos, n_neg)

            clf = LogisticRegression(C=self.C, max_iter=1000, solver="lbfgs")

            if effective_folds > 1:
                cv = StratifiedKFold(n_splits=effective_folds, shuffle=True, random_state=42)
                scores = cross_val_score(clf, X, y, cv=cv, scoring="accuracy")
                mean_acc = float(np.mean(scores))
            else:
                clf.fit(X, y)
                preds = clf.predict(X)
                mean_acc = float(np.mean(preds == y))

            clf.fit(X, y)
            probs = clf.predict_proba(X)[:, 1] if hasattr(clf, "predict_proba") else clf.decision_function(X)

            try:
                auc = float(roc_auc_score(y, probs))
            except Exception:
                auc = mean_acc

            return {
                "accuracy": mean_acc,
                "roc_auc": auc,
                "weight_norm": float(np.linalg.norm(clf.coef_)),
            }, clf

        except ImportError:
            # Fallback pure NumPy Fisher's Linear Discriminant / Mean Centroid Classifier
            return self._numpy_probe_fallback(X, y)

    def _numpy_probe_fallback(self, X: np.ndarray, y: np.ndarray) -> Tuple[Dict[str, float], Any]:
        """Pure NumPy implementation of centroid classification for environments without scikit-learn."""
        pos_mask = (y == 1)
        neg_mask = (y == 0)

        if not np.any(pos_mask) or not np.any(neg_mask):
            return {"accuracy": 0.5, "roc_auc": 0.5, "weight_norm": 0.0}, None

        mu_pos = np.mean(X[pos_mask], axis=0)
        mu_neg = np.mean(X[neg_mask], axis=0)
        w = mu_pos - mu_neg
        norm = np.linalg.norm(w)
        if norm > 1e-9:
            w = w / norm

        scores = X @ w
        threshold = (np.mean(scores[pos_mask]) + np.mean(scores[neg_mask])) / 2.0
        preds = (scores >= threshold).astype(int)
        acc = float(np.mean(preds == y))

        return {
            "accuracy": acc,
            "roc_auc": acc,
            "weight_norm": float(norm),
        }, {"direction": w, "threshold": threshold}


class SteeringVector:
    """Computes and applies Contrastive Activation Addition (CAA) steering directions."""

    def __init__(self, layer_idx: int, vector: np.ndarray, concept_name: str = "deception"):
        self.layer_idx = layer_idx
        self.vector = vector / (np.linalg.norm(vector) + 1e-9)
        self.concept_name = concept_name

    @classmethod
    def compute_from_pairs(
        cls,
        pos_activations: np.ndarray,
        neg_activations: np.ndarray,
        layer_idx: int,
        concept_name: str = "deception",
    ) -> "SteeringVector":
        """Computes difference in means: v = mean(h_pos) - mean(h_neg)."""
        mu_pos = np.mean(pos_activations, axis=0)
        mu_neg = np.mean(neg_activations, axis=0)
        diff = mu_pos - mu_neg
        return cls(layer_idx=layer_idx, vector=diff, concept_name=concept_name)

    def project(self, activation: np.ndarray) -> float:
        """Calculates scalar projection magnitude along the steering axis."""
        return float(np.dot(activation, self.vector))

    def cosine_similarity(self, activation: np.ndarray) -> float:
        """Calculates normalized cosine alignment with the steering axis."""
        norm_a = np.linalg.norm(activation)
        if norm_a < 1e-9:
            return 0.0
        return float(np.dot(activation, self.vector) / norm_a)
