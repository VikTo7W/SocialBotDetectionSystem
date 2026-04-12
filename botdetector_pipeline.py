
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple, List

import numpy as np
import pandas as pd

from sklearn.base import BaseEstimator
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import StratifiedKFold
from sklearn.covariance import LedoitWolf
from features_stage1 import extract_stage1_matrix
from features_stage2 import extract_stage2_features

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
    text_field: str = "profile"
) -> np.ndarray:
    """
    Minimal AMR representation: linearize AMR of a chosen field or concatenated text.
    In a real system, you'd parse multiple messages and/or aggregate.
    """
    amr_texts = []
    for _, r in df.iterrows():
        # You can do: concatenate a few representative messages; here keep it simple
        base = str(r.get(text_field) or "").strip()
        if base.lower() == "nan":
            base = ""
        amr = amr_linearize_stub(base)
        amr_texts.append(amr if amr else "")
    emb = embedder.encode(amr_texts)
    return emb.astype(np.float32)


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
# Structural feature extraction
# -----------------------------

def build_graph_features_nodeidx(
    accounts_df: pd.DataFrame,
    edges_df: pd.DataFrame,
    num_nodes_total: int,
    n_types: int = 3
) -> np.ndarray:
    node_ids = accounts_df["node_idx"].to_numpy(dtype=np.int32)

    src = edges_df["src"].to_numpy(dtype=np.int32)
    dst = edges_df["dst"].to_numpy(dtype=np.int32)
    w   = edges_df["weight"].to_numpy(dtype=np.float32)
    et  = edges_df["etype"].to_numpy(dtype=np.int8)

    # Global degrees
    in_deg  = np.zeros(num_nodes_total, dtype=np.float32)
    out_deg = np.zeros(num_nodes_total, dtype=np.float32)
    in_w    = np.zeros(num_nodes_total, dtype=np.float32)
    out_w   = np.zeros(num_nodes_total, dtype=np.float32)

    np.add.at(out_deg, src, 1.0)
    np.add.at(in_deg,  dst, 1.0)
    np.add.at(out_w,   src, w)
    np.add.at(in_w,    dst, w)

    feats = [in_deg, out_deg, in_deg + out_deg, in_w, out_w, in_w + out_w]

    # Per-type degrees/weights
    for t in range(n_types):
        mask = (et == t)
        in_d_t  = np.zeros(num_nodes_total, dtype=np.float32)
        out_d_t = np.zeros(num_nodes_total, dtype=np.float32)
        in_w_t  = np.zeros(num_nodes_total, dtype=np.float32)
        out_w_t = np.zeros(num_nodes_total, dtype=np.float32)

        np.add.at(out_d_t, src[mask], 1.0)
        np.add.at(in_d_t,  dst[mask], 1.0)
        np.add.at(out_w_t, src[mask], w[mask])
        np.add.at(in_w_t,  dst[mask], w[mask])

        feats.extend([in_d_t, out_d_t, in_w_t, out_w_t])

    X_all = np.stack(feats, axis=1)          # [num_nodes_total, D]
    return X_all[node_ids]                   # [len(accounts_df), D]


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
    amr_refiner: AMRDeltaRefiner
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
) -> TrainedSystem:
    """
    Train stage models on S1.
    Train meta12/meta123 on S2 using OOF meta12 predictions.
    """
    embedder = TextEmbedder()

    # ---- Stage 1 training on S1
    print("Stage 1 training on S1")
    X1_tr = extract_stage1_matrix(S1)
    y1_tr = S1["label"].to_numpy(dtype=np.int64)
    stage1 = Stage1MetadataModel(use_isotonic=False, random_state=random_state).fit(X1_tr, y1_tr)

    # ---- Stage 2a training on S1
    print("Stage 2a training on S1")
    X2_tr = extract_stage2_features(S1, embedder)
    stage2a = Stage2BaseContentModel(use_isotonic=False, random_state=random_state).fit(X2_tr, y1_tr)

    # ---- Build Stage outputs on S1 to train AMR refiner (you can restrict to gated subset if you want)
    out1_S1 = stage1.predict(X1_tr)
    out2a_S1 = stage2a.predict(X2_tr)

    # AMR embeddings for S1
    H_amr_S1 = extract_amr_embeddings_for_accounts(S1, cfg, embedder, text_field="profile")
    z2a_S1 = out2a_S1["z2a"]

    # Train AMR delta refiner with offset z2a
    print("Train AMR delta refiner with offset z2a")
    amr_refiner = AMRDeltaRefiner(lr=0.05, epochs=400, l2=1e-3, random_state=random_state)
    amr_refiner.fit(H_amr_S1, z2a_S1, y1_tr)

    # ---- Stage 3 training on S1
    print("Stage 3 training on S1")
    X3_tr = build_graph_features_nodeidx(S1, edges_S1, nodes_total)
    stage3 = Stage3StructuralModel(use_isotonic=False, random_state=random_state).fit(X3_tr, y1_tr)

    # ---- Now build meta training data on S2
    y2 = S2["label"].to_numpy(dtype=np.int64)

    X1_S2 = extract_stage1_matrix(S2)
    out1_S2 = stage1.predict(X1_S2)

    X2_S2 = extract_stage2_features(S2, embedder)
    out2a_S2 = stage2a.predict(X2_S2)

    # AMR gating based on Stage2a uncertainty/novelty/disagreement
    amr_mask = gate_amr(out2a_S2["p2a"], out2a_S2["n2"], out1_S2["z1"], out2a_S2["z2a"], th)

    # Compute AMR embeddings only for routed accounts
    H_amr_S2 = np.zeros((len(S2), H_amr_S1.shape[1]), dtype=np.float32)
    if amr_mask.any():
        H_amr_S2[amr_mask] = extract_amr_embeddings_for_accounts(S2.loc[amr_mask], cfg, embedder, text_field="profile")

    # Refine logits where AMR used
    z2 = out2a_S2["z2a"].astype(np.float64).copy()
    if amr_mask.any():
        z2[amr_mask] = amr_refiner.refine(z2[amr_mask], H_amr_S2[amr_mask])

    p2 = sigmoid(z2)
    out2_S2 = {
        "z2": z2,
        "p2": p2,
        "u2": entropy_from_p(p2),
        "n2": out2a_S2["n2"],  # novelty from base features; you can extend with AMR novelty if you want
    }

    X_meta12_S2 = build_meta12_table(out1_S2, out2_S2, amr_used=amr_mask.astype(np.float32))

    # OOF p12 predictions for routing Stage3 on S2
    p12_oof = oof_meta12_predictions(X_meta12_S2, y2, n_splits=5, random_state=random_state)

    # Train final meta12 on all S2 (after you got OOF for routing)
    print("Train final meta12 on all S2 (after you got OOF for routing)")
    meta12 = train_meta12(X_meta12_S2, y2)

    # ---- Stage 3 routing on S2 using OOF p12 + novelty safeguards
    stage3_mask = gate_stage3(p12_oof, out1_S2["n1"], out2_S2["n2"], th)

    X3_S2 = build_graph_features_nodeidx(S2, edges_S2, nodes_total)
    out3_S2 = {"p3": np.full(len(S2), 0.5, dtype=np.float64),
               "z3": np.zeros(len(S2), dtype=np.float64),
               "n3": np.zeros(len(S2), dtype=np.float64)}

    if stage3_mask.any():
        pred3 = stage3.predict(X3_S2[stage3_mask])
        out3_S2["p3"][stage3_mask] = pred3["p3"]
        out3_S2["z3"][stage3_mask] = pred3["z3"]
        out3_S2["n3"][stage3_mask] = pred3["n3"]

    # ---- meta123 training table (on S2)
    X_meta123_S2 = pd.DataFrame({
        "z12": logit(p12_oof),
        "z3": out3_S2["z3"],
        "stage3_used": stage3_mask.astype(np.float32),
        "n1": out1_S2["n1"],
        "n2": out2_S2["n2"],
        "n3": out3_S2["n3"],
    })

    print("Train final meta123 on gated S2 (after you got OOF for routing)")
    meta123 = train_meta123(X_meta123_S2, y2)

    return TrainedSystem(
        cfg=cfg, th=th, embedder=embedder,
        stage1=stage1, stage2a=stage2a, amr_refiner=amr_refiner, meta12=meta12,
        stage3=stage3, meta123=meta123
    )


