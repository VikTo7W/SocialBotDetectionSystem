from pathlib import Path
import os

import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split

from botsim24_io import load_users_csv, load_user_post_comment_json, build_account_table
from botdetector_pipeline import (
    Stage2LSTMRefiner,
    StageThresholds,
    TrainedSystem,
    apply_stage2b_refiner,
    build_graph_features_nodeidx,
    build_meta12_table,
    entropy_from_p,
    extract_message_embedding_sequences_for_accounts,
    gate_amr,
    gate_stage3,
    logit,
    oof_meta12_predictions,
    predict_system,
    sigmoid,
    train_meta12,
    train_meta123,
    train_system,
)
from calibrate import calibrate_thresholds, write_calibration_report_artifact
from evaluate import compare_stage2b_variants, evaluate_s3, write_stage2b_comparison_artifact
from features_stage1 import extract_stage1_matrix
from features_stage2 import extract_stage2_features

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")


def _load_pretrained_system_if_available(path: str = "trained_system.joblib"):
    artifact = Path(path)
    if not artifact.exists():
        return None
    print(f"[main] Loading pre-trained system from {artifact} for offline calibration/evaluation")
    return joblib.load(artifact)


def _load_any_pretrained_system(paths: list[str]):
    for path in paths:
        system = _load_pretrained_system_if_available(path)
        if system is not None:
            return system
    return None


def _variant_model_path(stage2b_variant: str) -> str:
    return f"trained_system_stage2b_{stage2b_variant}.joblib"


def _train_or_load_variant_system(
    *,
    stage2b_variant: str,
    S1: pd.DataFrame,
    S2: pd.DataFrame,
    edges_S1: pd.DataFrame,
    edges_S2: pd.DataFrame,
    th: StageThresholds,
    random_state: int,
    nodes_total: int,
):
    model_path = _variant_model_path(stage2b_variant)
    seed_system = _load_any_pretrained_system(
        [model_path, "trained_system.joblib", "trained_system_v12.joblib", "trained_system_v11.joblib"]
    )
    try:
        sys = train_system(
            S1=S1,
            S2=S2,
            edges_S1=edges_S1,
            edges_S2=edges_S2,
            cfg=None,
            th=th,
            random_state=random_state,
            nodes_total=nodes_total,
            stage2b_variant=stage2b_variant,
            embedder=None if seed_system is None else seed_system.embedder,
        )
    except Exception as exc:
        if stage2b_variant == "lstm" and seed_system is not None:
            print(f"[main] Full-cascade retrain unavailable for lstm, deriving variant from local baseline: {exc}")
            return _build_lstm_variant_from_seed_system(
                seed_system=seed_system,
                S1=S1,
                S2=S2,
                edges_S2=edges_S2,
                th=th,
                random_state=random_state,
                nodes_total=nodes_total,
            )
        fallback_paths = [model_path]
        if stage2b_variant == "amr":
            fallback_paths.extend(["trained_system.joblib", "trained_system_v12.joblib"])
        sys = _load_any_pretrained_system(fallback_paths)
        if sys is None:
            raise
        print(f"[main] Training unavailable for {stage2b_variant}, reusing {model_path}: {exc}")
    return sys


def _build_lstm_variant_from_seed_system(
    *,
    seed_system,
    S1: pd.DataFrame,
    S2: pd.DataFrame,
    edges_S2: pd.DataFrame,
    th: StageThresholds,
    random_state: int,
    nodes_total: int,
) -> TrainedSystem:
    cfg = getattr(seed_system, "cfg", None)
    embedder = seed_system.embedder

    y1_tr = S1["label"].to_numpy(dtype=np.int64)
    X1_tr = extract_stage1_matrix(S1)
    X2_tr = extract_stage2_features(S1, embedder)
    out2a_S1 = seed_system.stage2a.predict(X2_tr)
    sequences_S1, lengths_S1 = extract_message_embedding_sequences_for_accounts(S1, cfg, embedder)

    stage2b_lstm = Stage2LSTMRefiner(random_state=random_state)
    stage2b_lstm.fit(sequences_S1, lengths_S1, out2a_S1["z2a"], y1_tr)

    y2 = S2["label"].to_numpy(dtype=np.int64)
    X1_S2 = extract_stage1_matrix(S2)
    out1_S2 = seed_system.stage1.predict(X1_S2)
    X2_S2 = extract_stage2_features(S2, embedder)
    out2a_S2 = seed_system.stage2a.predict(X2_S2)

    stage2b_mask = gate_amr(out2a_S2["p2a"], out2a_S2["n2"], out1_S2["z1"], out2a_S2["z2a"], th)
    z2 = apply_stage2b_refiner(
        S2,
        cfg,
        embedder,
        out2a_S2["z2a"],
        stage2b_mask,
        stage2b_variant="lstm",
        stage2b_lstm=stage2b_lstm,
    )
    p2 = sigmoid(z2)
    out2_S2 = {
        "z2": z2,
        "p2": p2,
        "u2": entropy_from_p(p2),
        "n2": out2a_S2["n2"],
    }

    X_meta12_S2 = build_meta12_table(out1_S2, out2_S2, amr_used=stage2b_mask.astype(np.float32))
    p12_oof = oof_meta12_predictions(X_meta12_S2, y2, n_splits=5, random_state=random_state)
    meta12 = train_meta12(X_meta12_S2, y2)

    stage3_mask = gate_stage3(p12_oof, out1_S2["n1"], out2_S2["n2"], th)
    X3_S2 = build_graph_features_nodeidx(S2, edges_S2, nodes_total)
    out3_S2 = {
        "p3": np.full(len(S2), 0.5, dtype=np.float64),
        "z3": np.zeros(len(S2), dtype=np.float64),
        "n3": np.zeros(len(S2), dtype=np.float64),
    }
    if stage3_mask.any():
        pred3 = seed_system.stage3.predict(X3_S2[stage3_mask])
        out3_S2["p3"][stage3_mask] = pred3["p3"]
        out3_S2["z3"][stage3_mask] = pred3["z3"]
        out3_S2["n3"][stage3_mask] = pred3["n3"]

    X_meta123_S2 = pd.DataFrame(
        {
            "z12": logit(p12_oof),
            "z3": out3_S2["z3"],
            "stage3_used": stage3_mask.astype(np.float32),
            "n1": out1_S2["n1"],
            "n2": out2_S2["n2"],
            "n3": out3_S2["n3"],
        }
    )
    meta123 = train_meta123(X_meta123_S2, y2)

    return TrainedSystem(
        cfg=cfg,
        th=th,
        embedder=embedder,
        stage1=seed_system.stage1,
        stage2a=seed_system.stage2a,
        amr_refiner=seed_system.amr_refiner,
        meta12=meta12,
        stage3=seed_system.stage3,
        meta123=meta123,
        stage2b_lstm=stage2b_lstm,
        stage2b_variant="lstm",
    )


