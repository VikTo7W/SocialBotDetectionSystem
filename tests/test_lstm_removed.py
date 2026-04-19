import dataclasses

import botdetector_pipeline as bp


def test_stage2_lstm_refiner_symbol_is_absent():
    assert not hasattr(bp, "Stage2LSTMRefiner"), (
        "Stage2LSTMRefiner must be deleted from botdetector_pipeline (CORE-05)"
    )


def test_extract_message_embedding_sequences_for_accounts_symbol_is_absent():
    assert not hasattr(bp, "extract_message_embedding_sequences_for_accounts"), (
        "LSTM sequence helper must be deleted (CORE-05)"
    )


def test_apply_stage2b_refiner_symbol_is_absent():
    assert not hasattr(bp, "apply_stage2b_refiner"), (
        "apply_stage2b_refiner must be deleted (AMR path is inlined at both call sites)"
    )


def test_normalize_stage2b_variant_symbol_is_absent():
    assert not hasattr(bp, "normalize_stage2b_variant"), (
        "normalize_stage2b_variant must be deleted (no variant switching remains)"
    )


def test_stage2lstmnet_symbol_is_absent():
    assert not hasattr(bp, "_Stage2LSTMNet"), (
        "_Stage2LSTMNet must be deleted (CORE-05)"
    )


def test_trained_system_has_no_lstm_field():
    fields = {field.name for field in dataclasses.fields(bp.TrainedSystem)}
    assert "stage2b_lstm" not in fields, "TrainedSystem.stage2b_lstm field must be removed"
    assert "stage2b_variant" not in fields, "TrainedSystem.stage2b_variant field must be removed"
