
from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd


DATETIME_FMT = "%Y-%m-%d %H:%M:%S"  # matches README examples for created_utc


def _to_unix_seconds(dt_str: str) -> Optional[float]:
    if not dt_str or not isinstance(dt_str, str):
        return None
    try:
        # Treat as UTC (dataset uses created_utc strings)
        dt = datetime.strptime(dt_str, DATETIME_FMT).replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return None


def parse_subreddits(x: Any) -> List[str]:
    """
    README says Users.csv has a 'subreddit' column describing communities participated in. :contentReference[oaicite:3]{index=3}
    Format isn't specified, so we handle:
      - JSON-like lists: "['news','politics']"
      - comma-separated: "news,politics"
      - single string: "news"
      - missing -> []
    """
    if x is None:
        return []
    if isinstance(x, list):
        return [str(s).strip() for s in x if str(s).strip()]
    s = str(x).strip()
    if not s or s.lower() in {"nan", "none"}:
        return []
    # Try list literal
    if (s.startswith("[") and s.endswith("]")) or (s.startswith("(") and s.endswith(")")):
        try:
            v = ast.literal_eval(s)
            if isinstance(v, (list, tuple)):
                return [str(t).strip() for t in v if str(t).strip()]
        except Exception:
            pass
    # Split by comma
    if "," in s:
        return [t.strip() for t in s.split(",") if t.strip()]
    return [s]


def load_users_csv(path: str) -> pd.DataFrame:
    """
    Users.csv columns per README: user_id, name, description, submission_num, comment_num,
    comment_num_1, comment_num_2, subreddit. :contentReference[oaicite:4]{index=4}
    Labels derived from order: first 1907 human, last 1000 bot. :contentReference[oaicite:5]{index=5}
    """
    df = pd.read_csv(path)
    df = df.copy()

    # enforce expected columns if present
    for col in ["submission_num", "comment_num", "comment_num_1", "comment_num_2"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(np.float32)

    # label from row order
    n = len(df)
    # First 1907 -> human (0), remaining -> bot (1)
    df["label"] = 0
    if n >= 1907:
        df.loc[df.index >= 1907, "label"] = 1

    # normalize ids
    df["user_id"] = df["user_id"].astype(str)

    return df


def load_user_post_comment_json(path: str) -> Dict[str, Any]:
    """
    user_post_comment.json is keyed by user_id. :contentReference[oaicite:6]{index=6}
    Each entry contains:
      - posts: list of dicts with keys like submission_id, author_name, posts(text), score, num_comments,
               upvote_ratio, created_utc, subreddit :contentReference[oaicite:7]{index=7}
      - comment_1: list of dicts with comment_body, comment_score, link_id, parent_id, subreddit, created_utc, level :contentReference[oaicite:8]{index=8}
      - comment_2: list ...
    """
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    # keys are user ids
    return {str(k): v for k, v in obj.items()}


def build_account_table(users_df: pd.DataFrame, upc: Dict[str, Any]) -> pd.DataFrame:
    """
    Creates a unified per-account dataframe with:
      account_id, label, username, profile, subreddit_list,
      numeric metadata (submission_num, comment_num_1, comment_num_2, comment_num),
      messages: list[{text, ts, kind, subreddit, score_like}]
    """
    rows = []
    for _, u in users_df.iterrows():
        uid = str(u["user_id"])
        entry = upc.get(uid, {})
        posts = entry.get("posts", []) or []
        c1 = entry.get("comment_1", []) or []
        c2 = entry.get("comment_2", []) or []

        messages = []

        # posts: text key is literally "posts" in JSON sample :contentReference[oaicite:9]{index=9}
        for p in posts:
            txt = (p.get("posts") or "").strip()
            ts = _to_unix_seconds(p.get("created_utc", ""))
            if txt:
                messages.append({
                    "text": txt,
                    "ts": ts,
                    "kind": "post",
                    "subreddit": p.get("subreddit"),
                    "score": p.get("score"),
                    "upvote_ratio": p.get("upvote_ratio"),
                    "num_comments": p.get("num_comments"),
                })

        # comment_1: text key is "comment_body" in sample :contentReference[oaicite:10]{index=10}
        for c in c1:
            txt = (c.get("comment_body") or "").strip()
            ts = _to_unix_seconds(c.get("created_utc", ""))
            if txt:
                messages.append({
                    "text": txt,
                    "ts": ts,
                    "kind": "comment_1",
                    "subreddit": c.get("subreddit"),
                    "score": c.get("comment_score"),
                    "link_id": c.get("link_id"),
                    "parent_id": c.get("parent_id"),
                    "level": c.get("level"),
                })

        for c in c2:
            txt = (c.get("comment_body") or "").strip()
            ts = _to_unix_seconds(c.get("created_utc", ""))
            if txt:
                messages.append({
                    "text": txt,
                    "ts": ts,
                    "kind": "comment_2",
                    "subreddit": c.get("subreddit"),
                    "score": c.get("comment_score"),
                    "link_id": c.get("link_id"),
                    "parent_id": c.get("parent_id"),
                    "level": c.get("level"),
                })

        # sort temporally (temporal features depend on this)
        messages = [m for m in messages if m.get("ts") is not None]
        messages.sort(key=lambda m: m["ts"])

        sr_list = parse_subreddits(u.get("subreddit"))

        rows.append({
            "account_id": uid,
            "label": int(u["label"]),
            "username": (u.get("name") or ""),
            "profile": (u.get("description") or ""),
            "subreddit_list": sr_list,

            # numeric metadata from Users.csv
            "submission_num": float(u.get("submission_num", 0.0)),
            "comment_num": float(u.get("comment_num", 0.0)),
            "comment_num_1": float(u.get("comment_num_1", 0.0)),
            "comment_num_2": float(u.get("comment_num_2", 0.0)),

            "messages": messages,
        })

    return pd.DataFrame(rows)