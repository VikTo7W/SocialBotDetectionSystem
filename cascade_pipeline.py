"""
cascade_pipeline.py -- maintained orchestration surface for the bot detection cascade.

This module owns:
  - all stage model definitions (Stage1MetadataModel, Stage2BaseContentModel,
    Stage3StructuralModel, AMRDeltaRefiner)
  - the training contract types (FeatureConfig, StageThresholds, TrainedSystem)
  - math / routing helpers (sigmoid, logit, entropy_from_p, gate_amr, gate_stage3,
    build_meta12_table, oof_meta12_predictions, train_meta12, train_meta123)
  - CascadePipeline -- the end-to-end fit/predict orchestrator

botdetector_pipeline.py is a compatibility shim that re-exports from this module and
keeps legacy compatibility wrappers (train_system, predict_system) for callers that
have not yet been updated.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, List, Optional, Any

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.calibration import CalibratedClassifierCV
from sklearn.covariance import LedoitWolf
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold

try:
    import lightgbm as lgb
    HAS_LGB = True
except Exception:
    HAS_LGB = False
    from sklearn.ensemble import HistGradientBoostingClassifier

from features.stage1 import STAGE1_TWITTER_COLUMNS, Stage1Extractor
from features.stage2 import Stage2Extractor
from features.stage3 import Stage3Extractor


# ---------------------------------------------------------------------------
# Math helpers
# ---------------------------------------------------------------------------

def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def logit(p: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    p = np.clip(p, eps, 1 - eps)
    return np.log(p / (1 - p))


def entropy_from_p(p: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    p = np.clip(p, eps, 1 - eps)
    return -(p * np.log(p) + (1 - p) * np.log(1 - p))


# ---------------------------------------------------------------------------
# Novelty: Mahalanobis distance
# ---------------------------------------------------------------------------

class MahalanobisNovelty:
    """
    Novelty score via Mahalanobis distance:
      n(x) = sqrt( (x-mu)^T Sigma^{-1} (x-mu) )
    Uses LedoitWolf shrinkage covariance for stability.
    """
    def __init__(self):
        self.mu_: Optional[np.ndarray] = None
        self.prec_: Optional[np.ndarray] = None

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
        m2 = np.einsum("ij,jk,ik->i", d, self.prec_, d)
        return np.sqrt(np.maximum(m2, 0.0))


# ---------------------------------------------------------------------------
# Contract types
# ---------------------------------------------------------------------------

@dataclass
class FeatureConfig:
    """Configuration for feature extraction across both dataset types."""
    # stage 1 numeric columns (dataset-specific)
    stage1_numeric_cols: List[str]

    # stage 2 text settings
    max_messages_per_account: int = 50
    max_chars_per_message: int = 500


@dataclass
class StageThresholds:
    # stage 1 early exits
    s1_bot: float = 0.98
    s1_human: float = 0.02
    n1_max_for_exit: float = 3.0

    # stage 2 AMR gate
    s2a_bot: float = 0.95
    s2a_human: float = 0.05
    n2_trigger: float = 3.0
    disagreement_trigger: float = 4.0

    # stage 12 -> stage 3 routing
    s12_bot: float = 0.98
    s12_human: float = 0.02
    novelty_force_stage3: float = 3.5


class TextEmbedder:
    """Wraps sentence-transformers so you can swap models easily."""
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", device: Optional[str] = None):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name, device=device)

    def encode(self, texts: List[str], batch_size: int = 64) -> np.ndarray:
        emb = self.model.encode(
            texts, batch_size=batch_size, show_progress_bar=False, normalize_embeddings=True
        )
        return np.asarray(emb, dtype=np.float32)


@dataclass
class TrainedSystem:
    cfg: FeatureConfig
    th: StageThresholds
    embedder: Any  # TextEmbedder or FakeEmbedder

    stage1: "Stage1MetadataModel"
    stage2a: "Stage2BaseContentModel"
    amr_refiner: Optional["AMRDeltaRefiner"]
    meta12: LogisticRegression

    stage3: "Stage3StructuralModel"
    meta123: LogisticRegression


# ---------------------------------------------------------------------------
# Stage models
# ---------------------------------------------------------------------------

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
    """Stage 2a: content/temporal/linguistics -> calibrated prob + novelty on features."""
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
    Stage 2b: base logit z2a + learned delta(amr_emb) -> refined logit z2.

    Trains a linear delta via logistic loss with a fixed offset z_base:
      z = z_base + w^T h + b
      p = sigmoid(z)
    """
    def __init__(
        self,
        lr: float = 0.1,
        epochs: int = 300,
        l2: float = 1e-3,
        random_state: int = 42,
    ):
        self.lr = lr
        self.epochs = epochs
        self.l2 = l2
        self.random_state = random_state
        self.w: Optional[np.ndarray] = None
        self.b: float = 0.0

    def fit(
        self, h_amr: np.ndarray, z_base: np.ndarray, y: np.ndarray
    ) -> "AMRDeltaRefiner":
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
            grad_z = p - y
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
    """Stage 3: engineered structural features -> calibrated prob + novelty."""
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


