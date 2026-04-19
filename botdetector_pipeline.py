"""
botdetector_pipeline.py -- compatibility shim.

All maintained orchestration code has moved to cascade_pipeline.py.
This module re-exports everything that active callers still import from here
so that existing import sites continue to work without modification.

Do NOT add new pipeline logic here. New code belongs in cascade_pipeline.py.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Re-export the full maintained surface from cascade_pipeline
# ---------------------------------------------------------------------------
from cascade_pipeline import (
    # math helpers
    sigmoid,
    logit,
    entropy_from_p,
    # novelty
    MahalanobisNovelty,
    # contract types
    FeatureConfig,
    StageThresholds,
    TextEmbedder,
    TrainedSystem,
    # stage models
    Stage1MetadataModel,
    Stage2BaseContentModel,
    AMRDeltaRefiner,
    Stage3StructuralModel,
    # routing
    gate_amr,
    gate_stage3,
    # meta-model helpers
    build_meta12_table,
    oof_meta12_predictions,
    train_meta12,
    train_meta123,
    # dataset inference
    infer_dataset,
    # orchestrator
    CascadePipeline,
)

# re-export build_graph_features_nodeidx for callers that still import it here
from features.stage3 import build_graph_features_nodeidx  # noqa: F401

# legacy stubs kept for compatibility with the old preprocessing path
from features_stage1 import extract_stage1_matrix  # noqa: F401
from features_stage2 import extract_stage2_features  # noqa: F401


# ---------------------------------------------------------------------------
# AMR embedding helper (used by conftest.py and legacy callers)
# ---------------------------------------------------------------------------

def amr_linearize_stub(text: str) -> str:
    """Replace with actual AMR parsing + linearization. Stub returns original text."""
    return text


def extract_amr_embeddings_for_accounts(
    df: pd.DataFrame,
    cfg: FeatureConfig,
    embedder: TextEmbedder,
) -> np.ndarray:
    from features.stage2 import Stage2Extractor

    dataset = infer_dataset(df, cfg)
    max_chars = cfg.max_chars_per_message if cfg is not None else 500
    return Stage2Extractor(dataset).extract_amr(df, embedder, max_chars=max_chars)


# ---------------------------------------------------------------------------
# simple_linguistic_features -- kept here for any callers that imported it
# ---------------------------------------------------------------------------

def simple_linguistic_features(text: str) -> np.ndarray:
    """Cheap linguistic features: length, unique token ratio, punct ratio, digit ratio."""
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


# ---------------------------------------------------------------------------
# Compatibility wrappers -- forwarding only; implementation lives in CascadePipeline
# ---------------------------------------------------------------------------

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
    """Compatibility wrapper. Delegates to CascadePipeline.fit()."""
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
    """Compatibility wrapper. Delegates to CascadePipeline.predict()."""
    from cascade_pipeline import CascadePipeline, infer_dataset

    dataset = infer_dataset(df, sys.cfg)
    pipeline = CascadePipeline(dataset=dataset, cfg=sys.cfg, embedder=sys.embedder)
    return pipeline.predict(sys, df, edges_df, nodes_total=nodes_total)
