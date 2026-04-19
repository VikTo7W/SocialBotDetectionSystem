import pytest

from data_io import load_dataset


def test_load_dataset_rejects_unknown_dataset():
    with pytest.raises(ValueError, match="unknown dataset"):
        load_dataset("reddit", users_csv_path="x", upc_json_path="y")


def test_load_dataset_signature_exposes_top_level_dispatch():
    assert callable(load_dataset)
