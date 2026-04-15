
from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional

_NEAR_DUP_SIM_THRESHOLD = 0.9


def simple_linguistic_features(text: str) -> np.ndarray:
    if not text:
        return np.zeros(4, dtype=np.float32)
    s = text.strip()
    length = len(s)
    tokens = [t for t in s.split() if t]
    uniq_ratio = len(set(tokens)) / max(len(tokens), 1)
    punct = sum(1 for c in s if c in ".,!?;:")
    punct_ratio = punct / max(length, 1)
    digit = sum(1 for c in s if c.isdigit())
    digit_ratio = digit / max(length, 1)
    return np.array([length, uniq_ratio, punct_ratio, digit_ratio], dtype=np.float32)


def extract_stage2_features(df: pd.DataFrame, embedder, max_msgs: int = 50, max_chars: int = 500) -> np.ndarray:
    """
    Uses df['messages'] built from user_post_comment.json (posts/comment_1/comment_2). :contentReference[oaicite:17]{index=17}
    """
    rows: List[np.ndarray] = []

    # figure embedding dim once
    probe_dim = None

    for _, r in df.iterrows():
        messages: List[Dict[str, Any]] = r.get("messages") or []
        # keep last max_msgs (most recent) OR sample; here: most recent
        messages = messages[-max_msgs:] if len(messages) > max_msgs else messages

        # build embedding texts: message texts + username/profile
        texts = []
        ts = []

        for m in messages:
            t = (m.get("text") or "")[:max_chars].strip()
            if t:
                texts.append(t)
            if m.get("ts") is not None:
                ts.append(float(m["ts"]))


        if len(texts) > 0:
            emb = embedder.encode(texts)
            if probe_dim is None:
                probe_dim = emb.shape[1]
            emb_pool = emb.mean(axis=0).astype(np.float32)
            # FEAT-04: Cross-message cosine similarity (indices 395, 396)
            if emb.shape[0] >= 2:
                sim_matrix = emb @ emb.T  # cosine sim since embedder normalizes
                n_msgs = sim_matrix.shape[0]
                mask = ~np.eye(n_msgs, dtype=bool)
                off_diag = sim_matrix[mask]
                cross_msg_sim_mean = float(np.mean(off_diag))
                near_dup_frac = float(np.mean(off_diag > _NEAR_DUP_SIM_THRESHOLD))
            else:
                cross_msg_sim_mean = 0.0
                near_dup_frac = 0.0
        else:
            if probe_dim is None:
                # fallback default if nothing encoded yet
                probe_dim = 384
            emb_pool = np.zeros(probe_dim, dtype=np.float32)
            cross_msg_sim_mean = 0.0
            near_dup_frac = 0.0

        # linguistic aggregate (on message texts only)
        if len(messages) > 0:
            ling = [simple_linguistic_features((m.get("text") or "")) for m in messages]
            ling_pool = np.mean(np.stack(ling), axis=0).astype(np.float32)
        else:
            ling_pool = np.zeros(4, dtype=np.float32)

        # temporal stats
        if len(ts) >= 2:
            ts_sorted = np.sort(np.array(ts, dtype=np.float64))
            deltas = np.diff(ts_sorted)
            span = max(ts_sorted[-1] - ts_sorted[0], 1.0)
            rate = len(ts_sorted) / span
            delta_mean = float(np.mean(deltas))
            delta_std = float(np.std(deltas))
        else:
            rate, delta_mean, delta_std = 0.0, 0.0, 0.0

        # FEAT-01: CoV of inter-post intervals
        if len(ts) >= 2:
            cv_intervals = float(delta_std / max(delta_mean, 1e-6))
        else:
            cv_intervals = 0.0

        # FEAT-02: Character length stats
        if len(messages) > 0:
            char_lens = [len(m.get("text") or "") for m in messages]
            char_len_mean = float(np.mean(char_lens))
            char_len_std = float(np.std(char_lens))
        else:
            char_len_mean, char_len_std = 0.0, 0.0

        # FEAT-03: Posting hour entropy (Shannon, bits)
        if len(ts) >= 2:
            hours = [datetime.utcfromtimestamp(t).hour for t in ts]
            counts = np.bincount(hours, minlength=24).astype(np.float64)
            probs = counts / counts.sum()
            nonzero = probs[probs > 0]
            hour_entropy = float(-np.sum(nonzero * np.log2(nonzero)))
        else:
            hour_entropy = 0.0

        temporal = np.array([rate, delta_mean, delta_std, cv_intervals, char_len_mean, char_len_std, hour_entropy], dtype=np.float32)

        feat = np.concatenate([emb_pool, ling_pool, temporal, np.array([cross_msg_sim_mean, near_dup_frac], dtype=np.float32)], axis=0)
        rows.append(feat)

    return np.stack(rows, axis=0)