from __future__ import annotations

from email.utils import parsedate_to_datetime
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from twibot20_io import parse_tweet_types

_SECONDS_PER_DAY = 86400.0

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


class Stage1Extractor:
    def __init__(self, dataset: str) -> None:
        if dataset not in {"botsim", "twibot"}:
            raise ValueError(f"unknown dataset: {dataset!r}")
        self.dataset = dataset

    def extract(
        self,
        df: pd.DataFrame,
        reference_time: pd.Timestamp | None = None,
    ) -> np.ndarray:
        if self.dataset == "botsim":
            return self._extract_botsim(df)
        return self._extract_twibot(df, reference_time=reference_time)

    def _extract_botsim(self, df: pd.DataFrame) -> np.ndarray:
        name_len = df["username"].fillna("").astype(str).map(len).to_numpy(dtype=np.float32)
        post_num = df["submission_num"].to_numpy(dtype=np.float32)
        c1 = df["comment_num_1"].to_numpy(dtype=np.float32)
        c2 = df["comment_num_2"].to_numpy(dtype=np.float32)
        c_total = c1 + c2
        sr_num = df["subreddit_list"].map(
            lambda value: len(value) if isinstance(value, list) else 0
        ).to_numpy(dtype=np.float32)

        eps = 1e-6
        post_c1 = post_num / (c1 + eps)
        post_c2 = post_num / (c2 + eps)
        post_ct = post_num / (c_total + eps)
        post_sr = post_num / (sr_num + eps)

        X = np.stack(
            [
                name_len,
                post_num,
                c1,
                c2,
                c_total,
                sr_num,
                post_c1,
                post_c2,
                post_ct,
                post_sr,
            ],
            axis=1,
        )
        return np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    def _extract_twibot(
        self,
        df: pd.DataFrame,
        reference_time: pd.Timestamp | None = None,
    ) -> np.ndarray:
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
            age_days = self._safe_account_age_days(row.get("created_at"), reference_time)
            statuses_per_day = float(statuses_count / max(age_days, 1.0))
            breakdown = self._tweet_breakdown(messages)

            rows.append(
                np.array(
                    [
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
                    ],
                    dtype=np.float32,
                )
            )

        if not rows:
            return np.zeros((0, len(STAGE1_TWITTER_COLUMNS)), dtype=np.float32)

        X = np.stack(rows, axis=0)
        return np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    def _safe_account_age_days(
        self,
        created_at: Any,
        reference_time: pd.Timestamp | None,
    ) -> float:
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

    def _tweet_breakdown(self, messages: List[Dict[str, Any]]) -> Dict[str, float]:
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
