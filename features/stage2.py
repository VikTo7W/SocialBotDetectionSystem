from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

import numpy as np
import pandas as pd

_NEAR_DUP_SIM_THRESHOLD = 0.9
_MISSING_TEMPORAL_SENTINEL = -1.0

STAGE2_TWITTER_EMBEDDING_DIM = 384
STAGE2_TWITTER_COLUMNS = (
    [f"emb_{idx}" for idx in range(STAGE2_TWITTER_EMBEDDING_DIM)]
    + ["char_len_mean", "token_uniq_ratio_mean", "punct_ratio_mean", "digit_ratio_mean"]
    + ["message_count", "char_len_std", "cross_msg_sim_mean", "near_dup_frac", "nonempty_frac"]
)


class Stage2Extractor:
    def __init__(self, dataset: str) -> None:
        if dataset not in {"botsim", "twibot"}:
            raise ValueError(f"unknown dataset: {dataset!r}")
        self.dataset = dataset

    def extract(
        self,
        df: pd.DataFrame,
        embedder,
        max_msgs: int = 50,
        max_chars: int = 500,
    ) -> np.ndarray:
        if self.dataset == "botsim":
            return self._extract_botsim(df, embedder, max_msgs=max_msgs, max_chars=max_chars)
        return self._extract_twibot(df, embedder, max_msgs=max_msgs, max_chars=max_chars)

    def extract_amr(
        self,
        df: pd.DataFrame,
        embedder,
        max_chars: int = 500,
    ) -> np.ndarray:
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

    def _extract_botsim(
        self,
        df: pd.DataFrame,
        embedder,
        max_msgs: int = 50,
        max_chars: int = 500,
    ) -> np.ndarray:
        rows: List[np.ndarray] = []
        probe_dim = None

        for _, row in df.iterrows():
            messages: List[Dict[str, Any]] = row.get("messages") or []
            messages = messages[-max_msgs:] if len(messages) > max_msgs else messages

            texts: List[str] = []
            ts: List[float] = []
            for message in messages:
                text = str((message or {}).get("text") or "")[:max_chars].strip()
                if text:
                    texts.append(text)
                if message.get("ts") is not None:
                    ts.append(float(message["ts"]))

            if texts:
                emb = np.asarray(embedder.encode(texts), dtype=np.float32)
                if probe_dim is None:
                    probe_dim = int(emb.shape[1])
                emb_pool = emb.mean(axis=0).astype(np.float32)
                if emb.shape[0] >= 2:
                    sim_matrix = emb @ emb.T
                    mask = ~np.eye(sim_matrix.shape[0], dtype=bool)
                    off_diag = sim_matrix[mask]
                    cross_msg_sim_mean = float(np.mean(off_diag))
                    near_dup_frac = float(np.mean(off_diag > _NEAR_DUP_SIM_THRESHOLD))
                else:
                    cross_msg_sim_mean = 0.0
                    near_dup_frac = 0.0
            else:
                if probe_dim is None:
                    probe_dim = 384
                emb_pool = np.zeros(probe_dim, dtype=np.float32)
                cross_msg_sim_mean = 0.0
                near_dup_frac = 0.0

            if messages:
                ling = [self._simple_linguistic_features((message.get("text") or "")) for message in messages]
                ling_pool = np.mean(np.stack(ling), axis=0).astype(np.float32)
            else:
                ling_pool = np.zeros(4, dtype=np.float32)

            temporal_missing = len(messages) > 0 and len(ts) == 0
            if len(ts) >= 2:
                ts_sorted = np.sort(np.array(ts, dtype=np.float64))
                deltas = np.diff(ts_sorted)
                span = max(ts_sorted[-1] - ts_sorted[0], 1.0)
                rate = len(ts_sorted) / span
                delta_mean = float(np.mean(deltas))
                delta_std = float(np.std(deltas))
            elif temporal_missing:
                rate = _MISSING_TEMPORAL_SENTINEL
                delta_mean = _MISSING_TEMPORAL_SENTINEL
                delta_std = _MISSING_TEMPORAL_SENTINEL
            else:
                rate = 0.0
                delta_mean = 0.0
                delta_std = 0.0

            if len(ts) >= 2:
                cv_intervals = float(delta_std / max(delta_mean, 1e-6))
            elif temporal_missing:
                cv_intervals = _MISSING_TEMPORAL_SENTINEL
            else:
                cv_intervals = 0.0

            if messages:
                char_lens = [len(message.get("text") or "") for message in messages]
                char_len_mean = float(np.mean(char_lens))
                char_len_std = float(np.std(char_lens))
            else:
                char_len_mean = 0.0
                char_len_std = 0.0

            if len(ts) >= 2:
                hours = [datetime.utcfromtimestamp(timestamp).hour for timestamp in ts]
                counts = np.bincount(hours, minlength=24).astype(np.float64)
                probs = counts / counts.sum()
                nonzero = probs[probs > 0]
                hour_entropy = float(-np.sum(nonzero * np.log2(nonzero)))
            elif temporal_missing:
                hour_entropy = _MISSING_TEMPORAL_SENTINEL
            else:
                hour_entropy = 0.0

            temporal = np.array(
                [
                    rate,
                    delta_mean,
                    delta_std,
                    cv_intervals,
                    char_len_mean,
                    char_len_std,
                    hour_entropy,
                ],
                dtype=np.float32,
            )
            rows.append(
                np.concatenate(
                    [
                        emb_pool,
                        ling_pool,
                        temporal,
                        np.array([cross_msg_sim_mean, near_dup_frac], dtype=np.float32),
                    ],
                    axis=0,
                )
            )

        return np.stack(rows, axis=0)

    def _extract_twibot(
        self,
        df: pd.DataFrame,
        embedder,
        max_msgs: int = 50,
        max_chars: int = 500,
    ) -> np.ndarray:
        rows: List[np.ndarray] = []
        account_texts: List[List[str]] = []
        flat_nonempty_texts: List[str] = []

        for _, row in df.iterrows():
            messages = list(row.get("messages") or [])
            texts = self._select_texts(messages, max_msgs=max_msgs, max_chars=max_chars)
            account_texts.append(texts)
            flat_nonempty_texts.extend(text for text in texts if text)

        flat_embeddings = self._batch_encode(embedder, flat_nonempty_texts)
        probe_dim = int(flat_embeddings.shape[1]) if flat_embeddings.size else STAGE2_TWITTER_EMBEDDING_DIM
        cursor = 0

        for texts in account_texts:
            nonempty_count = sum(1 for text in texts if text)
            if nonempty_count:
                embeddings = flat_embeddings[cursor:cursor + nonempty_count]
                cursor += nonempty_count
                emb_pool = embeddings.mean(axis=0).astype(np.float32)
            else:
                embeddings = np.zeros((0, probe_dim), dtype=np.float32)
                emb_pool = np.zeros(probe_dim, dtype=np.float32)

            if texts:
                ling = np.stack([self._simple_linguistic_features(text) for text in texts], axis=0)
                ling_pool = ling.mean(axis=0).astype(np.float32)
                char_lengths = np.array([len(text) for text in texts], dtype=np.float32)
                char_len_std = float(np.std(char_lengths))
                nonempty_frac = float(nonempty_count / len(texts))
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

            extras = np.array(
                [
                    message_count,
                    char_len_std,
                    cross_msg_sim_mean,
                    near_dup_frac,
                    nonempty_frac,
                ],
                dtype=np.float32,
            )
            rows.append(np.concatenate([emb_pool, ling_pool, extras], axis=0))

        if not rows:
            return np.zeros((0, len(STAGE2_TWITTER_COLUMNS)), dtype=np.float32)

        return np.stack(rows, axis=0).astype(np.float32, copy=False)

    def _batch_encode(self, embedder, texts: List[str], batch_size: int = 256) -> np.ndarray:
        if not texts:
            return np.zeros((0, STAGE2_TWITTER_EMBEDDING_DIM), dtype=np.float32)
        unique_texts: List[str] = []
        text_to_index: Dict[str, int] = {}
        inverse_indices: List[int] = []

        for text in texts:
            idx = text_to_index.get(text)
            if idx is None:
                idx = len(unique_texts)
                text_to_index[text] = idx
                unique_texts.append(text)
            inverse_indices.append(idx)

        unique_embeddings = np.asarray(embedder.encode(unique_texts, batch_size=batch_size), dtype=np.float32)
        return unique_embeddings[np.asarray(inverse_indices, dtype=np.int32)]

    def _simple_linguistic_features(self, text: str) -> np.ndarray:
        if not text:
            return np.zeros(4, dtype=np.float32)
        stripped = text.strip()
        length = len(stripped)
        tokens = [token for token in stripped.split() if token]
        uniq_ratio = len(set(tokens)) / max(len(tokens), 1)
        punct_ratio = sum(1 for ch in stripped if ch in ".,!?;:") / max(length, 1)
        digit_ratio = sum(1 for ch in stripped if ch.isdigit()) / max(length, 1)
        return np.array([length, uniq_ratio, punct_ratio, digit_ratio], dtype=np.float32)

    def _select_texts(
        self,
        messages: List[Dict[str, Any]],
        max_msgs: int,
        max_chars: int,
    ) -> List[str]:
        selected = messages[-max_msgs:] if len(messages) > max_msgs else messages
        texts: List[str] = []
        for message in selected:
            text = str((message or {}).get("text") or "")[:max_chars].strip()
            texts.append(text)
        return texts
