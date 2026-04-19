from __future__ import annotations

from train_twibot import (
    DEFAULT_OUTPUT_FILES,
    DEFAULT_TWIBOT_MODEL_PATH,
    PHASE15_ARTIFACT_DIR,
    SEED,
    ensure_safe_model_output_path,
    filter_edges_for_split,
    list_expected_output_files,
    load_accounts_with_ids,
    split_train_accounts,
    train_twibot,
)

DEFAULT_NATIVE_MODEL_PATH = DEFAULT_TWIBOT_MODEL_PATH


def train_twibot20(*args, **kwargs):
    return train_twibot(*args, **kwargs)
