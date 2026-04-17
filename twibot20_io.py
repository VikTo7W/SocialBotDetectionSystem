"""TwiBot-20 data loader for cross-dataset evaluation (Phase 8)."""

from __future__ import annotations

import json
from typing import Any, Dict, List

import numpy as np
import pandas as pd

_no_neighbor_count: int = 0


def load_accounts(path: str) -> pd.DataFrame:
    """Load TwiBot-20 accounts from a JSON file into a BotSim-24-compatible DataFrame.

    Parameters
    ----------
    path : str
        Path to the TwiBot-20 JSON file (e.g., test.json).

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: node_idx (int32), screen_name, statuses_count,
        followers_count, friends_count, created_at, messages, label (int).
    """
    global _no_neighbor_count
    _no_neighbor_count = 0

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows: List[Dict[str, Any]] = []
    for idx, record in enumerate(data):
        profile = record["profile"]
        tweets = record.get("tweet") or []
        messages = [{"text": str(t), "ts": None, "kind": "tweet"} for t in tweets if t]
        if record.get("neighbor") is None:
            _no_neighbor_count += 1
        rows.append({
            "node_idx": np.int32(idx),
            "screen_name": str(profile.get("screen_name", "") or "").strip(),
            "statuses_count": int(str(profile.get("statuses_count", 0) or 0).strip() or 0),
            "followers_count": int(str(profile.get("followers_count", 0) or 0).strip() or 0),
            "friends_count": int(str(profile.get("friends_count", 0) or 0).strip() or 0),
            "created_at": str(profile.get("created_at", "") or "").strip(),
            "messages": messages,
            "label": int(record["label"]),
        })

    df = pd.DataFrame(rows)
    df["node_idx"] = df["node_idx"].astype(np.int32)
    return df


def build_edges(accounts_df: pd.DataFrame, path: str) -> pd.DataFrame:
    """Build an edges DataFrame from TwiBot-20 neighbor lists.

    Parameters
    ----------
    accounts_df : pd.DataFrame
        Output of load_accounts(); provides the node_idx mapping.
    path : str
        Path to the same TwiBot-20 JSON file used in load_accounts().

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: src (int32), dst (int32), etype (int8), weight (float32).
        following edges: etype=0, follower edges: etype=1.
        Weight is log1p(1.0) for all edges.
        Cross-set IDs (not in the evaluation file) are silently dropped.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Build lookup: Twitter string ID -> node_idx
    id_to_idx = {
        record["ID"]: int(accounts_df.iloc[i]["node_idx"])
        for i, record in enumerate(data)
    }

    WEIGHT = np.float32(np.log1p(1.0))
    rows = []
    for i, record in enumerate(data):
        neighbor = record.get("neighbor")
        if neighbor is None:
            continue
        src_idx = int(accounts_df.iloc[i]["node_idx"])
        for nid in (neighbor.get("following") or []):
            if nid in id_to_idx:
                rows.append((src_idx, id_to_idx[nid], 0, WEIGHT))
        for nid in (neighbor.get("follower") or []):
            if nid in id_to_idx:
                rows.append((id_to_idx[nid], src_idx, 1, WEIGHT))

    if rows:
        srcs, dsts, etypes, weights = zip(*rows)
    else:
        srcs, dsts, etypes, weights = [], [], [], []

    return pd.DataFrame({
        "src": np.array(srcs, dtype=np.int32),
        "dst": np.array(dsts, dtype=np.int32),
        "etype": np.array(etypes, dtype=np.int8),
        "weight": np.array(weights, dtype=np.float32),
    })


def validate(accounts_df: pd.DataFrame, edges_df: pd.DataFrame) -> None:
    """Validate data integrity of loaded TwiBot-20 accounts and edges.

    Parameters
    ----------
    accounts_df : pd.DataFrame
        Output of load_accounts().
    edges_df : pd.DataFrame
        Output of build_edges().

    Raises
    ------
    AssertionError
        If required columns are missing or edge indices are out of bounds.
    """
    required_cols = [
        "node_idx", "screen_name", "statuses_count", "followers_count",
        "friends_count", "created_at", "messages", "label",
    ]
    missing = [c for c in required_cols if c not in accounts_df.columns]
    assert not missing, f"Missing columns: {missing}"

    global _no_neighbor_count
    n = len(accounts_df)
    if len(edges_df) > 0:
        assert int(edges_df["src"].max()) < n, "src index out of bounds"
        assert int(edges_df["dst"].max()) < n, "dst index out of bounds"

    no_tweet_frac = sum(1 for m in accounts_df["messages"] if len(m) == 0) / n
    no_neighbor_frac = _no_neighbor_count / n if n > 0 else 0.0

    print(f"[twibot20] accounts: {n}, edges: {len(edges_df)}")
    print(f"[twibot20] no-neighbor fraction: {no_neighbor_frac:.3f}")
    print(f"[twibot20] no-tweet fraction: {no_tweet_frac:.3f}")


def parse_tweet_types(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Classify an account's tweets into RT, MT, and original buckets.

    Classifies each tweet by a case-insensitive prefix check (D-01, D-03):
    - "RT ..." -> retweet
    - "MT ..." -> modified tweet
    - anything else -> original tweet

    Extracts the first space-delimited token starting with "@" from RT/MT tweets
    as the retweeted/quoted account handle (D-02). Deduplicates handles while
    preserving insertion order.

    Args:
        messages: List of {"text": str, "ts": None, "kind": "tweet"} dicts
            as returned by load_accounts().

    Returns:
        Dict with keys:
            rt_count (int): number of retweets.
            mt_count (int): number of modified tweets.
            original_count (int): number of original tweets.
            rt_mt_usernames (list[str]): distinct lowercase @-handles (without
                the "@" prefix) extracted from RT/MT tweets, in order of first
                appearance.
    """
    rt_count = 0
    mt_count = 0
    original_count = 0
    rt_mt_usernames: List[str] = []

    for msg in messages:
        text = msg["text"].strip()
        upper = text.upper()
        if upper.startswith("RT "):
            rt_count += 1
            tokens = text.split()
            # tokens[0] is "RT"; tokens[1] should be "@handle" or "@handle:"
            if len(tokens) > 1 and tokens[1].startswith("@"):
                rt_mt_usernames.append(tokens[1].lstrip("@").rstrip(":").lower())
        elif upper.startswith("MT "):
            mt_count += 1
            tokens = text.split()
            if len(tokens) > 1 and tokens[1].startswith("@"):
                rt_mt_usernames.append(tokens[1].lstrip("@").rstrip(":").lower())
        else:
            original_count += 1

    return {
        "rt_count": rt_count,
        "mt_count": mt_count,
        "original_count": original_count,
        # dict.fromkeys deduplicates while preserving insertion order (Python 3.7+)
        "rt_mt_usernames": list(dict.fromkeys(rt_mt_usernames)),
    }