def filter_edges_for_split(edges_df: pd.DataFrame, node_ids: np.ndarray) -> pd.DataFrame:
    node_set = set(node_ids.tolist())
    m = edges_df["src"].isin(node_set) & edges_df["dst"].isin(node_set)
    return edges_df[m].reset_index(drop=True)

if __name__ == "__main__":
    SEED = 42
    COMPARISON_CALIBRATION_TRIALS = 8
    phase9_artifact = Path(
        ".planning/workstreams/calibration-fix/phases/"
        "09-validation-and-selection-evidence/09-real-run-calibration-report.json"
    )
    phase10_artifact = Path(
        ".planning/workstreams/stage2b-lstm-version/phases/"
        "10-evaluation-and-baseline-comparison/10-real-run-variant-comparison.json"
    )

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

    th = StageThresholds()

    # Disable Stage 3 routing safely (uncertain band always false + novelty never triggers)
    th.s12_human = 1.0
    th.s12_bot = 0.0
    th.novelty_force_stage3 = 1e9

    variant_reports = {}
    variant_systems = {}
    y_true = S3["label"].to_numpy()

    for stage2b_variant in ("amr", "lstm"):
        print(f"Training stage and combiner models for Stage 2b variant={stage2b_variant}")
        sys = _train_or_load_variant_system(
            stage2b_variant=stage2b_variant,
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
            random_state=SEED,
            nodes_total=len(users),
        )

        print(f"Calibrating novelty and confidence thresholds for variant={stage2b_variant}")
        calibrate_thresholds(
            system=sys,
            S2=S2,
            edges_S2=edges_S2,
            nodes_total=len(accounts),
            metric="f1",
            n_trials=COMPARISON_CALIBRATION_TRIALS,
            seed=SEED,
        )

        if stage2b_variant == "amr":
            summary = write_calibration_report_artifact(sys.calibration_report_, phase9_artifact)
            print(f"[main] Wrote calibration evidence artifact to {phase9_artifact}")
            print(
                "[main] Calibration winner summary: "
                f"trial={summary['selected_trial']['trial_number']}, "
                f"best_ties={summary['tie_analysis']['best_tie_count']}, "
                f"alternatives={len(summary['alternatives'])}"
            )

        print(f"Running {stage2b_variant} trained system on the test set")
        out = predict_system(sys, df=S3, edges_df=edges_S3, nodes_total=len(users))
        variant_reports[stage2b_variant] = evaluate_s3(out, y_true)
        variant_systems[stage2b_variant] = sys

        model_path = _variant_model_path(stage2b_variant)
        joblib.dump(sys, model_path)
        print(f"[main] Saved {stage2b_variant} TrainedSystem to {model_path}")

    comparison = compare_stage2b_variants(variant_reports)
    write_stage2b_comparison_artifact(comparison, phase10_artifact)
    print(f"[main] Wrote Stage 2b comparison artifact to {phase10_artifact}")
    print(
        "[main] Phase 10 recommendation: "
        f"{comparison['recommendation']['recommended_variant']} "
        f"({comparison['recommendation']['status']})"
    )

    amr_sys = variant_systems["amr"]
    joblib.dump(amr_sys, "trained_system.joblib")
    print("[main] Saved baseline TrainedSystem to trained_system.joblib")
    joblib.dump(amr_sys, "trained_system_v11.joblib")
    print("[main] Saved v1.1 TrainedSystem to trained_system_v11.joblib")
    joblib.dump(amr_sys, "trained_system_v12.joblib")
    print("[main] Saved v1.2 TrainedSystem to trained_system_v12.joblib")
