
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

import numpy as np
import pandas as pd

from features_stage1 import extract_stage1_matrix
from features_stage2 import extract_stage2_features
from sklearn.base import BaseEstimator
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.covariance import LedoitWolf
from features.stage2 import Stage2Extractor
from features.stage3 import build_graph_features_nodeidx
from sklearn.model_selection import StratifiedKFold

try:
    import lightgbm as lgb
    HAS_LGB = True
except Exception:
    HAS_LGB = False
    from sklearn.ensemble import HistGradientBoostingClassifier


# -----------------------------
# Utility: math helpers
# -----------------------------

def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))

def logit(p: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    p = np.clip(p, eps, 1 - eps)
    return np.log(p / (1 - p))

def entropy_from_p(p: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    p = np.clip(p, eps, 1 - eps)
    return -(p * np.log(p) + (1 - p) * np.log(1 - p))

# -----------------------------
# Novelty: Mahalanobis distance
# -----------------------------

class MahalanobisNovelty:
    """
    Simple, thesis-friendly novelty score:
      n(x) = sqrt( (x-mu)^T Sigma^{-1} (x-mu) )
    Uses LedoitWolf shrinkage covariance for stability.
    """
    def __init__(self):
        self.mu_: Optional[np.ndarray] = None
        self.prec_: Optional[np.ndarray] = None  # inverse covariance

    def fit(self, X: np.ndarray) -> "MahalanobisNovelty":
        X = np.asarray(X, dtype=np.float64)
        self.mu_ = X.mean(axis=0)
        cov = LedoitWolf().fit(X).covariance_
        self.prec_ = np.linalg.inv(cov)
        return self

    def score(self, X: np.ndarray) -> np.ndarray:
        if self.mu_ is None or self.prec_ is None:
            raise RuntimeError("Novelty model not fitted.")
        X = np.asarray(X, dtype=np.float64)
        d = X - self.mu_
        # Mahalanobis squared distance
        m2 = np.einsum("ij,jk,ik->i", d, self.prec_, d)
        return np.sqrt(np.maximum(m2, 0.0))


# -----------------------------
# Feature extraction
# -----------------------------

@dataclass
class FeatureConfig:
    # Stage 1 numeric columns (edit to match your dataset)
    stage1_numeric_cols: List[str]

    # Stage 2 text settings
    max_messages_per_account: int = 50
    max_chars_per_message: int = 500


# ---- Stage 2: text embedder (recommended: sentence-transformers) ----

class TextEmbedder:
    """
    Wraps sentence-transformers so you can swap models easily.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", device: Optional[str] = None):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name, device=device)

    def encode(self, texts: List[str], batch_size: int = 64) -> np.ndarray:
        emb = self.model.encode(texts, batch_size=batch_size, show_progress_bar=False, normalize_embeddings=True)
        return np.asarray(emb, dtype=np.float32)


def simple_linguistic_features(text: str) -> np.ndarray:
    """
    Cheap linguistic features you can expand:
    - length
    - unique token ratio
    - punctuation ratio
    """
    if not text:
        return np.zeros(4, dtype=np.float32)
    s = text.strip()
    length = len(s)
    tokens = [t for t in s.split() if t]
    uniq = len(set(tokens))
    uniq_ratio = uniq / max(len(tokens), 1)
    punct = sum(1 for c in s if c in ".,!?;:")
    punct_ratio = punct / max(length, 1)
    digit = sum(1 for c in s if c.isdigit())
    digit_ratio = digit / max(length, 1)
    return np.array([length, uniq_ratio, punct_ratio, digit_ratio], dtype=np.float32)


# ---- AMR utilities (you plug in a real AMR parser) ----

def amr_linearize_stub(text: str) -> str:
    """
    Replace this with actual AMR parsing + linearization.
    For now it's a stub that returns the original text.
    """
    return text


def extract_amr_embeddings_for_accounts(
    df: pd.DataFrame,
    cfg: FeatureConfig,
    embedder: TextEmbedder,
) -> np.ndarray:
    from cascade_pipeline import infer_dataset

    dataset = infer_dataset(df, cfg)
    max_chars = cfg.max_chars_per_message if cfg is not None else 500
    return Stage2Extractor(dataset).extract_amr(df, embedder, max_chars=max_chars)


# -----------------------------
# Stage Models
# -----------------------------

@dataclass
class StageThresholds:
    # Stage 1 early exits
    s1_bot: float = 0.98
    s1_human: float = 0.02
    n1_max_for_exit: float = 3.0  # novelty threshold (tune)

    # Stage 2 AMR gate
    s2a_bot: float = 0.95
    s2a_human: float = 0.05
    n2_trigger: float = 3.0
    disagreement_trigger: float = 4.0  # on logits

    # Stage 12 -> Stage 3 routing
    s12_bot: float = 0.98
    s12_human: float = 0.02
    novelty_force_stage3: float = 3.5


class Stage1MetadataModel:
    def __init__(self, use_isotonic: bool = False, random_state: int = 42):
        self.random_state = random_state
        self.use_isotonic = use_isotonic
        self.model: Optional[BaseEstimator] = None
        self.cal: Optional[CalibratedClassifierCV] = None
        self.novelty = MahalanobisNovelty()

    def fit(self, X: np.ndarray, y: np.ndarray) -> "Stage1MetadataModel":
        if HAS_LGB:
            base = lgb.LGBMClassifier(
                n_estimators=400,
                learning_rate=0.05,
                num_leaves=31,
                subsample=0.9,
                colsample_bytree=0.9,
                random_state=self.random_state,
            )
        else:
            base = HistGradientBoostingClassifier(random_state=self.random_state)

        self.model = base.fit(X, y)

        method = "isotonic" if self.use_isotonic else "sigmoid"
        self.cal = CalibratedClassifierCV(self.model, method=method, cv=3)
        self.cal.fit(X, y)

        self.novelty.fit(X)
        return self

    def predict(self, X: np.ndarray) -> Dict[str, np.ndarray]:
        if self.cal is None:
            raise RuntimeError("Stage1 not fitted.")
        p = self.cal.predict_proba(X)[:, 1]
        u = entropy_from_p(p)
        n = self.novelty.score(X)
        return {"p1": p, "u1": u, "n1": n, "z1": logit(p)}


class Stage2BaseContentModel:
    """
    Stage 2a: cheap content/temporal/linguistics -> calibrated prob + novelty on features.
    """
    def __init__(self, use_isotonic: bool = False, random_state: int = 42):
        self.random_state = random_state
        self.use_isotonic = use_isotonic
        self.model: Optional[BaseEstimator] = None
        self.cal: Optional[CalibratedClassifierCV] = None
        self.novelty = MahalanobisNovelty()

    def fit(self, X: np.ndarray, y: np.ndarray) -> "Stage2BaseContentModel":
        if HAS_LGB:
            base = lgb.LGBMClassifier(
                n_estimators=600,
                learning_rate=0.05,
                num_leaves=63,
                subsample=0.9,
                colsample_bytree=0.9,
                random_state=self.random_state,
            )
        else:
            base = HistGradientBoostingClassifier(random_state=self.random_state)

        self.model = base.fit(X, y)

        method = "isotonic" if self.use_isotonic else "sigmoid"
        self.cal = CalibratedClassifierCV(self.model, method=method, cv=3)
        self.cal.fit(X, y)

        self.novelty.fit(X)
        return self

    def predict(self, X: np.ndarray) -> Dict[str, np.ndarray]:
        if self.cal is None:
            raise RuntimeError("Stage2a not fitted.")
        p = self.cal.predict_proba(X)[:, 1]
        u = entropy_from_p(p)
        n = self.novelty.score(X)
        z = logit(p)
        return {"p2a": p, "u2": u, "n2": n, "z2a": z}


class AMRDeltaRefiner:
    """
    Option C: cheap base logit z2a + learned delta(amr_emb) -> refined logit z2.

    Trains a linear delta via logistic loss with a fixed offset z_base:
      z = z_base + w^T h + b
      p = sigmoid(z)
    """
    def __init__(self, lr: float = 0.1, epochs: int = 300, l2: float = 1e-3, random_state: int = 42):
        self.lr = lr
        self.epochs = epochs
        self.l2 = l2
        self.random_state = random_state
        self.w: Optional[np.ndarray] = None
        self.b: float = 0.0

    def fit(self, h_amr: np.ndarray, z_base: np.ndarray, y: np.ndarray) -> "AMRDeltaRefiner":
        rng = np.random.default_rng(self.random_state)
        h = np.asarray(h_amr, dtype=np.float64)
        z0 = np.asarray(z_base, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)

        n, d = h.shape
        self.w = rng.normal(scale=0.01, size=(d,))
        self.b = 0.0

        for _ in range(self.epochs):
            z = z0 + h @ self.w + self.b
            p = sigmoid(z)
            # gradients for logistic loss
            grad_z = (p - y)  # dL/dz
            grad_w = (h.T @ grad_z) / n + self.l2 * self.w
            grad_b = float(np.mean(grad_z))
            self.w -= self.lr * grad_w
            self.b -= self.lr * grad_b

        return self

    def delta(self, h_amr: np.ndarray) -> np.ndarray:
        if self.w is None:
            raise RuntimeError("AMRDeltaRefiner not fitted.")
        h = np.asarray(h_amr, dtype=np.float64)
        return (h @ self.w + self.b).astype(np.float64)

    def refine(self, z_base: np.ndarray, h_amr: np.ndarray) -> np.ndarray:
        return np.asarray(z_base, dtype=np.float64) + self.delta(h_amr)


class Stage3StructuralModel:
    """
    Stage 3: engineered structural features -> calibrated prob + novelty.
    """
    def __init__(self, use_isotonic: bool = False, random_state: int = 42):
        self.random_state = random_state
        self.use_isotonic = use_isotonic
        self.model: Optional[BaseEstimator] = None
        self.cal: Optional[CalibratedClassifierCV] = None
        self.novelty = MahalanobisNovelty()

    def fit(self, X: np.ndarray, y: np.ndarray) -> "Stage3StructuralModel":
        if HAS_LGB:
            base = lgb.LGBMClassifier(
                n_estimators=500,
                learning_rate=0.05,
                num_leaves=63,
                subsample=0.9,
                colsample_bytree=0.9,
                random_state=self.random_state,
            )
        else:
            base = HistGradientBoostingClassifier(random_state=self.random_state)

        self.model = base.fit(X, y)

        method = "isotonic" if self.use_isotonic else "sigmoid"
        self.cal = CalibratedClassifierCV(self.model, method=method, cv=3)
        self.cal.fit(X, y)

        self.novelty.fit(X)
        return self

    def predict(self, X: np.ndarray) -> Dict[str, np.ndarray]:
        if self.cal is None:
            raise RuntimeError("Stage3 not fitted.")
        p = self.cal.predict_proba(X)[:, 1]
        u = entropy_from_p(p)
        n = self.novelty.score(X)
        return {"p3": p, "u3": u, "n3": n, "z3": logit(p)}


# -----------------------------
# Meta models (logistic regression)
# -----------------------------

def train_meta12(X_meta: pd.DataFrame, y: np.ndarray) -> LogisticRegression:
    """
    X_meta should include columns like:
      z1, z2, n1, n2, u1, u2, amr_used, disagreement
    """
    model = LogisticRegression(max_iter=2000, class_weight="balanced")
    model.fit(X_meta.to_numpy(dtype=np.float32), y)
    return model

def train_meta123(X_meta: pd.DataFrame, y: np.ndarray) -> LogisticRegression:
    model = LogisticRegression(max_iter=2000, class_weight="balanced")
    model.fit(X_meta.to_numpy(dtype=np.float32), y)
    return model


# -----------------------------
# Routing logic
# -----------------------------

def gate_amr(
    p2a: np.ndarray, n2: np.ndarray, z1: np.ndarray, z2a: np.ndarray,
    th: StageThresholds
) -> np.ndarray:
    """
    Return boolean mask: compute AMR if uncertain OR novel OR disagreement.
    """
    uncertain = (p2a > th.s2a_human) & (p2a < th.s2a_bot)
    novel = n2 >= th.n2_trigger
    disagree = np.abs(z1 - z2a) >= th.disagreement_trigger
    return uncertain | novel | disagree

def gate_stage3(
    p12: np.ndarray, n1: np.ndarray, n2: np.ndarray, th: StageThresholds
) -> np.ndarray:
    """
    Compute Stage3 if uncertain in combined score OR novelty is high.
    """
    uncertain = (p12 > th.s12_human) & (p12 < th.s12_bot)
    novel = (np.maximum(n1, n2) >= th.novelty_force_stage3)
    return uncertain | novel


# -----------------------------
# OOF stacking for meta12 on S2
# -----------------------------

def build_meta12_table(
    stage1_out: Dict[str, np.ndarray],
    stage2_out: Dict[str, np.ndarray],
    amr_used: np.ndarray
) -> pd.DataFrame:
    z1 = stage1_out["z1"]
    z2 = stage2_out["z2"]  # final refined or base
    u1 = stage1_out["u1"]
    u2 = stage2_out["u2"]
    n1 = stage1_out["n1"]
    n2 = stage2_out["n2"]
    disagree = np.abs(z1 - z2)

    X = pd.DataFrame({
        "z1": z1,
        "z2": z2,
        "u1": u1,
        "u2": u2,
        "n1": n1,
        "n2": n2,
        "amr_used": amr_used.astype(np.float32),
        "disagree": disagree,
    })
    return X


def oof_meta12_predictions(
    X_meta12: pd.DataFrame, y: np.ndarray, n_splits: int = 5, random_state: int = 42
) -> np.ndarray:
    """
    Create out-of-fold p12 predictions on S2 so meta123 training is clean.
    """
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    p12_oof = np.zeros(len(y), dtype=np.float64)

    for tr_idx, va_idx in skf.split(X_meta12, y):
        m = train_meta12(X_meta12.iloc[tr_idx], y[tr_idx])
        p12_oof[va_idx] = m.predict_proba(X_meta12.iloc[va_idx].to_numpy(dtype=np.float32))[:, 1]
    return p12_oof


# -----------------------------
# Full training routine (S1/S2/S3)
# -----------------------------

@dataclass
class TrainedSystem:
    cfg: FeatureConfig
    th: StageThresholds
    embedder: TextEmbedder

    stage1: Stage1MetadataModel
    stage2a: Stage2BaseContentModel
    amr_refiner: Optional[AMRDeltaRefiner]
    meta12: LogisticRegression

    stage3: Stage3StructuralModel
    meta123: LogisticRegression


def train_system(
    S1: pd.DataFrame,
    S2: pd.DataFrame,
    edges_S1: pd.DataFrame,
    edges_S2: pd.DataFrame,
    cfg: FeatureConfig,
    th: StageThresholds,
    random_state: int = 42,
    nodes_total: Optional[int] = None,
    embedder: Optional[TextEmbedder] = None,
) -> TrainedSystem:
    from cascade_pipeline import CascadePipeline, infer_dataset

    dataset = infer_dataset(S1, cfg)
    pipeline = CascadePipeline(dataset=dataset, cfg=cfg, random_state=random_state, embedder=embedder)
    return pipeline.fit(
        S1,
        S2,
        edges_S1,
        edges_S2,
        th,
        nodes_total=nodes_total,
        embedder=embedder,
    )


def predict_system(
    sys: TrainedSystem,
    df: pd.DataFrame,
    edges_df: pd.DataFrame,
    nodes_total: Optional[int] = None,
) -> pd.DataFrame:
    from cascade_pipeline import CascadePipeline, infer_dataset

    dataset = infer_dataset(df, sys.cfg)
    pipeline = CascadePipeline(dataset=dataset, cfg=sys.cfg, embedder=sys.embedder)
    return pipeline.predict(sys, df, edges_df, nodes_total=nodes_total)
