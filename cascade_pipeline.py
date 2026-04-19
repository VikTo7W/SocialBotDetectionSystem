"""
cascade_pipeline.py — single maintained module for the bot-detection cascade.

Owns:
  - all feature extraction (Stage1Extractor, Stage2Extractor, Stage3Extractor)
  - all stage models (Stage1MetadataModel, Stage2BaseContentModel,
    Stage3StructuralModel, AMRDeltaRefiner)
  - training contract types (FeatureConfig, StageThresholds, TrainedSystem)
  - math / routing helpers
  - CascadePipeline — the end-to-end fit/predict orchestrator
  - top-level predict_system / train_system helpers (used by callers and tests)

botsim24_io.py, twibot20_io.py, and the features/ package have been deleted.
Data I/O lives in data_io.py. All feature extraction lives here.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional

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
    stage1_numeric_cols: List[str]
    max_messages_per_account: int = 50
    max_chars_per_message: int = 500


@dataclass
class StageThresholds:
    s1_bot: float = 0.98
    s1_human: float = 0.02
    n1_max_for_exit: float = 3.0
    s2a_bot: float = 0.95
    s2a_human: float = 0.05
    n2_trigger: float = 3.0
    disagreement_trigger: float = 4.0
    s12_bot: float = 0.98
    s12_human: float = 0.02
    novelty_force_stage3: float = 3.5


class TextEmbedder:
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
    embedder: Any

    stage1: "Stage1MetadataModel"
    stage2a: "Stage2BaseContentModel"
    amr_refiner: Optional["AMRDeltaRefiner"]
    meta12: LogisticRegression

    stage3: "Stage3StructuralModel"
    meta123: LogisticRegression


# ---------------------------------------------------------------------------
# Stage 1 feature extraction
# ---------------------------------------------------------------------------

_SECONDS_PER_DAY = 86400.0

STAGE1_TWITTER_COLUMNS = [
    "screen_name_len",
    "screen_name_digit_ratio",
    "statuses_count",
    "followers_count",
    "friends_count",
    "followers_friends_ratio",
    "account_age_days",
    "statuses_per_day",
    "tweet_count_loaded",
    "domain_count",
    "rt_fraction",
    "mt_fraction",
    "original_fraction",
    "unique_rt_mt_targets",
]


class Stage1Extractor:
    def __init__(self, dataset: str) -> None:
        if dataset not in {"botsim", "twibot"}:
            raise ValueError(f"unknown dataset: {dataset!r}")
        self.dataset = dataset

    def extract(self, df: pd.DataFrame, reference_time: pd.Timestamp | None = None) -> np.ndarray:
        if self.dataset == "botsim":
            return self._extract_botsim(df)
        return self._extract_twibot(df, reference_time=reference_time)

    def _extract_botsim(self, df: pd.DataFrame) -> np.ndarray:
        name_len = df["username"].fillna("").astype(str).map(len).to_numpy(dtype=np.float32)
        post_num = df["submission_num"].to_numpy(dtype=np.float32)
        c1 = df["comment_num_1"].to_numpy(dtype=np.float32)
        c2 = df["comment_num_2"].to_numpy(dtype=np.float32)
        c_total = c1 + c2
        sr_num = df["subreddit_list"].map(
            lambda v: len(v) if isinstance(v, list) else 0
        ).to_numpy(dtype=np.float32)
        eps = 1e-6
        X = np.stack([
            name_len, post_num, c1, c2, c_total, sr_num,
            post_num / (c1 + eps), post_num / (c2 + eps),
            post_num / (c_total + eps), post_num / (sr_num + eps),
        ], axis=1)
        return np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    def _extract_twibot(self, df: pd.DataFrame, reference_time: pd.Timestamp | None = None) -> np.ndarray:
        if reference_time is None:
            reference_time = pd.Timestamp.utcnow()
        if reference_time.tzinfo is None:
            reference_time = reference_time.tz_localize("UTC")
        else:
            reference_time = reference_time.tz_convert("UTC")

        rows: List[np.ndarray] = []
        for _, row in df.iterrows():
            screen_name = str(row.get("screen_name") or "")
            statuses_count = float(row.get("statuses_count") or 0.0)
            followers_count = float(row.get("followers_count") or 0.0)
            friends_count = float(row.get("friends_count") or 0.0)
            messages = list(row.get("messages") or [])
            domains = row.get("domain_list") or []

            age_days = _safe_account_age_days(row.get("created_at"), reference_time)
            breakdown = _tweet_breakdown(messages)
            rows.append(np.array([
                float(len(screen_name)),
                float(sum(1 for ch in screen_name if ch.isdigit()) / max(len(screen_name), 1)),
                statuses_count, followers_count, friends_count,
                float(followers_count / max(friends_count, 1.0)),
                age_days,
                float(statuses_count / max(age_days, 1.0)),
                breakdown["tweet_count_loaded"],
                float(len(domains)),
                breakdown["rt_fraction"], breakdown["mt_fraction"],
                breakdown["original_fraction"], breakdown["unique_rt_mt_targets"],
            ], dtype=np.float32))

        if not rows:
            return np.zeros((0, len(STAGE1_TWITTER_COLUMNS)), dtype=np.float32)
        return np.nan_to_num(np.stack(rows, axis=0), nan=0.0, posinf=0.0, neginf=0.0)


def _safe_account_age_days(created_at: Any, reference_time: pd.Timestamp | None) -> float:
    text = str(created_at or "").strip()
    if not text or reference_time is None:
        return 0.0
    try:
        created_dt = parsedate_to_datetime(text)
    except (TypeError, ValueError, IndexError, OverflowError):
        return 0.0
    created_ts = pd.Timestamp(created_dt)
    if created_ts.tzinfo is None:
        created_ts = created_ts.tz_localize("UTC")
    else:
        created_ts = created_ts.tz_convert("UTC")
    return float(max((reference_time - created_ts).total_seconds(), 0.0) / _SECONDS_PER_DAY)


def _tweet_breakdown(messages: List[Dict[str, Any]]) -> Dict[str, float]:
    from data_io import parse_tweet_types
    counts = parse_tweet_types(messages)
    total = float(len(messages))
    if total <= 0.0:
        return {"tweet_count_loaded": 0.0, "rt_fraction": 0.0,
                "mt_fraction": 0.0, "original_fraction": 0.0, "unique_rt_mt_targets": 0.0}
    return {
        "tweet_count_loaded": total,
        "rt_fraction": float(counts["rt_count"]) / total,
        "mt_fraction": float(counts["mt_count"]) / total,
        "original_fraction": float(counts["original_count"]) / total,
        "unique_rt_mt_targets": float(len(counts["rt_mt_usernames"])),
    }


# ---------------------------------------------------------------------------
# Stage 2 feature extraction
# ---------------------------------------------------------------------------

_NEAR_DUP_SIM_THRESHOLD = 0.9
_MISSING_TEMPORAL_SENTINEL = -1.0

STAGE2_TWITTER_EMBEDDING_DIM = 384
STAGE2_TWITTER_COLUMNS = (
    [f"emb_{i}" for i in range(STAGE2_TWITTER_EMBEDDING_DIM)]
    + ["char_len_mean", "token_uniq_ratio_mean", "punct_ratio_mean", "digit_ratio_mean"]
    + ["message_count", "char_len_std", "cross_msg_sim_mean", "near_dup_frac", "nonempty_frac"]
)


def simple_linguistic_features(text: str) -> np.ndarray:
    if not text:
        return np.zeros(4, dtype=np.float32)
    s = text.strip()
    length = len(s)
    tokens = [t for t in s.split() if t]
    return np.array([
        length,
        len(set(tokens)) / max(len(tokens), 1),
        sum(1 for c in s if c in ".,!?;:") / max(length, 1),
        sum(1 for c in s if c.isdigit()) / max(length, 1),
    ], dtype=np.float32)


class Stage2Extractor:
    def __init__(self, dataset: str) -> None:
        if dataset not in {"botsim", "twibot"}:
            raise ValueError(f"unknown dataset: {dataset!r}")
        self.dataset = dataset

    def extract(self, df: pd.DataFrame, embedder, max_msgs: int = 50, max_chars: int = 500) -> np.ndarray:
        if self.dataset == "botsim":
            return self._extract_botsim(df, embedder, max_msgs=max_msgs, max_chars=max_chars)
        return self._extract_twibot(df, embedder, max_msgs=max_msgs, max_chars=max_chars)

    def extract_amr(self, df: pd.DataFrame, embedder, max_chars: int = 500) -> np.ndarray:
        amr_texts = []
        zero_mask = []
        for _, row in df.iterrows():
            messages = row.get("messages") or []
            if messages:
                anchor = str(messages[-1].get("text") or "")[:max_chars].strip()
                amr_texts.append(anchor)
                zero_mask.append(not bool(anchor))
            else:
                amr_texts.append("")
                zero_mask.append(True)
        emb = self._batch_encode(embedder, amr_texts)
        for idx, is_zero in enumerate(zero_mask):
            if is_zero:
                emb[idx] = np.zeros(emb.shape[1], dtype=np.float32)
        return emb

    def _extract_botsim(self, df: pd.DataFrame, embedder, max_msgs: int = 50, max_chars: int = 500) -> np.ndarray:
        rows: List[np.ndarray] = []
        probe_dim = None

        for _, row in df.iterrows():
            messages: List[Dict[str, Any]] = row.get("messages") or []
            messages = messages[-max_msgs:] if len(messages) > max_msgs else messages

            texts: List[str] = []
            ts: List[float] = []
            for m in messages:
                text = str((m or {}).get("text") or "")[:max_chars].strip()
                if text:
                    texts.append(text)
                if m.get("ts") is not None:
                    ts.append(float(m["ts"]))

            if texts:
                emb = np.asarray(embedder.encode(texts), dtype=np.float32)
                if probe_dim is None:
                    probe_dim = int(emb.shape[1])
                emb_pool = emb.mean(axis=0).astype(np.float32)
                if emb.shape[0] >= 2:
                    sim = emb @ emb.T
                    off = sim[~np.eye(sim.shape[0], dtype=bool)]
                    cross_msg_sim_mean = float(np.mean(off))
                    near_dup_frac = float(np.mean(off > _NEAR_DUP_SIM_THRESHOLD))
                else:
                    cross_msg_sim_mean = near_dup_frac = 0.0
            else:
                if probe_dim is None:
                    probe_dim = 384
                emb_pool = np.zeros(probe_dim, dtype=np.float32)
                cross_msg_sim_mean = near_dup_frac = 0.0

            ling_pool = (
                np.mean(np.stack([simple_linguistic_features(m.get("text") or "") for m in messages]), axis=0).astype(np.float32)
                if messages else np.zeros(4, dtype=np.float32)
            )

            temporal_missing = len(messages) > 0 and len(ts) == 0
            if len(ts) >= 2:
                ts_s = np.sort(np.array(ts, dtype=np.float64))
                deltas = np.diff(ts_s)
                span = max(ts_s[-1] - ts_s[0], 1.0)
                rate = len(ts_s) / span
                delta_mean = float(np.mean(deltas))
                delta_std = float(np.std(deltas))
                cv_intervals = float(delta_std / max(delta_mean, 1e-6))
                hours = [datetime.utcfromtimestamp(t).hour for t in ts]
                counts = np.bincount(hours, minlength=24).astype(np.float64)
                probs = counts / counts.sum()
                nonzero = probs[probs > 0]
                hour_entropy = float(-np.sum(nonzero * np.log2(nonzero)))
            elif temporal_missing:
                rate = delta_mean = delta_std = cv_intervals = hour_entropy = _MISSING_TEMPORAL_SENTINEL
            else:
                rate = delta_mean = delta_std = cv_intervals = hour_entropy = 0.0

            char_lens = [len(m.get("text") or "") for m in messages]
            char_len_mean = float(np.mean(char_lens)) if messages else 0.0
            char_len_std = float(np.std(char_lens)) if messages else 0.0

            temporal = np.array([rate, delta_mean, delta_std, cv_intervals,
                                  char_len_mean, char_len_std, hour_entropy], dtype=np.float32)
            rows.append(np.concatenate([emb_pool, ling_pool, temporal,
                                         np.array([cross_msg_sim_mean, near_dup_frac], dtype=np.float32)]))

        return np.stack(rows, axis=0)

    def _extract_twibot(self, df: pd.DataFrame, embedder, max_msgs: int = 50, max_chars: int = 500) -> np.ndarray:
        rows: List[np.ndarray] = []
        account_texts: List[List[str]] = []
        flat_nonempty: List[str] = []

        for _, row in df.iterrows():
            messages = list(row.get("messages") or [])
            texts = self._select_texts(messages, max_msgs=max_msgs, max_chars=max_chars)
            account_texts.append(texts)
            flat_nonempty.extend(t for t in texts if t)

        flat_emb = self._batch_encode(embedder, flat_nonempty)
        probe_dim = int(flat_emb.shape[1]) if flat_emb.size else STAGE2_TWITTER_EMBEDDING_DIM
        cursor = 0

        for texts in account_texts:
            nonempty = sum(1 for t in texts if t)
            if nonempty:
                embeddings = flat_emb[cursor:cursor + nonempty]
                cursor += nonempty
                emb_pool = embeddings.mean(axis=0).astype(np.float32)
            else:
                embeddings = np.zeros((0, probe_dim), dtype=np.float32)
                emb_pool = np.zeros(probe_dim, dtype=np.float32)

            if texts:
                ling = np.stack([simple_linguistic_features(t) for t in texts], axis=0)
                ling_pool = ling.mean(axis=0).astype(np.float32)
                char_lengths = np.array([len(t) for t in texts], dtype=np.float32)
                char_len_std = float(np.std(char_lengths))
                nonempty_frac = float(nonempty / len(texts))
                message_count = float(len(texts))
            else:
                ling_pool = np.zeros(4, dtype=np.float32)
                char_len_std = nonempty_frac = message_count = 0.0

            if embeddings.shape[0] >= 2:
                sim = embeddings @ embeddings.T
                off = sim[~np.eye(sim.shape[0], dtype=bool)]
                cross_msg_sim_mean = float(np.mean(off))
                near_dup_frac = float(np.mean(off > _NEAR_DUP_SIM_THRESHOLD))
            else:
                cross_msg_sim_mean = near_dup_frac = 0.0

            extras = np.array([message_count, char_len_std, cross_msg_sim_mean,
                                near_dup_frac, nonempty_frac], dtype=np.float32)
            rows.append(np.concatenate([emb_pool, ling_pool, extras]))

        if not rows:
            return np.zeros((0, len(STAGE2_TWITTER_COLUMNS)), dtype=np.float32)
        return np.stack(rows, axis=0).astype(np.float32, copy=False)

    def _batch_encode(self, embedder, texts: List[str], batch_size: int = 256) -> np.ndarray:
        if not texts:
            return np.zeros((0, STAGE2_TWITTER_EMBEDDING_DIM), dtype=np.float32)
        unique: List[str] = []
        t2i: Dict[str, int] = {}
        inv: List[int] = []
        for t in texts:
            idx = t2i.get(t)
            if idx is None:
                idx = len(unique)
                t2i[t] = idx
                unique.append(t)
            inv.append(idx)
        uniq_emb = np.asarray(embedder.encode(unique, batch_size=batch_size), dtype=np.float32)
        return uniq_emb[np.asarray(inv, dtype=np.int32)]

    def _select_texts(self, messages: List[Dict[str, Any]], max_msgs: int, max_chars: int) -> List[str]:
        selected = messages[-max_msgs:] if len(messages) > max_msgs else messages
        return [str((m or {}).get("text") or "")[:max_chars].strip() for m in selected]


# ---------------------------------------------------------------------------
# Stage 3 feature extraction
# ---------------------------------------------------------------------------

STAGE3_TWITTER_COLUMNS = [
    "in_deg", "out_deg", "deg_total", "in_w", "out_w", "w_total",
    "following_in_deg", "following_out_deg", "following_in_w", "following_out_w",
    "follower_in_deg", "follower_out_deg", "follower_in_w", "follower_out_w",
    "type2_in_deg", "type2_out_deg", "type2_in_w", "type2_out_w",
]

TWITTER_NATIVE_EDGE_TYPES = {0: "following", 1: "follower"}


def build_graph_features_nodeidx(
    accounts_df: pd.DataFrame,
    edges_df: pd.DataFrame,
    num_nodes_total: int,
    n_types: int = 3,
) -> np.ndarray:
    node_ids = accounts_df["node_idx"].to_numpy(dtype=np.int32)
    src = edges_df["src"].to_numpy(dtype=np.int32)
    dst = edges_df["dst"].to_numpy(dtype=np.int32)
    w = edges_df["weight"].to_numpy(dtype=np.float32)
    et = edges_df["etype"].to_numpy(dtype=np.int8)

    in_deg = np.zeros(num_nodes_total, dtype=np.float32)
    out_deg = np.zeros(num_nodes_total, dtype=np.float32)
    in_w = np.zeros(num_nodes_total, dtype=np.float32)
    out_w = np.zeros(num_nodes_total, dtype=np.float32)
    np.add.at(out_deg, src, 1.0)
    np.add.at(in_deg, dst, 1.0)
    np.add.at(out_w, src, w)
    np.add.at(in_w, dst, w)

    feats = [in_deg, out_deg, in_deg + out_deg, in_w, out_w, in_w + out_w]
    for edge_type in range(n_types):
        mask = et == edge_type
        in_d_t = np.zeros(num_nodes_total, dtype=np.float32)
        out_d_t = np.zeros(num_nodes_total, dtype=np.float32)
        in_w_t = np.zeros(num_nodes_total, dtype=np.float32)
        out_w_t = np.zeros(num_nodes_total, dtype=np.float32)
        np.add.at(out_d_t, src[mask], 1.0)
        np.add.at(in_d_t, dst[mask], 1.0)
        np.add.at(out_w_t, src[mask], w[mask])
        np.add.at(in_w_t, dst[mask], w[mask])
        feats.extend([in_d_t, out_d_t, in_w_t, out_w_t])

    return np.stack(feats, axis=1)[node_ids]


class Stage3Extractor:
    def __init__(self, dataset: str) -> None:
        if dataset not in {"botsim", "twibot"}:
            raise ValueError(f"unknown dataset: {dataset!r}")
        self.dataset = dataset

    def extract(self, accounts_df: pd.DataFrame, edges_df: pd.DataFrame,
                num_nodes_total: int | None = None) -> np.ndarray:
        if num_nodes_total is None:
            num_nodes_total = 0 if len(accounts_df) == 0 else int(accounts_df["node_idx"].max()) + 1
        return np.asarray(build_graph_features_nodeidx(
            accounts_df=accounts_df, edges_df=edges_df,
            num_nodes_total=num_nodes_total, n_types=3,
        ), dtype=np.float32)


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
        base = (
            lgb.LGBMClassifier(n_estimators=400, learning_rate=0.05, num_leaves=31,
                                subsample=0.9, colsample_bytree=0.9, random_state=self.random_state)
            if HAS_LGB else HistGradientBoostingClassifier(random_state=self.random_state)
        )
        self.model = base.fit(X, y)
        self.cal = CalibratedClassifierCV(self.model, method="isotonic" if self.use_isotonic else "sigmoid", cv=3)
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
    def __init__(self, use_isotonic: bool = False, random_state: int = 42):
        self.random_state = random_state
        self.use_isotonic = use_isotonic
        self.model: Optional[BaseEstimator] = None
        self.cal: Optional[CalibratedClassifierCV] = None
        self.novelty = MahalanobisNovelty()

    def fit(self, X: np.ndarray, y: np.ndarray) -> "Stage2BaseContentModel":
        base = (
            lgb.LGBMClassifier(n_estimators=600, learning_rate=0.05, num_leaves=63,
                                subsample=0.9, colsample_bytree=0.9, random_state=self.random_state)
            if HAS_LGB else HistGradientBoostingClassifier(random_state=self.random_state)
        )
        self.model = base.fit(X, y)
        self.cal = CalibratedClassifierCV(self.model, method="isotonic" if self.use_isotonic else "sigmoid", cv=3)
        self.cal.fit(X, y)
        self.novelty.fit(X)
        return self

    def predict(self, X: np.ndarray) -> Dict[str, np.ndarray]:
        if self.cal is None:
            raise RuntimeError("Stage2a not fitted.")
        p = self.cal.predict_proba(X)[:, 1]
        u = entropy_from_p(p)
        n = self.novelty.score(X)
        return {"p2a": p, "u2": u, "n2": n, "z2a": logit(p)}


class AMRDeltaRefiner:
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
            grad_z = p - y
            self.w -= self.lr * ((h.T @ grad_z) / n + self.l2 * self.w)
            self.b -= self.lr * float(np.mean(grad_z))
        return self

    def delta(self, h_amr: np.ndarray) -> np.ndarray:
        if self.w is None:
            raise RuntimeError("AMRDeltaRefiner not fitted.")
        return (np.asarray(h_amr, dtype=np.float64) @ self.w + self.b).astype(np.float64)

    def refine(self, z_base: np.ndarray, h_amr: np.ndarray) -> np.ndarray:
        return np.asarray(z_base, dtype=np.float64) + self.delta(h_amr)


class Stage3StructuralModel:
    def __init__(self, use_isotonic: bool = False, random_state: int = 42):
        self.random_state = random_state
        self.use_isotonic = use_isotonic
        self.model: Optional[BaseEstimator] = None
        self.cal: Optional[CalibratedClassifierCV] = None
        self.novelty = MahalanobisNovelty()

    def fit(self, X: np.ndarray, y: np.ndarray) -> "Stage3StructuralModel":
        base = (
            lgb.LGBMClassifier(n_estimators=500, learning_rate=0.05, num_leaves=63,
                                subsample=0.9, colsample_bytree=0.9, random_state=self.random_state)
            if HAS_LGB else HistGradientBoostingClassifier(random_state=self.random_state)
        )
        self.model = base.fit(X, y)
        self.cal = CalibratedClassifierCV(self.model, method="isotonic" if self.use_isotonic else "sigmoid", cv=3)
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

def gate_amr(p2a: np.ndarray, n2: np.ndarray, z1: np.ndarray,
             z2a: np.ndarray, th: StageThresholds) -> np.ndarray:
    uncertain = (p2a > th.s2a_human) & (p2a < th.s2a_bot)
    novel = n2 >= th.n2_trigger
    disagree = np.abs(z1 - z2a) >= th.disagreement_trigger
    return uncertain | novel | disagree


def gate_stage3(p12: np.ndarray, n1: np.ndarray, n2: np.ndarray,
                th: StageThresholds) -> np.ndarray:
    uncertain = (p12 > th.s12_human) & (p12 < th.s12_bot)
    novel = np.maximum(n1, n2) >= th.novelty_force_stage3
    return uncertain | novel


# ---------------------------------------------------------------------------
# Meta-model helpers
# ---------------------------------------------------------------------------

def build_meta12_table(stage1_out: Dict[str, np.ndarray], stage2_out: Dict[str, np.ndarray],
                        amr_used: np.ndarray) -> pd.DataFrame:
    z1 = stage1_out["z1"]
    z2 = stage2_out["z2"]
    return pd.DataFrame({
        "z1": z1, "z2": z2,
        "u1": stage1_out["u1"], "u2": stage2_out["u2"],
        "n1": stage1_out["n1"], "n2": stage2_out["n2"],
        "amr_used": amr_used.astype(np.float32),
        "disagree": np.abs(z1 - z2),
    })


def oof_meta12_predictions(X_meta12: pd.DataFrame, y: np.ndarray,
                            n_splits: int = 5, random_state: int = 42) -> np.ndarray:
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    p12_oof = np.zeros(len(y), dtype=np.float64)
    for tr_idx, va_idx in skf.split(X_meta12, y):
        m = train_meta12(X_meta12.iloc[tr_idx], y[tr_idx])
        p12_oof[va_idx] = m.predict_proba(X_meta12.iloc[va_idx].to_numpy(dtype=np.float32))[:, 1]
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
# AMR helpers (used by conftest and callers)
# ---------------------------------------------------------------------------

def amr_linearize_stub(text: str) -> str:
    return text


def extract_amr_embeddings_for_accounts(df: pd.DataFrame, cfg: FeatureConfig, embedder) -> np.ndarray:
    dataset = infer_dataset(df, cfg)
    max_chars = cfg.max_chars_per_message if cfg is not None else 500
    return Stage2Extractor(dataset).extract_amr(df, embedder, max_chars=max_chars)


# Module-level feature extraction helpers (accessible as cp.extract_stage1_matrix etc.)
def extract_stage1_matrix(df: pd.DataFrame) -> np.ndarray:
    return Stage1Extractor("botsim").extract(df)


def extract_stage2_features(df: pd.DataFrame, embedder, max_msgs: int = 50) -> np.ndarray:
    return Stage2Extractor("botsim").extract(df, embedder, max_msgs=max_msgs)


# ---------------------------------------------------------------------------
# CascadePipeline — end-to-end orchestrator
# ---------------------------------------------------------------------------

class CascadePipeline:
    def __init__(self, dataset: str, cfg: FeatureConfig | None = None, *,
                 random_state: int = 42, embedder: TextEmbedder | None = None) -> None:
        if dataset not in {"botsim", "twibot"}:
            raise ValueError(f"unknown dataset: {dataset!r}")
        self.dataset = dataset
        self.random_state = random_state
        self.embedder = embedder
        self.cfg = cfg or self._default_cfg(dataset)
        self.stage1_extractor = Stage1Extractor(dataset)
        self.stage2_extractor = Stage2Extractor(dataset)
        self.stage3_extractor = Stage3Extractor(dataset)

    def fit(self, S1: pd.DataFrame, S2: pd.DataFrame, edges_S1: pd.DataFrame,
            edges_S2: pd.DataFrame, th: StageThresholds, *,
            nodes_total: int | None = None, embedder: TextEmbedder | None = None) -> TrainedSystem:
        embedder = embedder or self.embedder or TextEmbedder()

        X1_tr = self.stage1_extractor.extract(S1)
        y1_tr = S1["label"].to_numpy(dtype=np.int64)
        stage1 = Stage1MetadataModel(use_isotonic=False, random_state=self.random_state).fit(X1_tr, y1_tr)

        X2_tr = self.stage2_extractor.extract(S1, embedder,
                                               max_msgs=self.cfg.max_messages_per_account,
                                               max_chars=self.cfg.max_chars_per_message)
        stage2a = Stage2BaseContentModel(use_isotonic=False, random_state=self.random_state).fit(X2_tr, y1_tr)
        out2a_S1 = stage2a.predict(X2_tr)

        h_amr_S1 = self.stage2_extractor.extract_amr(S1, embedder, max_chars=self.cfg.max_chars_per_message)
        amr_refiner = AMRDeltaRefiner(lr=0.05, epochs=400, l2=1e-3, random_state=self.random_state)
        amr_refiner.fit(h_amr_S1, out2a_S1["z2a"], y1_tr)

        X3_tr = self.stage3_extractor.extract(S1, edges_S1, num_nodes_total=nodes_total)
        stage3 = Stage3StructuralModel(use_isotonic=False, random_state=self.random_state).fit(X3_tr, y1_tr)

        y2 = S2["label"].to_numpy(dtype=np.int64)
        out1_S2 = stage1.predict(self.stage1_extractor.extract(S2))
        X2_S2 = self.stage2_extractor.extract(S2, embedder,
                                               max_msgs=self.cfg.max_messages_per_account,
                                               max_chars=self.cfg.max_chars_per_message)
        out2a_S2 = stage2a.predict(X2_S2)

        amr_mask = gate_amr(out2a_S2["p2a"], out2a_S2["n2"], out1_S2["z1"], out2a_S2["z2a"], th)
        z2 = np.asarray(out2a_S2["z2a"], dtype=np.float64).copy()
        if amr_mask.any():
            h_amr_S2 = self.stage2_extractor.extract_amr(S2.loc[amr_mask], embedder,
                                                          max_chars=self.cfg.max_chars_per_message)
            z2[amr_mask] = amr_refiner.refine(z2[amr_mask], h_amr_S2)

        p2 = sigmoid(z2)
        out2_S2 = {"z2": z2, "p2": p2, "u2": entropy_from_p(p2), "n2": out2a_S2["n2"]}
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

        X_meta123_S2 = pd.DataFrame({
            "z12": logit(p12_oof), "z3": out3_S2["z3"],
            "stage3_used": stage3_mask.astype(np.float32),
            "n1": out1_S2["n1"], "n2": out2_S2["n2"], "n3": out3_S2["n3"],
        })
        meta123 = train_meta123(X_meta123_S2, y2)

        return TrainedSystem(
            cfg=replace(self.cfg), th=replace(th), embedder=embedder,
            stage1=stage1, stage2a=stage2a, amr_refiner=amr_refiner,
            meta12=meta12, stage3=stage3, meta123=meta123,
        )

    def predict(self, system: TrainedSystem, df: pd.DataFrame, edges_df: pd.DataFrame, *,
                nodes_total: int | None = None) -> pd.DataFrame:
        cfg = system.cfg
        th = system.th

        out1 = system.stage1.predict(self.stage1_extractor.extract(df))
        X2 = self.stage2_extractor.extract(df, system.embedder,
                                            max_msgs=cfg.max_messages_per_account,
                                            max_chars=cfg.max_chars_per_message)
        out2a = system.stage2a.predict(X2)

        amr_mask = gate_amr(out2a["p2a"], out2a["n2"], out1["z1"], out2a["z2a"], th)
        z2 = np.asarray(out2a["z2a"], dtype=np.float64).copy()
        if amr_mask.any():
            h_amr = self.stage2_extractor.extract_amr(df.loc[amr_mask], system.embedder,
                                                       max_chars=cfg.max_chars_per_message)
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

        X_meta123 = pd.DataFrame({
            "z12": logit(p12), "z3": z3,
            "stage3_used": stage3_mask.astype(np.float32),
            "n1": out1["n1"], "n2": out2["n2"], "n3": n3,
        })
        p_final = system.meta123.predict_proba(X_meta123.to_numpy(dtype=np.float32))[:, 1]

        return pd.DataFrame({
            "account_id": df["account_id"].astype(str).values,
            "p1": out1["p1"], "n1": out1["n1"],
            "p2": p2, "n2": out2["n2"],
            "amr_used": amr_mask.astype(int),
            "p12": p12, "stage3_used": stage3_mask.astype(int),
            "p3": p3, "n3": n3, "p_final": p_final,
        })

    @staticmethod
    def _default_cfg(dataset: str) -> FeatureConfig:
        if dataset == "twibot":
            return FeatureConfig(stage1_numeric_cols=list(STAGE1_TWITTER_COLUMNS))
        return FeatureConfig(stage1_numeric_cols=[])


# ---------------------------------------------------------------------------
# Top-level convenience helpers
# ---------------------------------------------------------------------------

def train_system(S1: pd.DataFrame, S2: pd.DataFrame, edges_S1: pd.DataFrame,
                 edges_S2: pd.DataFrame, cfg: FeatureConfig, th: StageThresholds,
                 random_state: int = 42, nodes_total: Optional[int] = None,
                 embedder: Optional[TextEmbedder] = None) -> TrainedSystem:
    dataset = infer_dataset(S1, cfg)
    pipeline = CascadePipeline(dataset=dataset, cfg=cfg, random_state=random_state, embedder=embedder)
    return pipeline.fit(S1, S2, edges_S1, edges_S2, th, nodes_total=nodes_total, embedder=embedder)


def predict_system(sys: TrainedSystem, df: pd.DataFrame, edges_df: pd.DataFrame,
                   nodes_total: Optional[int] = None) -> pd.DataFrame:
    dataset = infer_dataset(df, sys.cfg)
    pipeline = CascadePipeline(dataset=dataset, cfg=sys.cfg, embedder=sys.embedder)
    return pipeline.predict(sys, df, edges_df, nodes_total=nodes_total)
