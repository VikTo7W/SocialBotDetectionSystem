import numpy as np
import pandas as pd

from features.stage1 import STAGE1_TWITTER_COLUMNS, Stage1Extractor


def _account(
    screen_name="bot123",
    statuses_count=120,
    followers_count=30,
    friends_count=10,
    created_at="Mon Apr 23 09:47:10 +0000 2012",
    messages=None,
    domain_list=None,
):
    return {
        "screen_name": screen_name,
        "statuses_count": statuses_count,
        "followers_count": followers_count,
        "friends_count": friends_count,
        "created_at": created_at,
        "messages": messages or [],
        "domain_list": domain_list or [],
    }


def test_stage1_twitter_shape_and_semantic_values():
    extractor = Stage1Extractor("twibot")
    df = pd.DataFrame([_account(
        screen_name="bot123",
        statuses_count=120,
        followers_count=30,
        friends_count=10,
        created_at="Tue Apr 10 00:00:00 +0000 2012",
        messages=[
            {"text": "RT @alice: signal boost", "ts": None, "kind": "tweet"},
            {"text": "MT @bob: remix", "ts": None, "kind": "tweet"},
            {"text": "own thought", "ts": None, "kind": "tweet"},
        ],
        domain_list=["Politics", "News"],
    )])

    reference_time = pd.Timestamp("2012-04-20T00:00:00Z")
    X = extractor.extract(df, reference_time=reference_time)

    assert X.shape == (1, len(STAGE1_TWITTER_COLUMNS))
    assert X[0, 0] == 6.0
    assert np.isclose(X[0, 1], 0.5)
    assert X[0, 5] == 3.0
    assert np.isclose(X[0, 6], 10.0)
    assert np.isclose(X[0, 7], 12.0)
    assert X[0, 8] == 3.0
    assert X[0, 9] == 2.0
    assert np.isclose(X[0, 10], 1.0 / 3.0)
    assert np.isclose(X[0, 11], 1.0 / 3.0)
    assert np.isclose(X[0, 12], 1.0 / 3.0)
    assert X[0, 13] == 2.0


def test_stage1_twitter_zero_tweet_zero_domain_defaults():
    extractor = Stage1Extractor("twibot")
    df = pd.DataFrame([_account(
        screen_name="plainuser",
        statuses_count=0,
        followers_count=0,
        friends_count=0,
        created_at="",
        messages=[],
        domain_list=[],
    )])

    X = extractor.extract(df, reference_time=pd.Timestamp("2012-04-20T00:00:00Z"))

    assert X.shape == (1, len(STAGE1_TWITTER_COLUMNS))
    assert np.all(np.isfinite(X))
    assert X[0, 8] == 0.0
    assert X[0, 9] == 0.0
    assert X[0, 10] == 0.0
    assert X[0, 11] == 0.0
    assert X[0, 12] == 0.0
    assert X[0, 13] == 0.0


def test_stage1_twitter_rt_heavy_behavior_changes_breakdown():
    extractor = Stage1Extractor("twibot")
    df = pd.DataFrame([_account(
        messages=[
            {"text": "RT @alice: one", "ts": None, "kind": "tweet"},
            {"text": "rt @alice: two", "ts": None, "kind": "tweet"},
            {"text": "RT @carol: three", "ts": None, "kind": "tweet"},
            {"text": "ordinary post", "ts": None, "kind": "tweet"},
        ]
    )])

    X = extractor.extract(df, reference_time=pd.Timestamp("2012-04-20T00:00:00Z"))

    assert np.isclose(X[0, 10], 0.75)
    assert np.isclose(X[0, 12], 0.25)
    assert X[0, 13] == 2.0


def test_stage1_twitter_malformed_created_at_falls_back_to_zero_age():
    extractor = Stage1Extractor("twibot")
    df = pd.DataFrame([_account(created_at="not a real timestamp")])
    X = extractor.extract(df, reference_time=pd.Timestamp("2012-04-20T00:00:00Z"))

    assert X[0, 6] == 0.0
    assert X[0, 7] == 120.0
