"""
Shared pytest fixtures for bot detection system tests.

Provides:
    minimal_system: returns (TrainedSystem, S2, edges_S2, nodes_total)
    Uses only synthetic data — does NOT load real BotSim-24 data or sentence-transformers.
"""

import os

import numpy as np
import pandas as pd
import pytest

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import botdetector_pipeline as bp
from botdetector_pipeline import (
    TrainedSystem,
    StageThresholds,
    FeatureConfig,
    Stage1MetadataModel,
    Stage2BaseContentModel,
    AMRDeltaRefiner,
    Stage3StructuralModel,
    train_meta12,
    train_meta123,
    build_meta12_table,
    build_graph_features_nodeidx,
    gate_amr,
    gate_stage3,
    oof_meta12_predictions,
    logit,
    sigmoid,
    entropy_from_p,
)
from features.stage1 import Stage1Extractor
from features.stage2 import Stage2Extractor


class FakeEmbedder:
    """
    Deterministic fake embedder that avoids loading the sentence-transformers model.
    Returns random 384-dimensional float32 vectors matching MiniLM output dimension.
    """

    def encode(self, texts, batch_size: int = 64) -> np.ndarray:
        rng = np.random.RandomState(42)
        return rng.randn(len(texts), 384).astype(np.float32)


class NormalizedFakeEmbedder:
    """
    Deterministic fake embedder that returns L2-normalized 384-dim vectors.
    Required for FEAT-04 value tests where cosine similarity must be valid
    (i.e. emb @ emb.T gives true cosine similarities only for unit vectors).
    """

    def encode(self, texts, batch_size: int = 64) -> np.ndarray:
        rng = np.random.RandomState(42)
        raw = rng.randn(len(texts), 384).astype(np.float32)
        norms = np.linalg.norm(raw, axis=1, keepdims=True)
        return raw / np.maximum(norms, 1e-8)


def _make_synthetic_dataframe(rng: np.random.RandomState) -> pd.DataFrame:
    """Build a 50-account synthetic DataFrame with all required columns."""
    n = 50
    account_ids = [f"acc_{i}" for i in range(n)]
    node_idxs = list(range(n))
    labels = [0] * 25 + [1] * 25

    usernames = ["".join(rng.choice(list("abcdefghijklmnopqrstuvwxyz"), 5)) for _ in range(n)]
    submission_nums = rng.randint(0, 100, size=n).tolist()
    comment_num_1s = rng.randint(0, 50, size=n).tolist()
    comment_num_2s = rng.randint(0, 50, size=n).tolist()

    subreddit_lists = [
        [f"sub_{rng.randint(0, 20)}" for _ in range(rng.randint(1, 6))]
        for _ in range(n)
    ]

    profiles = [f"user profile {i}" for i in range(n)]

    messages_list = []
    for i in range(n):
        n_msgs = rng.randint(3, 6)
        msgs = [
            {"text": f"sample message text {j} for account {i}", "ts": float(1700000000 + j * 3600)}
            for j in range(n_msgs)
        ]
        messages_list.append(msgs)

    df = pd.DataFrame({
        "account_id": account_ids,
        "node_idx": node_idxs,
        "label": labels,
        "username": usernames,
        "submission_num": submission_nums,
        "comment_num_1": comment_num_1s,
        "comment_num_2": comment_num_2s,
        "subreddit_list": subreddit_lists,
        "profile": profiles,
        "messages": messages_list,
    })
    return df


def _make_synthetic_edges(rng: np.random.RandomState, n_nodes: int = 50) -> pd.DataFrame:
    """Build a synthetic edge DataFrame with 100 random edges."""
    n_edges = 100
    src = rng.randint(0, n_nodes, size=n_edges)
    dst = rng.randint(0, n_nodes, size=n_edges)
    weight = np.ones(n_edges, dtype=np.float32)
    etype = rng.randint(0, 3, size=n_edges)

    return pd.DataFrame({
        "src": src,
        "dst": dst,
        "weight": weight,
        "etype": etype,
    })