def predict_system(
    sys: TrainedSystem,
    df: pd.DataFrame,
    edges_df: pd.DataFrame,
    nodes_total: Optional[int] = None,
) -> pd.DataFrame:
    """
    Run full inference on a dataset (e.g., S3).
    Returns per-account probabilities and flags.
    """
    cfg, th = sys.cfg, sys.th

    # Stage 1
    X1 = extract_stage1_matrix(df)
    out1 = sys.stage1.predict(X1)

    # Stage 2a
    X2 = extract_stage2_features(df, sys.embedder)
    out2a = sys.stage2a.predict(X2)

    # AMR gate
    amr_mask = gate_amr(out2a["p2a"], out2a["n2"], out1["z1"], out2a["z2a"], th)

    # AMR embeddings for gated
    H_amr = np.zeros((len(df), 384), dtype=np.float32)  # if MiniLM; adjust if needed
    if amr_mask.any():
        H_amr[amr_mask] = extract_amr_embeddings_for_accounts(df.loc[amr_mask], cfg, sys.embedder, text_field="profile")

    # Refine
    z2 = out2a["z2a"].astype(np.float64).copy()
    if amr_mask.any():
        z2[amr_mask] = sys.amr_refiner.refine(z2[amr_mask], H_amr[amr_mask])
    p2 = sigmoid(z2)
    out2 = {
        "z2": z2, "p2": p2, "u2": entropy_from_p(p2), "n2": out2a["n2"]
    }

    # Meta12
    X_meta12 = build_meta12_table(out1, out2, amr_used=amr_mask.astype(np.float32))
    p12 = sys.meta12.predict_proba(X_meta12.to_numpy(dtype=np.float32))[:, 1]

    # Stage 3 gate
    stage3_mask = gate_stage3(p12, out1["n1"], out2["n2"], th)

    # Stage 3
    X3 = build_graph_features_nodeidx(df, edges_df, nodes_total)
    p3 = np.full(len(df), 0.5, dtype=np.float64)
    z3 = np.zeros(len(df), dtype=np.float64)
    n3 = np.zeros(len(df), dtype=np.float64)

    if stage3_mask.any():
        out3 = sys.stage3.predict(X3[stage3_mask])
        p3[stage3_mask] = out3["p3"]
        z3[stage3_mask] = out3["z3"]
        n3[stage3_mask] = out3["n3"]

    # Meta123
    X_meta123 = pd.DataFrame({
        "z12": logit(p12),
        "z3": z3,
        "stage3_used": stage3_mask.astype(np.float32),
        "n1": out1["n1"],
        "n2": out2["n2"],
        "n3": n3,
    })
    p_final = sys.meta123.predict_proba(X_meta123.to_numpy(dtype=np.float32))[:, 1]

    return pd.DataFrame({
        "account_id": df["account_id"].astype(str).values,
        "p1": out1["p1"],
        "n1": out1["n1"],
        "p2": p2,
        "n2": out2["n2"],
        "amr_used": amr_mask.astype(int),
        "p12": p12,
        "stage3_used": stage3_mask.astype(int),
        "p3": p3,
        "n3": n3,
        "p_final": p_final,
    })