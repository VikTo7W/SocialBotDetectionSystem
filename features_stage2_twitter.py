from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd

_NEAR_DUP_SIM_THRESHOLD = 0.9

STAGE2_TWITTER_EMBEDDING_DIM = 384
STAGE2_TWITTER_COLUMNS = (
    [f"emb_{idx}" for idx in range(STAGE2_TWITTER_EMBEDDING_DIM)]
    + ["char_len_mean", "token_uniq_ratio_mean", "punct_ratio_mean", "digit_ratio_mean"]
    + ["message_count", "char_len_std", "cross_msg_sim_mean", "near_dup_frac", "nonempty_frac"]
)


def _simple_linguistic_features(text: str) -> np.ndarray:
    if not text:
        return np.zeros(4, dtype=np.float32)
    stripped = text.strip()
    length = len(stripped)
    tokens = [token for token in stripped.split() if token]
    uniq_ratio = len(set(tokens)) / max(len(tokens), 1)
    punct_ratio = sum(1 for ch in stripped if ch in ".,!?;:") / max(length, 1)
    digit_ratio = sum(1 for ch in stripped if ch.isdigit()) / max(length, 1)
    return np.array([length, uniq_ratio, punct_ratio, digit_ratio], dtype=np.float32)


def _select_texts(messages: List[Dict[str, Any]], max_msgs: int, max_chars: int) -> List[str]:
    selected = messages[-max_msgs:] if len(messages) > max_msgs else messages
    texts: List[str] = []
    for message in selected:
        text = str((message or {}).get("text") or "")[:max_chars].strip()
        texts.append(text)
    return texts


def extract_stage2_features_twitter(
    df: pd.DataFrame,
    embedder,
    max_msgs: int = 50,
    max_chars: int = 500,
) -> np.ndarray:
    """
    Standalone TwiBot-native Stage 2 extractor for tweet text.

    Output contract:
    - 384 pooled embedding dimensions
    - 4 mean lightweight linguistic features
    - message_count
    - char_len_std
    - cross_msg_sim_mean
    - near_dup_frac
    - nonempty_frac

    The native path omits the Reddit-transfer timestamp sentinel features.
    """
    rows: List[np.ndarray] = []
    probe_dim = None

    for _, row in df.iterrows():
        messages = list(row.get("messages") or [])
        texts = _select_texts(messages, max_msgs=max_msgs, max_chars=max_chars)
        nonempty_texts = [text for text in texts if text]

        if nonempty_texts:
            embeddings = np.asarray(embedder.encode(nonempty_texts), dtype=np.float32)
            if probe_dim is None:
                probe_dim = int(embeddings.shape[1])
            emb_pool = embeddings.mean(axis=0).astype(np.float32)
        else:
            if probe_dim is None:
                probe_dim = STAGE2_TWITTER_EMBEDDING_DIM
            embeddings = np.zeros((0, probe_dim), dtype=np.float32)
            emb_pool = np.zeros(probe_dim, dtype=np.float32)

        if texts:
            ling = np.stack([_simple_linguistic_features(text) for text in texts], axis=0)
            ling_pool = ling.mean(axis=0).astype(np.float32)
            char_lengths = np.array([len(text) for text in texts], dtype=np.float32)
            char_len_std = float(np.std(char_lengths))
            nonempty_frac = float(sum(1 for text in texts if text) / len(texts))
            message_count = float(len(texts))
        else:
            ling_pool = np.zeros(4, dtype=np.float32)
            char_len_std = 0.0
            nonempty_frac = 0.0
            message_count = 0.0

        if embeddings.shape[0] >= 2:
            sim_matrix = embeddings @ embeddings.T
            mask = ~np.eye(sim_matrix.shape[0], dtype=bool)
            off_diag = sim_matrix[mask]
            cross_msg_sim_mean = float(np.mean(off_diag))
            near_dup_frac = float(np.mean(off_diag > _NEAR_DUP_SIM_THRESHOLD))
        else:
            cross_msg_sim_mean = 0.0
            near_dup_frac = 0.0

        extras = np.array([
            message_count,
            char_len_std,
            cross_msg_sim_mean,
            near_dup_frac,
            nonempty_frac,
        ], dtype=np.float32)

        rows.append(np.concatenate([emb_pool, ling_pool, extras], axis=0))

    if not rows:
        return np.zeros((0, len(STAGE2_TWITTER_COLUMNS)), dtype=np.float32)

    return np.stack(rows, axis=0).astype(np.float32, copy=False)
