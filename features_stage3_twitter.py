from __future__ import annotations

import numpy as np
import pandas as pd

from botdetector_pipeline import build_graph_features_nodeidx

STAGE3_TWITTER_COLUMNS = [
    "in_deg",
    "out_deg",
    "deg_total",
    "in_w",
    "out_w",
    "w_total",
    "following_in_deg",
    "following_out_deg",
    "following_in_w",
    "following_out_w",
    "follower_in_deg",
    "follower_out_deg",
    "follower_in_w",
    "follower_out_w",
    "type2_in_deg",
    "type2_out_deg",
    "type2_in_w",
    "type2_out_w",
]

TWITTER_NATIVE_EDGE_TYPES = {
    0: "following",
    1: "follower",
}


def extract_stage3_features_twitter(
    accounts_df: pd.DataFrame,
    edges_df: pd.DataFrame,
    num_nodes_total: int | None = None,
) -> np.ndarray:
    """
    TwiBot-native Stage 3 wrapper around the shared graph builder.

    Contract:
    - output shape is ``[len(accounts_df), 18]``
    - edge types 0 and 1 are TwiBot-native (following, follower)
    - the final 4-dim type-2 block is retained for contract stability and is
      expected to remain zero when TwiBot edges only use types 0 and 1
    """
    if num_nodes_total is None:
        if len(accounts_df) == 0:
            num_nodes_total = 0
        else:
            num_nodes_total = int(accounts_df["node_idx"].max()) + 1

    X = build_graph_features_nodeidx(
        accounts_df=accounts_df,
        edges_df=edges_df,
        num_nodes_total=num_nodes_total,
        n_types=3,
    )
    return np.asarray(X, dtype=np.float32)
