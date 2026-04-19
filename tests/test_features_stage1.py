import numpy as np
import pandas as pd
import pytest

from cascade_pipeline import STAGE1_TWITTER_COLUMNS, Stage1Extractor


def _botsim_df():
    return pd.DataFrame(
        {
            "username": ["alice", "bob_42", ""],
            "submission_num": np.array([10.0, 0.0, 5.0], dtype=np.float32),
            "comment_num_1": np.array([3.0, 0.0, 2.0], dtype=np.float32),
            "comment_num_2": np.array([2.0, 0.0, 1.0], dtype=np.float32),
            "subreddit_list": [["r1", "r2"], [], ["r1"]],
        }
    )


def _twibot_df():
    return pd.DataFrame(
        [
            {
                "screen_name": "bot123",
                "statuses_count": 120,
                "followers_count": 30,
                "friends_count": 10,
                "created_at": "Mon Apr 23 09:47:10 +0000 2012",
                "messages": [
                    {"text": "RT @alice: boost", "ts": None, "kind": "tweet"},
                    {"text": "original", "ts": None, "kind": "tweet"},
                ],
                "domain_list": ["a.com"],
            },
            {
                "screen_name": "",
                "statuses_count": 0,
                "followers_count": 0,
                "friends_count": 0,
                "created_at": "",
                "messages": [],
                "domain_list": [],
            },
        ]
    )


def test_stage1_rejects_unknown_dataset():
    with pytest.raises(ValueError, match="unknown dataset"):
        Stage1Extractor("reddit")


def test_stage1_botsim_shape_is_ten_columns():
    extractor = Stage1Extractor("botsim")
    X = extractor.extract(_botsim_df())
    assert X.shape == (3, 10)
    assert X.dtype == np.float32
    assert np.isfinite(X).all()


def test_stage1_twibot_shape_matches_columns_constant():
    extractor = Stage1Extractor("twibot")
    X = extractor.extract(_twibot_df())
    assert X.shape == (2, len(STAGE1_TWITTER_COLUMNS))
    assert len(STAGE1_TWITTER_COLUMNS) == 14
    assert X.dtype == np.float32


def test_stage1_twibot_empty_df_returns_zero_rows():
    extractor = Stage1Extractor("twibot")
    empty = pd.DataFrame(
        columns=[
            "screen_name",
            "statuses_count",
            "followers_count",
            "friends_count",
            "created_at",
            "messages",
            "domain_list",
        ]
    )
    X = extractor.extract(empty)
    assert X.shape == (0, len(STAGE1_TWITTER_COLUMNS))
    assert X.dtype == np.float32


def test_stage1_botsim_nan_values_are_zeroed():
    df = _botsim_df()
    df.loc[0, "comment_num_1"] = np.nan
    extractor = Stage1Extractor("botsim")
    X = extractor.extract(df)
    assert np.isfinite(X).all(), "nan_to_num must replace NaN with 0.0"
