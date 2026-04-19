"""
Tests for leakage fixes and new behavioral features.

Requirements covered:
  - LEAK-02: No identity strings (USERNAME:/PROFILE:) in embedding pool
  - LEAK-03: AMR anchor uses most-recent message text, not profile field
  - FEAT-01: cv_intervals at index 391
  - FEAT-02: char_len_mean, char_len_std at indices 392, 393
  - FEAT-03: hour_entropy at index 394
  - FEAT-04: cross_msg_sim_mean at index 395, near_dup_frac at index 396

Feature vector layout (after FEAT-04):
  [0..383]  emb_pool          (384-dim)
  [384..387] ling_pool        (4-dim)
  [388]     rate
  [389]     delta_mean
  [390]     delta_std
  [391]     cv_intervals      (FEAT-01)
  [392]     char_len_mean     (FEAT-02)
  [393]     char_len_std      (FEAT-02)
  [394]     hour_entropy      (FEAT-03)
  [395]     cross_msg_sim_mean (FEAT-04)
  [396]     near_dup_frac     (FEAT-04)
"""

import numpy as np
import pandas as pd
import pytest

from cascade_pipeline import (
    Stage2Extractor,
    extract_amr_embeddings_for_accounts,
    FeatureConfig,
)


class NormalizedFakeEmbedder:
    """
    Deterministic fake embedder that returns L2-normalized 384-dim vectors.
    Required for FEAT-04 value tests — cosine similarity via emb @ emb.T is
    only valid when embeddings are unit-normalized.
    """

    def encode(self, texts, batch_size: int = 64) -> np.ndarray:
        rng = np.random.RandomState(42)
        raw = rng.randn(len(texts), 384).astype(np.float32)
        norms = np.linalg.norm(raw, axis=1, keepdims=True)
        return raw / np.maximum(norms, 1e-8)


class RecordingEmbedder:
    """Fake embedder that records all texts passed to encode()."""

    def __init__(self):
        self.recorded_texts: list = []

    def encode(self, texts, batch_size: int = 64) -> np.ndarray:
        self.recorded_texts.extend(list(texts))
        rng = np.random.RandomState(42)
        return rng.randn(len(texts), 384).astype(np.float32)


def _make_single_account_df(
    username: str = "user1",
    profile: str = "profile text",
    messages=None,
    label: int = 0,
) -> pd.DataFrame:
    """Return a 1-row DataFrame with all required columns."""
    if messages is None:
        messages = []
    return pd.DataFrame([{
        "account_id": "acc_test",
        "node_idx": 0,
        "label": label,
        "username": username,
        "profile": profile,
        "subreddit_list": [],
        "submission_num": 0,
        "comment_num_1": 0,
        "comment_num_2": 0,
        "messages": messages,
    }])


# ---------------------------------------------------------------------------
# LEAK-02: No identity strings in embedding pool
# ---------------------------------------------------------------------------

def test_no_identity_in_embeddings():
    """USERNAME:/PROFILE: strings must not be passed to the embedder."""
    rec = RecordingEmbedder()
    df = _make_single_account_df(
        username="testbot123",
        profile="I am a bot profile",
        messages=[{"text": "hello", "ts": 1700000000.0}],
    )
    extract = Stage2Extractor("botsim").extract
    extract(df, rec)

    flat = " ".join(rec.recorded_texts)
    assert "USERNAME:" not in flat, "Found 'USERNAME:' in encoded texts"
    assert "PROFILE:" not in flat, "Found 'PROFILE:' in encoded texts"
    assert "testbot123" not in flat, "Found username in encoded texts"
    assert "I am a bot profile" not in flat, "Found profile text in encoded texts"


# ---------------------------------------------------------------------------
# LEAK-03: AMR uses most-recent message text, not profile
# ---------------------------------------------------------------------------

def test_amr_uses_message_not_profile():
    """AMR embedder must encode message text, not profile string."""
    rec = RecordingEmbedder()
    df = _make_single_account_df(
        username="u",
        profile="bot profile text",
        messages=[{"text": "hello world", "ts": 1700000000.0}],
    )
    cfg = FeatureConfig(stage1_numeric_cols=[])
    extract_amr_embeddings_for_accounts(df, cfg, rec)

    flat = " ".join(rec.recorded_texts)
    assert "bot profile text" not in flat, "Profile text must not appear in AMR encoding"
    assert any("hello world" in t for t in rec.recorded_texts), (
        "Most-recent message text must appear in AMR encoding"
    )


def test_amr_zero_for_no_messages():
    """Accounts with no messages must produce an all-zero AMR embedding."""
    rec = RecordingEmbedder()
    df = _make_single_account_df(messages=[])
    cfg = FeatureConfig(stage1_numeric_cols=[])
    result = extract_amr_embeddings_for_accounts(df, cfg, rec)
    assert result.shape[0] == 1
    assert np.allclose(result[0], 0.0), "Zero-message account must yield zero AMR vector"