# ---------------------------------------------------------------------------
# Routing logic
# ---------------------------------------------------------------------------

def gate_amr(
    p2a: np.ndarray,
    n2: np.ndarray,
    z1: np.ndarray,
    z2a: np.ndarray,
    th: StageThresholds,
) -> np.ndarray:
    """Return boolean mask: activate AMR if uncertain OR novel OR disagreement."""
    uncertain = (p2a > th.s2a_human) & (p2a < th.s2a_bot)
    novel = n2 >= th.n2_trigger
    disagree = np.abs(z1 - z2a) >= th.disagreement_trigger
    return uncertain | novel | disagree


def gate_stage3(
    p12: np.ndarray,
    n1: np.ndarray,
    n2: np.ndarray,
    th: StageThresholds,
) -> np.ndarray:
    """Return boolean mask: escalate to Stage 3 if uncertain or novelty is high."""
    uncertain = (p12 > th.s12_human) & (p12 < th.s12_bot)
    novel = np.maximum(n1, n2) >= th.novelty_force_stage3
    return uncertain | novel


# ---------------------------------------------------------------------------
# Meta-model helpers
# ---------------------------------------------------------------------------

def build_meta12_table(
    stage1_out: Dict[str, np.ndarray],
    stage2_out: Dict[str, np.ndarray],
    amr_used: np.ndarray,
) -> pd.DataFrame:
    z1 = stage1_out["z1"]
    z2 = stage2_out["z2"]
    u1 = stage1_out["u1"]
    u2 = stage2_out["u2"]
    n1 = stage1_out["n1"]
    n2 = stage2_out["n2"]
    disagree = np.abs(z1 - z2)
    return pd.DataFrame({
        "z1": z1,
        "z2": z2,
        "u1": u1,
        "u2": u2,
        "n1": n1,
        "n2": n2,
        "amr_used": amr_used.astype(np.float32),
        "disagree": disagree,
    })


def oof_meta12_predictions(
    X_meta12: pd.DataFrame,
    y: np.ndarray,
    n_splits: int = 5,
    random_state: int = 42,
) -> np.ndarray:
    """Out-of-fold p12 predictions on S2 so meta123 training is leakage-free."""
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    p12_oof = np.zeros(len(y), dtype=np.float64)
    for tr_idx, va_idx in skf.split(X_meta12, y):
        m = train_meta12(X_meta12.iloc[tr_idx], y[tr_idx])
        p12_oof[va_idx] = m.predict_proba(
            X_meta12.iloc[va_idx].to_numpy(dtype=np.float32)
        )[:, 1]
    return p12_oof


def train_meta12(X_meta: pd.DataFrame, y: np.ndarray) -> LogisticRegression:
    model = LogisticRegression(max_iter=2000, class_weight="balanced")
    model.fit(X_meta.to_numpy(dtype=np.float32), y)
    return model


def train_meta123(X_meta: pd.DataFrame, y: np.ndarray) -> LogisticRegression:
    model = LogisticRegression(max_iter=2000, class_weight="balanced")
    model.fit(X_meta.to_numpy(dtype=np.float32), y)
    return model


# ---------------------------------------------------------------------------
# Dataset inference
# ---------------------------------------------------------------------------

