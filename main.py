import json
import os

import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split

from botsim24_io import load_users_csv, load_user_post_comment_json, build_account_table
from botdetector_pipeline import StageThresholds, train_system, predict_system
from calibrate import calibrate_thresholds
from evaluate import evaluate_s3

def filter_edges_for_split(edges_df: pd.DataFrame, node_ids: np.ndarray) -> pd.DataFrame:
    node_set = set(node_ids.tolist())
    m = edges_df["src"].isin(node_set) & edges_df["dst"].isin(node_set)
    return edges_df[m].reset_index(drop=True)

if __name__ == "__main__":
    SEED = 42

    # 1) Load BotSim-24
    users = load_users_csv("Users.csv")
    users["node_idx"] = np.arange(len(users), dtype=np.int32)
    users["user_id"] = users["user_id"].astype(str)
    upc = load_user_post_comment_json("user_post_comment.json")
    accounts = build_account_table(users, upc)
    assert "character_setting" not in accounts.columns, (
        "character_setting must not appear in account table -- it is a target leak"
    )

    accounts["account_id"] = accounts["account_id"].astype(str)
    accounts = accounts.merge(users[["user_id", "node_idx"]], left_on="account_id", right_on="user_id", how="left")
    accounts.drop(columns=["user_id"], inplace=True)

    assert accounts["node_idx"].isna().sum() == 0, "Some accounts have no node_idx mapping."
    accounts["node_idx"] = accounts["node_idx"].astype(np.int32)

    # IMPORTANT:
    # Users.csv is NOT shuffled; first 1907 are humans, last 1000 are bots :contentReference[oaicite:1]{index=1}
    # So always stratify + shuffle before splitting.
    accounts = accounts.sample(frac=1.0, random_state=SEED).reset_index(drop=True)

    # (Optional sanity check)
    print(accounts["label"].value_counts())

    # 2) Create S1 (stage training), S2 (meta training), S3 (final test)
    # Example split: 70% / 15% / 15%
    S_temp, S3 = train_test_split(
        accounts,
        test_size=0.15,
        stratify=accounts["label"],
        shuffle=True,
        random_state=SEED,
    )
    S1, S2 = train_test_split(
        S_temp,
        test_size=0.1765,  # 0.1765 * 0.85 ~= 0.15 overall
        stratify=S_temp["label"],
        shuffle=True,
        random_state=SEED,
    )

    print("S1:", len(S1), "S2:", len(S2), "S3:", len(S3))

    # 3) Edges: until you confirm .pt coverage + mapping, run with Stage3 disabled OR with dummy edges.
    #    You likely have .pt edge files somewhere; but you said you’re not sure if they’re full graph.
    #    For now, pass empty edges and disable Stage 3 routing to debug Stages 1–2 cleanly.

    edge_index = torch.load("edge_index.pt", map_location="cpu").numpy()  # (E,2)
    edge_type = torch.load("edge_type.pt", map_location="cpu").numpy()  # (E,)
    edge_w = torch.load("edge_weight.pt", map_location="cpu").numpy()  # (E,1)

    edge_w = edge_w.reshape(-1).astype(np.float32)  # (E,)

    edges_df = pd.DataFrame({
        "src": edge_index[:, 0].astype(np.int32),
        "dst": edge_index[:, 1].astype(np.int32),
        "etype": edge_type.astype(np.int8),
        "weight": edge_w,
    })

    # Optional but recommended: stabilize heavy-tail weights
    edges_df["weight"] = np.log1p(edges_df["weight"])

    edges_S1 = filter_edges_for_split(edges_df, S1["node_idx"].to_numpy())
    edges_S2 = filter_edges_for_split(edges_df, S2["node_idx"].to_numpy())
    edges_S3 = filter_edges_for_split(edges_df, S3["node_idx"].to_numpy())

    # ---- Capture v1.0 S3 metrics before any code changes ----
    if os.path.exists("trained_system.joblib") and not os.path.exists("results_v10.json"):
        print("[main] Capturing v1.0 baseline metrics on S3...")
        sys_v10 = joblib.load("trained_system.joblib")
        out_v10 = predict_system(sys_v10, df=S3, edges_df=edges_S3, nodes_total=len(users))
        y_true_v10 = S3["label"].to_numpy()
        report_v10 = evaluate_s3(out_v10, y_true_v10)
        results_v10 = {
            "auc": report_v10["overall"]["auc"],
            "f1": report_v10["overall"]["f1"],
            "precision": report_v10["overall"]["precision"],
            "recall": report_v10["overall"]["recall"],
            "stage": "S3",
        }
        with open("results_v10.json", "w") as f:
            json.dump(results_v10, f, indent=2)
        print(f"[main] v1.0 metrics saved to results_v10.json: {results_v10}")
        del sys_v10, out_v10, y_true_v10, report_v10

    th = StageThresholds()

    # Disable Stage 3 routing safely (uncertain band always false + novelty never triggers)
    th.s12_human = 1.0
    th.s12_bot = 0.0
    th.novelty_force_stage3 = 1e9

    print("Training stage and combiner models")
    # 4) Train the system (Stages trained on S1; meta models trained on S2 with OOF meta12 internally)
    sys = train_system(
        S1=S1,
        S2=S2,
        edges_S1=edges_S1,
        edges_S2=edges_S2,
        cfg=None,  # if your updated train_system no longer needs cfg for stage1 columns
        th=th,
        random_state=SEED,
        nodes_total=len(users),
    )

    print("Calibrating novelty and confidence thresholds")
    # --- Threshold Calibration on S2 ---
    best_th = calibrate_thresholds(
        system=sys,
        S2=S2,
        edges_S2=edges_S2,
        nodes_total=len(accounts),
        metric="f1",
        n_trials=100,
        seed=SEED,
    )
    # sys.th is now updated; predict_system() will use calibrated thresholds

    print("Running trained system on the test set")
    # 5) Final evaluation on S3
    out = predict_system(sys, df=S3, edges_df=edges_S3, nodes_total=len(users))
    y_true = S3["label"].to_numpy()
    report = evaluate_s3(out, y_true)
    joblib.dump(sys, "trained_system.joblib")
    print(f"[main] Saved TrainedSystem to trained_system.joblib")
    joblib.dump(sys, "trained_system_v11.joblib")
    print(f"[main] Saved v1.1 TrainedSystem to trained_system_v11.joblib")