# ---------------------------------------------------------------------------
# FEAT-01: CoV of inter-post intervals (index 391)
# ---------------------------------------------------------------------------

def test_feat01_default_zero():
    """cv_intervals must be 0.0 when account has 0 messages."""
    rec = RecordingEmbedder()
    df = _make_single_account_df(messages=[])
    feat = Stage2Extractor("botsim").extract(df, rec)
    assert feat.shape == (1, 397), f"Expected (1, 397), got {feat.shape}"
    assert feat[0, 391] == 0.0, "cv_intervals must be 0.0 for 0-message account"


def test_feat01_formula():
    """cv_intervals must equal delta_std / max(delta_mean, 1e-6)."""
    rec = RecordingEmbedder()
    # 3 messages at t=0, 3600, 7200 => deltas=[3600,3600], delta_mean=3600, delta_std=0
    messages = [
        {"text": "msg1", "ts": 0.0},
        {"text": "msg2", "ts": 3600.0},
        {"text": "msg3", "ts": 7200.0},
    ]
    df = _make_single_account_df(messages=messages)
    feat = Stage2Extractor("botsim").extract(df, rec)
    deltas = np.array([3600.0, 3600.0])
    delta_mean = float(np.mean(deltas))
    delta_std = float(np.std(deltas))
    expected_cv = delta_std / max(delta_mean, 1e-6)
    assert abs(feat[0, 391] - expected_cv) < 1e-5, (
        f"cv_intervals mismatch: got {feat[0, 391]}, expected {expected_cv}"
    )


# ---------------------------------------------------------------------------
# FEAT-02: Character length stats (indices 392, 393)
# ---------------------------------------------------------------------------

def test_feat02_default_zero():
    """char_len_mean and char_len_std must be 0.0 for 0-message account."""
    rec = RecordingEmbedder()
    df = _make_single_account_df(messages=[])
    feat = Stage2Extractor("botsim").extract(df, rec)
    assert feat[0, 392] == 0.0, "char_len_mean must be 0.0 for 0 messages"
    assert feat[0, 393] == 0.0, "char_len_std must be 0.0 for 0 messages"


def test_feat02_values():
    """char_len_mean = mean([3,6,2])=3.6667, char_len_std = std([3,6,2])=1.6997."""
    rec = RecordingEmbedder()
    messages = [
        {"text": "aaa", "ts": 0.0},
        {"text": "bbbbbb", "ts": 3600.0},
        {"text": "cc", "ts": 7200.0},
    ]
    df = _make_single_account_df(messages=messages)
    feat = Stage2Extractor("botsim").extract(df, rec)
    lens = [3, 6, 2]
    expected_mean = float(np.mean(lens))
    expected_std = float(np.std(lens))
    assert abs(feat[0, 392] - expected_mean) < 1e-3, (
        f"char_len_mean mismatch: got {feat[0, 392]}, expected {expected_mean}"
    )
    assert abs(feat[0, 393] - expected_std) < 1e-3, (
        f"char_len_std mismatch: got {feat[0, 393]}, expected {expected_std}"
    )


# ---------------------------------------------------------------------------
# FEAT-03: Posting hour entropy (index 394)
# ---------------------------------------------------------------------------

def test_feat03_default_zero():
    """hour_entropy must be 0.0 for accounts with 0 or 1 timestamp."""
    rec = RecordingEmbedder()
    df = _make_single_account_df(messages=[])
    feat = Stage2Extractor("botsim").extract(df, rec)
    assert feat[0, 394] == 0.0, "hour_entropy must be 0.0 for 0 messages"

    # Also test single message
    df1 = _make_single_account_df(messages=[{"text": "hi", "ts": 1700000000.0}])
    feat1 = Stage2Extractor("botsim").extract(df1, rec)
    assert feat1[0, 394] == 0.0, "hour_entropy must be 0.0 for single message"


def test_missing_timestamps_use_sentinel_values():
    """Accounts with messages but no usable timestamps should not look like true zeros."""
    rec = RecordingEmbedder()
    df = _make_single_account_df(
        messages=[
            {"text": "msg1", "ts": None},
            {"text": "msg2", "ts": None},
        ]
    )
    feat = Stage2Extractor("botsim").extract(df, rec)

    assert feat[0, 388] == -1.0, "rate should use missing-timestamp sentinel"
    assert feat[0, 389] == -1.0, "delta_mean should use missing-timestamp sentinel"
    assert feat[0, 390] == -1.0, "delta_std should use missing-timestamp sentinel"
    assert feat[0, 391] == -1.0, "cv_intervals should use missing-timestamp sentinel"
    assert feat[0, 394] == -1.0, "hour_entropy should use missing-timestamp sentinel"