def infer_dataset(df: pd.DataFrame, cfg: FeatureConfig | None = None) -> str:
    if cfg is not None and list(cfg.stage1_numeric_cols) == list(STAGE1_TWITTER_COLUMNS):
        return "twibot"
    if "screen_name" in df.columns or "domain_list" in df.columns:
        return "twibot"
    return "botsim"


# ---------------------------------------------------------------------------
# CascadePipeline -- the maintained end-to-end orchestrator
# ---------------------------------------------------------------------------

class CascadePipeline:
    def __init__(
        self,
        dataset: str,
        cfg: FeatureConfig | None = None,
        *,
        random_state: int = 42,
        embedder: TextEmbedder | None = None,
    ) -> None:
        if dataset not in {"botsim", "twibot"}:
            raise ValueError(f"unknown dataset: {dataset!r}")
        self.dataset = dataset
        self.random_state = random_state
        self.embedder = embedder
        self.cfg = cfg or self._default_cfg(dataset)
        self.stage1_extractor = Stage1Extractor(dataset)
        self.stage2_extractor = Stage2Extractor(dataset)
        self.stage3_extractor = Stage3Extractor(dataset)

    def fit(
        self,
        S1: pd.DataFrame,
        S2: pd.DataFrame,
        edges_S1: pd.DataFrame,
        edges_S2: pd.DataFrame,
        th: StageThresholds,
        *,
        nodes_total: int | None = None,
        embedder: TextEmbedder | None = None,
    ) -> TrainedSystem:
        embedder = embedder or self.embedder or TextEmbedder()

        X1_tr = self.stage1_extractor.extract(S1)
        y1_tr = S1["label"].to_numpy(dtype=np.int64)
        stage1 = Stage1MetadataModel(use_isotonic=False, random_state=self.random_state).fit(X1_tr, y1_tr)

        X2_tr = self.stage2_extractor.extract(
            S1,
            embedder,
            max_msgs=self.cfg.max_messages_per_account,
            max_chars=self.cfg.max_chars_per_message,
        )
        stage2a = Stage2BaseContentModel(use_isotonic=False, random_state=self.random_state).fit(X2_tr, y1_tr)
        out2a_S1 = stage2a.predict(X2_tr)

        h_amr_S1 = self.stage2_extractor.extract_amr(
            S1,
            embedder,
            max_chars=self.cfg.max_chars_per_message,
        )
        amr_refiner = AMRDeltaRefiner(lr=0.05, epochs=400, l2=1e-3, random_state=self.random_state)
        amr_refiner.fit(h_amr_S1, out2a_S1["z2a"], y1_tr)

        X3_tr = self.stage3_extractor.extract(S1, edges_S1, num_nodes_total=nodes_total)
        stage3 = Stage3StructuralModel(use_isotonic=False, random_state=self.random_state).fit(X3_tr, y1_tr)

        y2 = S2["label"].to_numpy(dtype=np.int64)
        out1_S2 = stage1.predict(self.stage1_extractor.extract(S2))
        X2_S2 = self.stage2_extractor.extract(
            S2,
            embedder,
            max_msgs=self.cfg.max_messages_per_account,
            max_chars=self.cfg.max_chars_per_message,
        )
        out2a_S2 = stage2a.predict(X2_S2)

        amr_mask = gate_amr(out2a_S2["p2a"], out2a_S2["n2"], out1_S2["z1"], out2a_S2["z2a"], th)
        z2 = np.asarray(out2a_S2["z2a"], dtype=np.float64).copy()
        if amr_mask.any():
            h_amr_S2 = self.stage2_extractor.extract_amr(
                S2.loc[amr_mask],
                embedder,
                max_chars=self.cfg.max_chars_per_message,
            )
            z2[amr_mask] = amr_refiner.refine(z2[amr_mask], h_amr_S2)

        p2 = sigmoid(z2)
        out2_S2 = {
            "z2": z2,
            "p2": p2,
            "u2": entropy_from_p(p2),
            "n2": out2a_S2["n2"],
        }
        X_meta12_S2 = build_meta12_table(out1_S2, out2_S2, amr_used=amr_mask.astype(np.float32))
        p12_oof = oof_meta12_predictions(X_meta12_S2, y2, n_splits=5, random_state=self.random_state)
        meta12 = train_meta12(X_meta12_S2, y2)

        stage3_mask = gate_stage3(p12_oof, out1_S2["n1"], out2_S2["n2"], th)
        X3_S2 = self.stage3_extractor.extract(S2, edges_S2, num_nodes_total=nodes_total)
        out3_S2 = {
            "p3": np.full(len(S2), 0.5, dtype=np.float64),
            "z3": np.zeros(len(S2), dtype=np.float64),
            "n3": np.zeros(len(S2), dtype=np.float64),
        }
        if stage3_mask.any():
            pred3 = stage3.predict(X3_S2[stage3_mask])
            out3_S2["p3"][stage3_mask] = pred3["p3"]
            out3_S2["z3"][stage3_mask] = pred3["z3"]
            out3_S2["n3"][stage3_mask] = pred3["n3"]

        X_meta123_S2 = pd.DataFrame(
            {
                "z12": logit(p12_oof),
                "z3": out3_S2["z3"],
                "stage3_used": stage3_mask.astype(np.float32),
                "n1": out1_S2["n1"],
                "n2": out2_S2["n2"],
                "n3": out3_S2["n3"],
            }
        )
        meta123 = train_meta123(X_meta123_S2, y2)

        return TrainedSystem(
            cfg=replace(self.cfg),
            th=replace(th),
            embedder=embedder,
            stage1=stage1,
            stage2a=stage2a,
            amr_refiner=amr_refiner,
            meta12=meta12,
            stage3=stage3,
            meta123=meta123,
        )

    def predict(
        self,
        system: TrainedSystem,
        df: pd.DataFrame,
        edges_df: pd.DataFrame,
        *,
        nodes_total: int | None = None,
    ) -> pd.DataFrame:
        cfg = system.cfg
        th = system.th

        out1 = system.stage1.predict(self.stage1_extractor.extract(df))
        X2 = self.stage2_extractor.extract(
            df,
            system.embedder,
            max_msgs=cfg.max_messages_per_account,
            max_chars=cfg.max_chars_per_message,
        )
        out2a = system.stage2a.predict(X2)

        amr_mask = gate_amr(out2a["p2a"], out2a["n2"], out1["z1"], out2a["z2a"], th)
        z2 = np.asarray(out2a["z2a"], dtype=np.float64).copy()
        if amr_mask.any():
            h_amr = self.stage2_extractor.extract_amr(
                df.loc[amr_mask],
                system.embedder,
                max_chars=cfg.max_chars_per_message,
            )
            z2[amr_mask] = system.amr_refiner.refine(z2[amr_mask], h_amr)

        p2 = sigmoid(z2)
        out2 = {"z2": z2, "p2": p2, "u2": entropy_from_p(p2), "n2": out2a["n2"]}
        X_meta12 = build_meta12_table(out1, out2, amr_used=amr_mask.astype(np.float32))
        p12 = system.meta12.predict_proba(X_meta12.to_numpy(dtype=np.float32))[:, 1]

        stage3_mask = gate_stage3(p12, out1["n1"], out2["n2"], th)
        X3 = self.stage3_extractor.extract(df, edges_df, num_nodes_total=nodes_total)
        p3 = np.full(len(df), 0.5, dtype=np.float64)
        z3 = np.zeros(len(df), dtype=np.float64)
        n3 = np.zeros(len(df), dtype=np.float64)
        if stage3_mask.any():
            out3 = system.stage3.predict(X3[stage3_mask])
            p3[stage3_mask] = out3["p3"]
            z3[stage3_mask] = out3["z3"]
            n3[stage3_mask] = out3["n3"]

        X_meta123 = pd.DataFrame(
            {
                "z12": logit(p12),
                "z3": z3,
                "stage3_used": stage3_mask.astype(np.float32),
                "n1": out1["n1"],
                "n2": out2["n2"],
                "n3": n3,
            }
        )
        p_final = system.meta123.predict_proba(X_meta123.to_numpy(dtype=np.float32))[:, 1]

        return pd.DataFrame(
            {
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
            }
        )

    @staticmethod
    def _default_cfg(dataset: str) -> FeatureConfig:
        if dataset == "twibot":
            return FeatureConfig(stage1_numeric_cols=list(STAGE1_TWITTER_COLUMNS))
        return FeatureConfig(stage1_numeric_cols=[])
