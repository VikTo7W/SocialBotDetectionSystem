"""
Tests for LEAK-04: character_setting must not appear in build_account_table output.
"""

import pandas as pd
import numpy as np
import pytest

from data_io import build_account_table


def test_no_character_setting_in_table():
    """build_account_table must not include character_setting in result columns."""
    # Minimal users_df with character_setting column
    users_df = pd.DataFrame([{
        "user_id": "u001",
        "name": "testuser",
        "description": "A test account",
        "submission_num": 5.0,
        "comment_num": 10.0,
        "comment_num_1": 3.0,
        "comment_num_2": 7.0,
        "subreddit": "news",
        "label": 0,
        "character_setting": "some character setting that leaks label",
    }])

    # Minimal upc dict: one user with no posts
    upc = {
        "u001": {
            "posts": [],
            "comment_1": [],
            "comment_2": [],
        }
    }

    result = build_account_table(users_df, upc)
    assert "character_setting" not in result.columns, (
        "character_setting must not appear in build_account_table output — it is a target leak"
    )
