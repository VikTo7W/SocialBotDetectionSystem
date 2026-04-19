from __future__ import annotations

import os
from typing import Any

import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split

from botsim24_io import build_account_table, load_user_post_comment_json, load_users_csv
from calibrate import calibrate_thresholds
from cascade_pipeline import CascadePipeline, StageThresholds
from evaluate import evaluate_s3

SEED = 42
DEFAULT_BOTSIM_MODEL_PATH = "trained_system_botsim.joblib"
_PROTECTED_MODEL_ARTIFACTS = {
    "trained_system_twibot.joblib",
    "trained_system_twibot20.joblib",
    "trained_system_v11.joblib",
    "trained_system_v12.joblib",
    "trained_system_stage2b_amr.joblib",
    "trained_system_stage2b_lstm.joblib",
}

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")


def ensure_safe_model_output_path(path: str) -> str:
    basename = os.path.basename(path)
    if basename in _PROTECTED_MODEL_ARTIFACTS:
        raise ValueError(f"Refusing to overwrite protected model artifact: {basename}")
    return path


def filter_edges_for_split(edges_df: pd.DataFrame, node_ids: np.ndarray) -> pd.DataFrame:
    node_set = set(np.asarray(node_ids).tolist())
    mask = edges_df["src"].isin(node_set) & edges_df["dst"].isin(node_set)
    return edges_df[mask].reset_index(drop=True)


def load_botsim_accounts(
    users_path: str = "Users.csv",
    interactions_path: str = "user_post_comment.json",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    users = load_users_csv(users_path).copy()
    users["node_idx"] = np.arange(len(users), dtype=np.int32)
    users["user_id"] = users["user_id"].astype(str)
    upc = load_user_post_comment_json(interactions_path)
    accounts = build_account_table(users, upc)
    assert "character_setting" not in accounts.columns, (
        "character_setting must not appear in account table -- it is a target leak"
    )

    accounts["account_id"] = accounts["account_id"].astype(str)
    accounts = accounts.merge(
        users[["user_id", "node_idx"]],
        left_on="account_id",
        right_on="user_id",
        how="left",
    )
    accounts.drop(columns=["user_id"], inplace=True)
    assert accounts["node_idx"].isna().sum() == 0, "Some accounts have no node_idx mapping."
    accounts["node_idx"] = accounts["node_idx"].astype(np.int32)
    accounts = accounts.sample(frac=1.0, random_state=SEED).reset_index(drop=True)
    return users, accounts


def _tensor_to_numpy(value: Any) -> np.ndarray:
    if hasattr(value, "numpy"):
        return value.numpy()
    return np.asarray(value)


def load_botsim_edges(
    edge_index_path: str = "edge_index.pt",
    edge_type_path: str = "edge_type.pt",
    edge_weight_path: str = "edge_weight.pt",
) -> pd.DataFrame:
    edge_index = _tensor_to_numpy(torch.load(edge_index_path, map_location="cpu"))
    edge_type = _tensor_to_numpy(torch.load(edge_type_path, map_location="cpu"))
    edge_weight = _tensor_to_numpy(torch.load(edge_weight_path, map_location="cpu"))
    edge_weight = np.asarray(edge_weight, dtype=np.float32).reshape(-1)

    edges_df = pd.DataFrame(
        {
            "src": edge_index[:, 0].astype(np.int32),
            "dst": edge_index[:, 1].astype(np.int32),
            "etype": edge_type.astype(np.int8),
            "weight": edge_weight,
        }
    )
    edges_df["weight"] = np.log1p(edges_df["weight"])
    return edges_df


def split_train_accounts(
    accounts_df: pd.DataFrame,
    *,
    seed: int = SEED,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    S_temp, S3 = train_test_split(
        accounts_df,
        test_size=0.15,
        stratify=accounts_df["label"],
        shuffle=True,
        random_state=seed,
    )
    S1, S2 = train_test_split(
        S_temp,
        test_size=0.1765,
        stratify=S_temp["label"],
        shuffle=True,
        random_state=seed,
    )
    return S1.reset_index(drop=True), S2.reset_index(drop=True), S3.reset_index(drop=True)


def train_botsim(
    users_path: str = "Users.csv",
    interactions_path: str = "user_post_comment.json",
    edge_index_path: str = "edge_index.pt",
    edge_type_path: str = "edge_type.pt",
    edge_weight_path: str = "edge_weight.pt",
    model_output_path: str = DEFAULT_BOTSIM_MODEL_PATH,
    seed: int = SEED,
    calibrate_trials: int = 1,
) -> dict:
    _ = calibrate_trials
    model_output_path = ensure_safe_model_output_path(model_output_path)

    users, accounts = load_botsim_accounts(users_path, interactions_path)
    edges_df = load_botsim_edges(edge_index_path, edge_type_path, edge_weight_path)
    S1, S2, S3 = split_train_accounts(accounts, seed=seed)

    edges_S1 = filter_edges_for_split(edges_df, S1["node_idx"].to_numpy())
    edges_S2 = filter_edges_for_split(edges_df, S2["node_idx"].to_numpy())
    edges_S3 = filter_edges_for_split(edges_df, S3["node_idx"].to_numpy())

    th = StageThresholds()
    th.s12_human = 1.0
    th.s12_bot = 0.0
    th.novelty_force_stage3 = 1e9

    pipeline = CascadePipeline("botsim", random_state=seed)
    system = pipeline.fit(
        S1=S1,
        S2=S2,
        edges_S1=edges_S1,
        edges_S2=edges_S2,
        th=StageThresholds(
            s1_bot=th.s1_bot,
            s1_human=th.s1_human,
            n1_max_for_exit=th.n1_max_for_exit,
            s2a_bot=th.s2a_bot,
            s2a_human=th.s2a_human,
            n2_trigger=th.n2_trigger,
            disagreement_trigger=th.disagreement_trigger,
            s12_bot=th.s12_bot,
            s12_human=th.s12_human,
            novelty_force_stage3=th.novelty_force_stage3,
        ),
        nodes_total=len(users),
    )

    calibrate_thresholds(
        system=system,
        S2=S2,
        edges_S2=edges_S2,
        nodes_total=len(accounts),
        metric="f1",
        n_trials=1,
        seed=seed,
    )

    results = pipeline.predict(system, df=S3, edges_df=edges_S3, nodes_total=len(users))
    metrics = evaluate_s3(results, S3["label"].to_numpy(), verbose=False)

    joblib.dump(system, model_output_path)
    return {
        "system": system,
        "metrics": metrics,
        "results": results,
        "paths": {"model": model_output_path},
        "splits": {
            "users": users_path,
            "interactions": interactions_path,
            "s1_size": len(S1),
            "s2_size": len(S2),
            "s3_size": len(S3),
        },
    }


if __name__ == "__main__":
    summary = train_botsim()
    print(f"[botsim] model: {summary['paths']['model']}")
    print(
        f"[botsim] s1/s2/s3: "
        f"{summary['splits']['s1_size']}/"
        f"{summary['splits']['s2_size']}/"
        f"{summary['splits']['s3_size']}"
    )