@pytest.fixture
def minimal_system():
    """
    Build a minimal TrainedSystem from 50-account synthetic data.

    Returns:
        (system, S2, edges_S2, nodes_total)
        system      -- TrainedSystem with all stage models fitted on synthetic data
        S2          -- pd.DataFrame with 50 synthetic accounts
        edges_S2    -- pd.DataFrame with 100 synthetic edges
        nodes_total -- int = 50

    Notes:
        - Uses FakeEmbedder to avoid loading sentence-transformers (90MB model)
        - All random data generated with np.random.RandomState(42)
    """
    rng = np.random.RandomState(42)
    fake_embedder = FakeEmbedder()
    nodes_total = 50

    # Build synthetic data
    S2 = _make_synthetic_dataframe(rng)
    edges_S2 = _make_synthetic_edges(rng, n_nodes=nodes_total)
    y = S2["label"].to_numpy(dtype=np.int64)

    # ---- Extract features using real functions (not patched versions) ----
    X1 = Stage1Extractor("botsim").extract(S2)
    X2 = Stage2Extractor("botsim").extract(S2, fake_embedder)

    # ---- Fit Stage1MetadataModel ----
    stage1 = Stage1MetadataModel(use_isotonic=False, random_state=42)
    stage1.fit(X1, y)
    out1 = stage1.predict(X1)

    # ---- Fit Stage2BaseContentModel ----
    stage2a = Stage2BaseContentModel(use_isotonic=False, random_state=42)
    stage2a.fit(X2, y)
    out2a = stage2a.predict(X2)

    # ---- Fit AMRDeltaRefiner ----
    # Use stage2a logits as z_base; AMR embeddings from most-recent message text
    from botdetector_pipeline import extract_amr_embeddings_for_accounts
    H_amr = extract_amr_embeddings_for_accounts(S2, FeatureConfig(stage1_numeric_cols=[]), fake_embedder)
    z2a = out2a["z2a"]

    amr_refiner = AMRDeltaRefiner(lr=0.05, epochs=100, l2=1e-3, random_state=42)
    amr_refiner.fit(H_amr, z2a, y)

    # ---- Build graph features and fit Stage3StructuralModel ----
    X3 = build_graph_features_nodeidx(S2, edges_S2, nodes_total)
    stage3 = Stage3StructuralModel(use_isotonic=False, random_state=42)
    stage3.fit(X3, y)

    # ---- Build meta12 table ----
    # Compute refined logits (use z2a as z2 since amr is optional here)
    th_default = StageThresholds()
    amr_mask = gate_amr(out2a["p2a"], out2a["n2"], out1["z1"], out2a["z2a"], th_default)

    z2 = out2a["z2a"].astype(np.float64).copy()
    if amr_mask.any():
        z2[amr_mask] = amr_refiner.refine(z2[amr_mask], H_amr[amr_mask])

    p2 = sigmoid(z2)
    out2 = {
        "z2": z2,
        "p2": p2,
        "u2": entropy_from_p(p2),
        "n2": out2a["n2"],
    }

    X_meta12 = build_meta12_table(out1, out2, amr_used=amr_mask.astype(np.float32))

    # OOF predictions for clean meta123 training
    p12_oof = oof_meta12_predictions(X_meta12, y, n_splits=5, random_state=42)

    # Train final meta12 on all data
    meta12 = train_meta12(X_meta12, y)

    # ---- Stage3 routing ----
    stage3_mask = gate_stage3(p12_oof, out1["n1"], out2["n2"], th_default)

    out3 = {
        "p3": np.full(nodes_total, 0.5, dtype=np.float64),
        "z3": np.zeros(nodes_total, dtype=np.float64),
        "n3": np.zeros(nodes_total, dtype=np.float64),
    }
    if stage3_mask.any():
        pred3 = stage3.predict(X3[stage3_mask])
        out3["p3"][stage3_mask] = pred3["p3"]
        out3["z3"][stage3_mask] = pred3["z3"]
        out3["n3"][stage3_mask] = pred3["n3"]

    # ---- Build meta123 table ----
    X_meta123 = pd.DataFrame({
        "z12": logit(p12_oof),
        "z3": out3["z3"],
        "stage3_used": stage3_mask.astype(np.float32),
        "n1": out1["n1"],
        "n2": out2["n2"],
        "n3": out3["n3"],
    })
    meta123 = train_meta123(X_meta123, y)

    # ---- Assemble TrainedSystem ----
    system = TrainedSystem(
        cfg=FeatureConfig(stage1_numeric_cols=[]),
        th=StageThresholds(),
        embedder=fake_embedder,
        stage1=stage1,
        stage2a=stage2a,
        amr_refiner=amr_refiner,
        meta12=meta12,
        stage3=stage3,
        meta123=meta123,
    )

    return (system, S2, edges_S2, nodes_total)
@pytest.fixture
def synthetic_training_split():
    """
    Deterministic synthetic S1/S2 split for end-to-end train_system tests.
    """
    rng = np.random.RandomState(7)
    nodes_total = 50
    S1 = _make_synthetic_dataframe(rng)
    S2 = _make_synthetic_dataframe(rng)
    edges_S1 = _make_synthetic_edges(rng, n_nodes=nodes_total)
    edges_S2 = _make_synthetic_edges(rng, n_nodes=nodes_total)
    return {
        "S1": S1,
        "S2": S2,
        "edges_S1": edges_S1,
        "edges_S2": edges_S2,
        "cfg": FeatureConfig(stage1_numeric_cols=[], max_messages_per_account=4),
        "th": StageThresholds(),
        "nodes_total": nodes_total,
    }
