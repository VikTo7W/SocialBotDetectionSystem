from __future__ import annotations

from unittest.mock import patch

from train_twibot import DEFAULT_TWIBOT_MODEL_PATH, train_twibot
from train_twibot20 import DEFAULT_NATIVE_MODEL_PATH, train_twibot20


def test_legacy_twibot20_shim_uses_maintained_default_artifact():
    assert DEFAULT_NATIVE_MODEL_PATH == DEFAULT_TWIBOT_MODEL_PATH


def test_legacy_twibot20_shim_forwards_to_maintained_trainer():
    with patch("train_twibot20.train_twibot", return_value={"ok": True}) as mock_train:
        result = train_twibot20(train_path="train.json")

    mock_train.assert_called_once_with(train_path="train.json")
    assert result == {"ok": True}
