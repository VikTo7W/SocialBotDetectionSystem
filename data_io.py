from __future__ import annotations

from typing import Any, Dict

from botsim24_io import build_account_table, load_user_post_comment_json, load_users_csv
from twibot20_io import build_edges, load_accounts, validate


def load_dataset(dataset: str, **kwargs) -> Dict[str, Any]:
    if dataset == "botsim":
        return _load_botsim(**kwargs)
    if dataset == "twibot":
        return _load_twibot(**kwargs)
    raise ValueError(f"unknown dataset: {dataset!r}")


def _load_botsim(
    users_csv_path: str,
    upc_json_path: str,
) -> Dict[str, Any]:
    users_df = load_users_csv(users_csv_path)
    upc = load_user_post_comment_json(upc_json_path)
    accounts_df = build_account_table(users_df, upc)
    return {"accounts_df": accounts_df}


def _load_twibot(
    json_path: str,
    run_validate: bool = False,
) -> Dict[str, Any]:
    accounts_df = load_accounts(json_path)
    edges_df = build_edges(accounts_df, json_path)
    if run_validate:
        validate(accounts_df, edges_df)
    return {"accounts_df": accounts_df, "edges_df": edges_df}
