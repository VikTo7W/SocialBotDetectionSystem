"""data_io.py — unified data loading for BotSim-24 and TwiBot-20.

All I/O logic lives here. botsim24_io.py and twibot20_io.py have been deleted.
"""

from __future__ import annotations

import ast
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# BotSim-24 I/O
# ---------------------------------------------------------------------------

DATETIME_FMT = "%Y-%m-%d %H:%M:%S"


def _to_unix_seconds(dt_str: str) -> Optional[float]:
    if not dt_str or not isinstance(dt_str, str):
        return None
    try:
        dt = datetime.strptime(dt_str, DATETIME_FMT).replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return None


def parse_subreddits(x: Any) -> List[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return [str(s).strip() for s in x if str(s).strip()]
    s = str(x).strip()
    if not s or s.lower() in {"nan", "none"}:
        return []
    if (s.startswith("[") and s.endswith("]")) or (s.startswith("(") and s.endswith(")")):
        try:
            v = ast.literal_eval(s)
            if isinstance(v, (list, tuple)):
                return [str(t).strip() for t in v if str(t).strip()]
        except Exception:
            pass
    if "," in s:
        return [t.strip() for t in s.split(",") if t.strip()]
    return [s]


def load_users_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path).copy()
    for col in ["submission_num", "comment_num", "comment_num_1", "comment_num_2"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(np.float32)
    n = len(df)
    df["label"] = 0
    if n >= 1907:
        df.loc[df.index >= 1907, "label"] = 1
    df["user_id"] = df["user_id"].astype(str)
    return df


def load_user_post_comment_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    return {str(k): v for k, v in obj.items()}


def build_account_table(users_df: pd.DataFrame, upc: Dict[str, Any]) -> pd.DataFrame:
    rows = []
    for _, u in users_df.iterrows():
        uid = str(u["user_id"])
        entry = upc.get(uid, {})
        posts = entry.get("posts", []) or []
        c1 = entry.get("comment_1", []) or []
        c2 = entry.get("comment_2", []) or []

        messages = []
        for p in posts:
            txt = (p.get("posts") or "").strip()
            ts = _to_unix_seconds(p.get("created_utc", ""))
            if txt:
                messages.append({
                    "text": txt, "ts": ts, "kind": "post",
                    "subreddit": p.get("subreddit"), "score": p.get("score"),
                    "upvote_ratio": p.get("upvote_ratio"), "num_comments": p.get("num_comments"),
                })
        for c in c1:
            txt = (c.get("comment_body") or "").strip()
            ts = _to_unix_seconds(c.get("created_utc", ""))
            if txt:
                messages.append({
                    "text": txt, "ts": ts, "kind": "comment_1",
                    "subreddit": c.get("subreddit"), "score": c.get("comment_score"),
                    "link_id": c.get("link_id"), "parent_id": c.get("parent_id"),
                    "level": c.get("level"),
                })
        for c in c2:
            txt = (c.get("comment_body") or "").strip()
            ts = _to_unix_seconds(c.get("created_utc", ""))
            if txt:
                messages.append({
                    "text": txt, "ts": ts, "kind": "comment_2",
                    "subreddit": c.get("subreddit"), "score": c.get("comment_score"),
                    "link_id": c.get("link_id"), "parent_id": c.get("parent_id"),
                    "level": c.get("level"),
                })

        messages = [m for m in messages if m.get("ts") is not None]
        messages.sort(key=lambda m: m["ts"])
        sr_list = parse_subreddits(u.get("subreddit"))

        rows.append({
            "account_id": uid,
            "label": int(u["label"]),
            "username": (u.get("name") or ""),
            "profile": (u.get("description") or ""),
            "subreddit_list": sr_list,
            "submission_num": float(u.get("submission_num", 0.0)),
            "comment_num": float(u.get("comment_num", 0.0)),
            "comment_num_1": float(u.get("comment_num_1", 0.0)),
            "comment_num_2": float(u.get("comment_num_2", 0.0)),
            "messages": messages,
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# TwiBot-20 I/O
# ---------------------------------------------------------------------------

_no_neighbor_count: int = 0
_UTF16_BOMS = (b"\xff\xfe", b"\xfe\xff")


def _detect_encoding(path: str) -> str:
    with open(path, "rb") as fb:
        header = fb.read(2)
    return "utf-16" if header in _UTF16_BOMS else "utf-8"


def load_accounts(path: str) -> pd.DataFrame:
    global _no_neighbor_count
    _no_neighbor_count = 0
    encoding = _detect_encoding(path)
    with open(path, "r", encoding=encoding) as f:
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
            "domain_list": [str(d).strip() for d in (record.get("domain") or []) if str(d).strip()],
            "label": int(record["label"]),
        })

    df = pd.DataFrame(rows)
    df["node_idx"] = df["node_idx"].astype(np.int32)
    return df


def build_edges(accounts_df: pd.DataFrame, path: str) -> pd.DataFrame:
    encoding = _detect_encoding(path)
    with open(path, "r", encoding=encoding) as f:
        data = json.load(f)

    id_to_idx = {record["ID"]: int(accounts_df.iloc[i]["node_idx"]) for i, record in enumerate(data)}
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
    required_cols = [
        "node_idx", "screen_name", "statuses_count", "followers_count",
        "friends_count", "created_at", "messages", "domain_list", "label",
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
    rt_count = mt_count = original_count = 0
    rt_mt_usernames: List[str] = []

    for msg in messages:
        text = msg["text"].strip()
        upper = text.upper()
        if upper.startswith("RT "):
            rt_count += 1
            tokens = text.split()
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
        "rt_mt_usernames": list(dict.fromkeys(rt_mt_usernames)),
    }


# ---------------------------------------------------------------------------
# Unified dataset loader
# ---------------------------------------------------------------------------

def load_dataset(dataset: str, **kwargs) -> Dict[str, Any]:
    if dataset == "botsim":
        return _load_botsim(**kwargs)
    if dataset == "twibot":
        return _load_twibot(**kwargs)
    raise ValueError(f"unknown dataset: {dataset!r}")


def _load_botsim(users_csv_path: str, upc_json_path: str) -> Dict[str, Any]:
    users_df = load_users_csv(users_csv_path)
    upc = load_user_post_comment_json(upc_json_path)
    accounts_df = build_account_table(users_df, upc)
    return {"accounts_df": accounts_df}


def _load_twibot(json_path: str, run_validate: bool = False) -> Dict[str, Any]:
    accounts_df = load_accounts(json_path)
    edges_df = build_edges(accounts_df, json_path)
    if run_validate:
        validate(accounts_df, edges_df)
    return {"accounts_df": accounts_df, "edges_df": edges_df}
