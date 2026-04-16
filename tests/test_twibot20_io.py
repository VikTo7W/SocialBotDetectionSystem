"""
Tests for Phase 8: TwiBot-20 data loader.
Requirements covered: TW-01, TW-02, TW-03
"""

import json
import os
import tempfile

import numpy as np
import pandas as pd
import pytest

from twibot20_io import load_accounts, build_edges, validate


def _write_test_json(records: list, tmp_path) -> str:
    path = os.path.join(str(tmp_path), "test.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f)
    return path


def _make_record(id_: str, screen_name: str, label: str = "0", tweets=None, neighbor=None) -> dict:
    return {
        "ID": id_,
        "profile": {
            "screen_name": screen_name + " ",    # trailing space per Pitfall 1
            "statuses_count": "10 ",
            "followers_count": "5 ",
            "friends_count": "3 ",
            "created_at": "Mon Apr 23 09:47:10 +0000 2012 ",
            "id_str": id_ + " ",
        },
        "tweet": tweets,
        "neighbor": neighbor,
        "domain": [],
        "label": label,
    }


def test_load_accounts_schema(tmp_path):
    records = [
        _make_record("1", "alice", tweets=["hello", "world"]),
        _make_record("2", "bob", tweets=["hello", "world"]),
    ]
    path = _write_test_json(records, tmp_path)
    df = load_accounts(path)
    required_cols = ["node_idx", "screen_name", "statuses_count", "followers_count",
                     "friends_count", "created_at", "messages", "label"]
    for col in required_cols:
        assert col in df.columns, f"Missing column: {col}"
    assert len(df) == 2, f"Expected 2 rows, got {len(df)}"


def test_node_idx_contiguous(tmp_path):
    records = [
        _make_record("1", "alice"),
        _make_record("2", "bob"),
        _make_record("3", "carol"),
    ]
    path = _write_test_json(records, tmp_path)
    df = load_accounts(path)
    assert df["node_idx"].tolist() == [0, 1, 2], (
        f"Expected [0, 1, 2], got {df['node_idx'].tolist()}"
    )
    assert df["node_idx"].dtype == np.int32, (
        f"Expected int32, got {df['node_idx'].dtype}"
    )


def test_messages_structure(tmp_path):
    records = [_make_record("1", "alice", tweets=["hello", "world"])]
    path = _write_test_json(records, tmp_path)
    df = load_accounts(path)
    messages = df.iloc[0]["messages"]
    assert len(messages) == 2, f"Expected 2 messages, got {len(messages)}"
    assert messages[0] == {"text": "hello", "ts": None, "kind": "tweet"}, (
        f"Unexpected message[0]: {messages[0]}"
    )
    assert messages[1] == {"text": "world", "ts": None, "kind": "tweet"}, (
        f"Unexpected message[1]: {messages[1]}"
    )


def test_null_tweet_handled(tmp_path):
    records = [_make_record("1", "alice", tweets=None)]
    path = _write_test_json(records, tmp_path)
    df = load_accounts(path)
    assert df.iloc[0]["messages"] == [], (
        f"Expected empty list for tweet=None, got {df.iloc[0]['messages']}"
    )


def test_label_is_int(tmp_path):
    records = [
        _make_record("1", "alice", label="0"),
        _make_record("2", "bob", label="1"),
    ]
    path = _write_test_json(records, tmp_path)
    df = load_accounts(path)
    assert df["label"].tolist() == [0, 1], (
        f"Expected [0, 1], got {df['label'].tolist()}"
    )
    assert pd.api.types.is_integer_dtype(df["label"]), (
        f"Expected integer dtype, got {df['label'].dtype}"
    )


def test_trailing_whitespace_stripped(tmp_path):
    records = [_make_record("1", "alice")]
    path = _write_test_json(records, tmp_path)
    df = load_accounts(path)
    assert df.iloc[0]["screen_name"] == "alice", (
        f"Expected 'alice' (no trailing space), got {repr(df.iloc[0]['screen_name'])}"
    )
    assert df.iloc[0]["statuses_count"] == 10, (
        f"Expected numeric 10, got {repr(df.iloc[0]['statuses_count'])}"
    )