def test_feat03_entropy_value():
    """hour_entropy must match Shannon entropy over 24-hour histogram."""
    from datetime import datetime

    rec = RecordingEmbedder()
    # Create messages at distinct hours: 0:00, 6:00, 12:00, 18:00
    # Unix timestamps for 2023-11-14 at hours 0, 6, 12, 18 UTC
    base = 1700000000.0  # ~2023-11-14 22:13:20 UTC — hour 22
    # Force specific hours by choosing timestamps carefully
    # 2023-01-01 00:00:00 UTC = 1672531200
    # 2023-01-01 06:00:00 UTC = 1672531200 + 6*3600
    # 2023-01-01 12:00:00 UTC = 1672531200 + 12*3600
    # 2023-01-01 18:00:00 UTC = 1672531200 + 18*3600
    t0 = 1672531200.0
    timestamps = [t0, t0 + 6 * 3600, t0 + 12 * 3600, t0 + 18 * 3600]
    messages = [{"text": f"msg{i}", "ts": ts} for i, ts in enumerate(timestamps)]

    df = _make_single_account_df(messages=messages)
    feat = Stage2Extractor("botsim").extract(df, rec)

    # Expected: hours = [0, 6, 12, 18], uniform distribution -> entropy = log2(4) = 2.0
    hours = [datetime.utcfromtimestamp(t).hour for t in timestamps]
    counts = np.bincount(hours, minlength=24).astype(np.float64)
    probs = counts / counts.sum()
    nonzero = probs[probs > 0]
    expected_entropy = float(-np.sum(nonzero * np.log2(nonzero)))

    assert abs(feat[0, 394] - expected_entropy) < 1e-3, (
        f"hour_entropy mismatch: got {feat[0, 394]}, expected {expected_entropy}"
    )


# ---------------------------------------------------------------------------
# FEAT-04: Cross-message cosine similarity (indices 395, 396)
# ---------------------------------------------------------------------------

def test_feat04_default_zero():
    """cross_msg_sim_mean and near_dup_frac must be 0.0 for 0 or 1 message accounts."""
    rec = RecordingEmbedder()

    # 0-message account
    df0 = _make_single_account_df(messages=[])
    feat0 = Stage2Extractor("botsim").extract(df0, rec)
    assert feat0[0, 395] == 0.0, "cross_msg_sim_mean must be 0.0 for 0-message account"
    assert feat0[0, 396] == 0.0, "near_dup_frac must be 0.0 for 0-message account"

    # 1-message account
    df1 = _make_single_account_df(messages=[{"text": "only message", "ts": 1700000000.0}])
    feat1 = Stage2Extractor("botsim").extract(df1, rec)
    assert feat1[0, 395] == 0.0, "cross_msg_sim_mean must be 0.0 for 1-message account"
    assert feat1[0, 396] == 0.0, "near_dup_frac must be 0.0 for 1-message account"


def test_feat04_sim_mean():
    """cross_msg_sim_mean must equal mean of off-diagonal cosine similarities."""
    norm_emb = NormalizedFakeEmbedder()
    texts = ["message one", "message two", "message three"]
    messages = [{"text": t, "ts": float(1700000000 + i * 3600)} for i, t in enumerate(texts)]
    df = _make_single_account_df(messages=messages)

    feat = Stage2Extractor("botsim").extract(df, norm_emb)

    # Compute expected value manually using the same embedder
    emb = NormalizedFakeEmbedder().encode(texts)
    sim = emb @ emb.T
    n = sim.shape[0]
    mask = ~np.eye(n, dtype=bool)
    off_diag = sim[mask]
    expected = float(np.mean(off_diag))

    assert abs(feat[0, 395] - expected) < 1e-4, (
        f"cross_msg_sim_mean mismatch: got {feat[0, 395]}, expected {expected}"
    )


def test_feat04_near_dup():
    """near_dup_frac must equal fraction of off-diagonal similarities > 0.9."""
    norm_emb = NormalizedFakeEmbedder()
    texts = ["message one", "message two", "message three"]
    messages = [{"text": t, "ts": float(1700000000 + i * 3600)} for i, t in enumerate(texts)]
    df = _make_single_account_df(messages=messages)

    feat = Stage2Extractor("botsim").extract(df, norm_emb)

    # Compute expected value manually
    emb = NormalizedFakeEmbedder().encode(texts)
    sim = emb @ emb.T
    n = sim.shape[0]
    mask = ~np.eye(n, dtype=bool)
    off_diag = sim[mask]
    expected_frac = float(np.mean(off_diag > 0.9))

    assert abs(feat[0, 396] - expected_frac) < 1e-4, (
        f"near_dup_frac mismatch: got {feat[0, 396]}, expected {expected_frac}"
    )
