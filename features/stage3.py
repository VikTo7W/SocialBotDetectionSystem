from __future__ import annotations

import numpy as np
import pandas as pd

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

    X_all = np.stack(feats, axis=1)
    return X_all[node_ids]


class Stage3Extractor:
    def __init__(self, dataset: str) -> None:
        if dataset not in {"botsim", "twibot"}:
            raise ValueError(f"unknown dataset: {dataset!r}")
        self.dataset = dataset

    def extract(
        self,
        accounts_df: pd.DataFrame,
        edges_df: pd.DataFrame,
        num_nodes_total: int | None = None,
    ) -> np.ndarray:
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
