from __future__ import annotations

from email.utils import parsedate_to_datetime
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from twibot20_io import parse_tweet_types

_SECONDS_PER_DAY = 86400.0
_EPS = 1e-6

STAGE1_TWITTER_COLUMNS = [
    "screen_name_len",
    "screen_name_digit_ratio",
    "statuses_count",
    "followers_count",
    "friends_count",
    "followers_friends_ratio",
    "account_age_days",
    "statuses_per_day",
    "tweet_count_loaded",
    "domain_count",
    "rt_fraction",
    "mt_fraction",
    "original_fraction",
    "unique_rt_mt_targets",
]


def _safe_account_age_days(created_at: Any, reference_time: pd.Timestamp | None) -> float:
    text = str(created_at or "").strip()
    if not text or reference_time is None:
        return 0.0
    try:
        created_dt = parsedate_to_datetime(text)
    except (TypeError, ValueError, IndexError, OverflowError):
        return 0.0

    created_ts = pd.Timestamp(created_dt)
    if created_ts.tzinfo is None:
        created_ts = created_ts.tz_localize("UTC")
    else:
        created_ts = created_ts.tz_convert("UTC")

    delta_seconds = max((reference_time - created_ts).total_seconds(), 0.0)
    return float(delta_seconds / _SECONDS_PER_DAY)


def _tweet_breakdown(messages: List[Dict[str, Any]]) -> Dict[str, float]:
    counts = parse_tweet_types(messages)
    total = float(len(messages))
    if total <= 0.0:
        return {
            "tweet_count_loaded": 0.0,
            "rt_fraction": 0.0,
            "mt_fraction": 0.0,
            "original_fraction": 0.0,
            "unique_rt_mt_targets": 0.0,
        }

    return {
        "tweet_count_loaded": total,
        "rt_fraction": float(counts["rt_count"]) / total,
        "mt_fraction": float(counts["mt_count"]) / total,
        "original_fraction": float(counts["original_count"]) / total,
        "unique_rt_mt_targets": float(len(counts["rt_mt_usernames"])),
    }


def extract_stage1_matrix_twitter(
    df: pd.DataFrame,
    reference_time: pd.Timestamp | None = None,
) -> np.ndarray:
    """
    Standalone TwiBot-native Stage 1 feature extractor.

    Consumes only fields exposed by ``twibot20_io.load_accounts()``:
    ``screen_name``, ``statuses_count``, ``followers_count``, ``friends_count``,
    ``created_at``, ``messages``, and ``domain_list``.

    Output contract: a float32 matrix with columns listed in
    ``STAGE1_TWITTER_COLUMNS`` and no dependence on Reddit schema analogs.
    """
    if reference_time is None:
        reference_time = pd.Timestamp.utcnow()
    if reference_time.tzinfo is None:
        reference_time = reference_time.tz_localize("UTC")
    else:
        reference_time = reference_time.tz_convert("UTC")

    rows: List[np.ndarray] = []

    for _, row in df.iterrows():
        screen_name = str(row.get("screen_name") or "")
        statuses_count = float(row.get("statuses_count") or 0.0)
        followers_count = float(row.get("followers_count") or 0.0)
        friends_count = float(row.get("friends_count") or 0.0)
        messages = list(row.get("messages") or [])
        domains = row.get("domain_list") or []

        name_len = float(len(screen_name))
        digit_count = sum(1 for ch in screen_name if ch.isdigit())
        digit_ratio = float(digit_count / max(len(screen_name), 1))
        age_days = _safe_account_age_days(row.get("created_at"), reference_time)
        statuses_per_day = float(statuses_count / max(age_days, 1.0))
        breakdown = _tweet_breakdown(messages)

        feat = np.array([
            name_len,
            digit_ratio,
            statuses_count,
            followers_count,
            friends_count,
            float(followers_count / max(friends_count, 1.0)),
            age_days,
            statuses_per_day,
            breakdown["tweet_count_loaded"],
            float(len(domains)),
            breakdown["rt_fraction"],
            breakdown["mt_fraction"],
            breakdown["original_fraction"],
            breakdown["unique_rt_mt_targets"],
        ], dtype=np.float32)
        rows.append(feat)

    if not rows:
        return np.zeros((0, len(STAGE1_TWITTER_COLUMNS)), dtype=np.float32)

    X = np.stack(rows, axis=0)
    return np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
