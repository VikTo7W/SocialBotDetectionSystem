"""
run_batch.py — Batch inference on a custom dataset using a trained system.

Load a trained system artifact such as `trained_system_botsim.joblib`, provide your own account
DataFrame, and get per-account bot probabilities.

Unlike the API (which takes one account at a time as JSON), this script
processes a whole dataset at once — useful for offline evaluation or
scoring a new corpus before deploying.

Usage:
    python run_batch.py                   # uses the built-in synthetic example
    python run_batch.py --csv my_data.csv # score accounts from a CSV file

Output:
    results.csv — one row per account with p_final, label (0=human, 1=bot),
                  and intermediate per-stage probabilities for inspection.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd

from botdetector_pipeline import predict_system, TrainedSystem

# ---------------------------------------------------------------------------
# DATASET STRUCTURE
# ---------------------------------------------------------------------------
# predict_system() expects a pandas DataFrame with these columns.
# Every column is required; use sensible defaults (0, "", []) if unknown.
#
# Column           Type        Description
# ─────────────────────────────────────────────────────────────────────────────
# account_id       str         Unique identifier for the account (any string)
# username         str         Display name / handle of the account
# profile          str         Bio / "about me" text — can be empty string ""
# subreddit_list   list[str]   Subreddits the account is active in, e.g.
#                              ["news", "politics"].  Use [] if unknown.
# submission_num   float       Total number of posts/submissions made
# comment_num      float       Total number of comments made
# comment_num_1    float       Number of first-level (direct) comments
# comment_num_2    float       Number of second-level (nested) comments
#                              If you only have total comments, set both
#                              comment_num_1 = comment_num and comment_num_2 = 0
# messages         list[dict]  Timeline of posts and comments.  Each dict must
#                              have at least a "text" key (str).  Additional
#                              keys recognised by Stage 2 features:
#                                "ts"       : float | None — Unix timestamp
#                                "kind"     : str — "post", "comment_1", etc.
#                                "subreddit": str | None
#                                "score"    : int | None — upvotes
#                              Sort by ts ascending (oldest first).
#                              If no posts/comments are available use [].
# ─────────────────────────────────────────────────────────────────────────────
# NOTE: "character_setting" (BotSim-24 specific) is intentionally excluded —
#       the model was trained without it and it is not used at inference time.


# ---------------------------------------------------------------------------
# EDGES DATAFRAME (Stage 3 graph features)
# ---------------------------------------------------------------------------
# predict_system() also needs an edges DataFrame describing relationships
# between accounts.  If you have no graph data, pass an empty DataFrame with
# the correct columns — Stage 3 will simply receive zero-degree features for
# all nodes (safe; the cascade will rely on Stage 1/2 outputs instead).
#
# Column        Type    Description
# ─────────────────────────────────────────────────────────────────────────────
# source        int     node_idx of the source account
# target        int     node_idx of the target account
# edge_type     int     Relationship type code (arbitrary integer)
# weight        float   Edge weight (e.g. interaction frequency)
# ─────────────────────────────────────────────────────────────────────────────
# The model maps each account to a node_idx.  When building from scratch:
#   df["node_idx"] = range(len(df))
# Then source/target in edges_df reference those indices.


EMPTY_EDGES = pd.DataFrame(
    columns=["source", "target", "edge_type", "weight"],
    dtype=float,
)


# ---------------------------------------------------------------------------
# SYNTHETIC EXAMPLE
# ---------------------------------------------------------------------------
# Replace this function (or the --csv path) with your own data loading logic.

def make_synthetic_dataset() -> pd.DataFrame:
    """
    Two synthetic accounts to verify the pipeline runs end-to-end.
    Replace this with real account data.
    """
    records = [
        {
            # ── Human-like account ──────────────────────────────────────────
            "account_id": "human_001",
            "username": "Alice_Thoughtful",
            "profile": "Graduate student interested in history and open-source.",
            # Subreddits as a Python list of strings:
            "subreddit_list": ["history", "linux", "science"],
            # Numeric metadata — fill from your data source:
            "submission_num": 12.0,
            "comment_num": 340.0,
            "comment_num_1": 280.0,
            "comment_num_2": 60.0,
            # Messages: list of dicts with at minimum a "text" key.
            # "ts" is a Unix timestamp (float); sort oldest-first.
            "messages": [
                {"text": "Really interesting article on Byzantine history.",
                 "ts": 1_700_000_000.0, "kind": "comment_1", "subreddit": "history"},
                {"text": "Just published my first open-source tool!",
                 "ts": 1_700_100_000.0, "kind": "post", "subreddit": "linux"},
            ],
        },
        {
            # ── Bot-like account ─────────────────────────────────────────────
            "account_id": "bot_001",
            "username": "NewsBot_9182736",
            # profile can be empty string — the model handles it:
            "profile": "",
            # Empty subreddit list is fine:
            "subreddit_list": [],
            "submission_num": 4200.0,
            "comment_num": 100.0,
            "comment_num_1": 100.0,
            "comment_num_2": 0.0,
            # No messages available — use an empty list:
            "messages": [],
        },
    ]

    df = pd.DataFrame(records)
    # node_idx is required by Stage 3's graph feature builder:
    df["node_idx"] = range(len(df))
    return df


# ---------------------------------------------------------------------------
# CSV LOADER
# ---------------------------------------------------------------------------

def load_from_csv(path: str) -> pd.DataFrame:
    """
    Load accounts from a flat CSV file.

    Expected CSV columns (see DATASET STRUCTURE above for details):
        account_id, username, profile,
        subreddit_list,     <- comma-separated string, e.g. "news,politics"
        submission_num, comment_num, comment_num_1, comment_num_2

    The "messages" column is optional.  If absent, every account gets an
    empty message list (Stage 2 will rely on profile/username only).

    If your CSV has different column names, rename them before calling
    predict_system() or adjust the mapping below.
    """
    df = pd.read_csv(path)
    df = df.copy()

    # ── account_id ──────────────────────────────────────────────────────────
    # Map whatever ID column you have to "account_id":
    if "account_id" not in df.columns:
        if "user_id" in df.columns:
            df["account_id"] = df["user_id"].astype(str)
        else:
            df["account_id"] = [f"account_{i}" for i in range(len(df))]
    df["account_id"] = df["account_id"].astype(str)

    # ── username ─────────────────────────────────────────────────────────────
    if "username" not in df.columns:
        # Try common alternatives:
        for alt in ["name", "handle", "screen_name"]:
            if alt in df.columns:
                df["username"] = df[alt].fillna("").astype(str)
                break
        else:
            df["username"] = ""

    # ── profile (bio text) ───────────────────────────────────────────────────
    if "profile" not in df.columns:
        for alt in ["description", "bio", "about"]:
            if alt in df.columns:
                df["profile"] = df[alt].fillna("").astype(str)
                break
        else:
            df["profile"] = ""
    # Ensure NaN profiles become empty strings (the model does not accept NaN):
    df["profile"] = df["profile"].fillna("").astype(str)

    # ── subreddit_list ───────────────────────────────────────────────────────
    # If stored as a comma-separated string, split it into a Python list:
    if "subreddit_list" not in df.columns:
        src = "subreddit" if "subreddit" in df.columns else None
        if src:
            df["subreddit_list"] = df[src].fillna("").apply(
                lambda x: [s.strip() for s in str(x).split(",") if s.strip()]
            )
        else:
            df["subreddit_list"] = [[] for _ in range(len(df))]
    else:
        # Column exists but may still be a string representation:
        def _parse_sr(x: Any) -> List[str]:
            if isinstance(x, list):
                return x
            if not x or (isinstance(x, float) and np.isnan(x)):
                return []
            return [s.strip() for s in str(x).split(",") if s.strip()]
        df["subreddit_list"] = df["subreddit_list"].apply(_parse_sr)

    # ── numeric counts ───────────────────────────────────────────────────────
    for col in ["submission_num", "comment_num", "comment_num_1", "comment_num_2"]:
        if col not in df.columns:
            # If you only have a total comment count, Stage 1 degrades gracefully:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0).astype(float)

    # ── messages ─────────────────────────────────────────────────────────────
    # The model uses posts/comments for Stage 2 (text + temporal features).
    # If your dataset has no text timeline, leave as empty list — the model
    # will still run using profile/username and numeric metadata alone.
    if "messages" not in df.columns:
        df["messages"] = [[] for _ in range(len(df))]

    # ── node_idx (Stage 3) ───────────────────────────────────────────────────
    # Assign consecutive integer indices used by the graph feature builder:
    if "node_idx" not in df.columns:
        df["node_idx"] = range(len(df))

    return df


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Batch bot detection inference")
    parser.add_argument(
        "--model", default="trained_system_botsim.joblib",
        help="Path to a trained system artifact (default: trained_system_botsim.joblib)"
    )
    parser.add_argument(
        "--csv", default=None,
        help="CSV file with account data (omit to use built-in synthetic example)"
    )
    parser.add_argument(
        "--threshold", type=float, default=None,
        help="Override the decision threshold for final label (default: use calibrated value)"
    )
    parser.add_argument(
        "--output", default="results.csv",
        help="Output CSV path (default: results.csv)"
    )
    args = parser.parse_args()

    # ── Load model ───────────────────────────────────────────────────────────
    model_path = Path(args.model)
    if not model_path.exists():
        print(f"ERROR: model file not found: {model_path}")
        print("Run train_botsim.py or train_twibot.py first to create a maintained model artifact.")
        sys.exit(1)

    print(f"Loading model from {model_path} ...")
    system: TrainedSystem = joblib.load(model_path)

    # ── Load data ────────────────────────────────────────────────────────────
    if args.csv:
        print(f"Loading accounts from {args.csv} ...")
        df = load_from_csv(args.csv)
    else:
        print("No --csv provided. Using synthetic example dataset.")
        df = make_synthetic_dataset()

    print(f"Accounts to score: {len(df)}")

    # ── Run inference ─────────────────────────────────────────────────────────
    # Stage 3 needs graph edges. Pass EMPTY_EDGES if you have no graph data.
    # To provide real edges:
    #   edges_df = pd.DataFrame({
    #       "source": [0, 1, ...],   # node_idx of source account
    #       "target": [1, 2, ...],   # node_idx of target account
    #       "edge_type": [0, 1, ...],
    #       "weight":    [1.0, ...],
    #   })
    print("Running cascade inference ...")
    results = predict_system(
        sys=system,
        df=df,
        edges_df=EMPTY_EDGES,
        nodes_total=len(df),
    )

    # ── Apply decision threshold ──────────────────────────────────────────────
    # The calibrated threshold is stored on the system object.
    # You can override it with --threshold if needed.
    threshold = args.threshold if args.threshold is not None else system.th.s3_final_bot
    results["label"] = (results["p_final"] >= threshold).astype(int)

    # ── Print summary ─────────────────────────────────────────────────────────
    n_bot = results["label"].sum()
    n_human = len(results) - n_bot
    print(f"\nResults (threshold={threshold:.3f}):")
    print(f"  Human : {n_human}")
    print(f"  Bot   : {n_bot}")
    print()
    print(results[["account_id", "p1", "p2", "p12", "p3", "p_final", "label",
                    "amr_used", "stage3_used"]].to_string(index=False))

    # ── Save ──────────────────────────────────────────────────────────────────
    results.to_csv(args.output, index=False)
    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
