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


# --- TW-02: Edge construction tests ---


def test_edges_schema(tmp_path):
    records = [
        _make_record("A", "alice", neighbor={"following": ["B"], "follower": []}),
        _make_record("B", "bob", neighbor={"following": [], "follower": ["A"]}),
        _make_record("C", "carol", neighbor=None),
    ]
    path = _write_test_json(records, tmp_path)
    accounts_df = load_accounts(path)
    edges_df = build_edges(accounts_df, path)
    assert list(edges_df.columns) == ["src", "dst", "etype", "weight"], (
        f"Expected ['src','dst','etype','weight'], got {list(edges_df.columns)}"
    )
    assert edges_df["src"].dtype == np.int32, f"Expected int32, got {edges_df['src'].dtype}"
    assert edges_df["dst"].dtype == np.int32, f"Expected int32, got {edges_df['dst'].dtype}"
    assert edges_df["etype"].dtype == np.int8, f"Expected int8, got {edges_df['etype'].dtype}"
    assert edges_df["weight"].dtype == np.float32, f"Expected float32, got {edges_df['weight'].dtype}"


def test_null_neighbor_no_rows(tmp_path):
    records = [
        _make_record("A", "alice", neighbor=None),
        _make_record("B", "bob", neighbor=None),
    ]
    path = _write_test_json(records, tmp_path)
    accounts_df = load_accounts(path)
    edges_df = build_edges(accounts_df, path)
    assert len(edges_df) == 0, f"Expected 0 rows, got {len(edges_df)}"
    assert list(edges_df.columns) == ["src", "dst", "etype", "weight"], (
        f"Expected 4 columns even when empty, got {list(edges_df.columns)}"
    )


def test_edges_in_set_only(tmp_path):
    records = [
        _make_record("A", "alice", neighbor={"following": ["B", "OUTSIDER"], "follower": []}),
        _make_record("B", "bob", neighbor={"following": ["OUTSIDER2"], "follower": []}),
    ]
    path = _write_test_json(records, tmp_path)
    accounts_df = load_accounts(path)
    edges_df = build_edges(accounts_df, path)
    assert len(edges_df) == 1, f"Expected 1 in-set edge, got {len(edges_df)}"
    assert edges_df.iloc[0]["src"] == 0, f"Expected src=0 (A), got {edges_df.iloc[0]['src']}"
    assert edges_df.iloc[0]["dst"] == 1, f"Expected dst=1 (B), got {edges_df.iloc[0]['dst']}"
    assert edges_df.iloc[0]["etype"] == 0, f"Expected etype=0 (following), got {edges_df.iloc[0]['etype']}"


def test_edge_weight(tmp_path):
    records = [
        _make_record("A", "alice", neighbor={"following": ["B"], "follower": []}),
        _make_record("B", "bob", neighbor=None),
    ]
    path = _write_test_json(records, tmp_path)
    accounts_df = load_accounts(path)
    edges_df = build_edges(accounts_df, path)
    assert np.allclose(edges_df["weight"].values, np.log1p(1.0)), (
        f"Expected all weights=log1p(1.0)={np.log1p(1.0)}, got {edges_df['weight'].values}"
    )


def test_edge_direction(tmp_path):
    records = [
        _make_record("X", "xuser", neighbor={"following": ["Y"], "follower": ["Y"]}),
        _make_record("Y", "yuser", neighbor=None),
    ]
    path = _write_test_json(records, tmp_path)
    accounts_df = load_accounts(path)
    edges_df = build_edges(accounts_df, path)
    assert len(edges_df) == 2, f"Expected 2 edges, got {len(edges_df)}"
    following_rows = edges_df[edges_df["etype"] == 0]
    follower_rows = edges_df[edges_df["etype"] == 1]
    assert len(following_rows) == 1, "Expected exactly 1 following edge"
    assert int(following_rows.iloc[0]["src"]) == 0, "Following edge: src should be X (idx=0)"
    assert int(following_rows.iloc[0]["dst"]) == 1, "Following edge: dst should be Y (idx=1)"
    assert len(follower_rows) == 1, "Expected exactly 1 follower edge"
    assert int(follower_rows.iloc[0]["src"]) == 1, "Follower edge: src should be Y (idx=1)"
    assert int(follower_rows.iloc[0]["dst"]) == 0, "Follower edge: dst should be X (idx=0)"


# --- TW-03: Validation tests ---


def test_validate_passes(tmp_path):
    records = [
        _make_record("A", "alice", neighbor={"following": ["B"], "follower": []}),
        _make_record("B", "bob", neighbor=None),
    ]
    path = _write_test_json(records, tmp_path)
    accounts_df = load_accounts(path)
    edges_df = build_edges(accounts_df, path)
    # Should not raise
    validate(accounts_df, edges_df)


def test_validate_bounds_fail(tmp_path):
    records = [_make_record("A", "alice", neighbor=None)]
    path = _write_test_json(records, tmp_path)
    accounts_df = load_accounts(path)
    # Manually create bad edges_df with out-of-bounds src index
    bad_edges = pd.DataFrame({
        "src": np.array([5], dtype=np.int32),
        "dst": np.array([0], dtype=np.int32),
        "etype": np.array([0], dtype=np.int8),
        "weight": np.array([0.69], dtype=np.float32),
    })
    with pytest.raises(AssertionError):
        validate(accounts_df, bad_edges)
