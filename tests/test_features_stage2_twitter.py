import numpy as np
import pandas as pd

from cascade_pipeline import STAGE2_TWITTER_COLUMNS, Stage2Extractor


class HashingFakeEmbedder:
    def encode(self, texts, batch_size: int = 64):
        vectors = []
        for text in texts:
            vec = np.zeros(384, dtype=np.float32)
            key = sum(ord(ch) for ch in text) % 384
            vec[key] = 1.0
            if text:
                vec[(key + len(text)) % 384] = 0.5
            norm = np.linalg.norm(vec)
            vectors.append(vec / max(norm, 1e-8))
        return np.stack(vectors, axis=0)


def _df(messages):
    return pd.DataFrame([{"messages": messages}])


def test_stage2_twitter_empty_messages_are_shape_stable():
    X = Stage2Extractor("twibot").extract(_df([]), HashingFakeEmbedder())

    assert X.shape == (1, len(STAGE2_TWITTER_COLUMNS))
    assert X.dtype == np.float32
    assert np.allclose(X[0, :384], 0.0)
    assert X[0, 388] == 0.0
    assert X[0, 389] == 0.0
    assert X[0, 390] == 0.0
    assert X[0, 391] == 0.0
    assert X[0, 392] == 0.0


def test_stage2_twitter_single_message_semantics():
    X = Stage2Extractor("twibot").extract(
        _df([{"text": "Hello 123!", "ts": None, "kind": "tweet"}]),
        HashingFakeEmbedder(),
    )

    assert X.shape == (1, len(STAGE2_TWITTER_COLUMNS))
    assert X[0, 388] == 1.0
    assert X[0, 389] == 0.0
    assert X[0, 390] == 0.0
    assert X[0, 391] == 0.0
    assert X[0, 392] == 1.0
    assert X[0, 384] == float(len("Hello 123!"))


def test_stage2_twitter_duplicate_messages_raise_near_dup_features():
    embedder = HashingFakeEmbedder()
    messages = [
        {"text": "repeat me", "ts": None, "kind": "tweet"},
        {"text": "repeat me", "ts": None, "kind": "tweet"},
        {"text": "different", "ts": None, "kind": "tweet"},
    ]

    X = Stage2Extractor("twibot").extract(_df(messages), embedder)

    assert X[0, 388] == 3.0
    assert X[0, 391] > 0.0
    assert X[0, 392] > 0.0


def test_stage2_twitter_uses_raw_message_count_even_with_empty_texts():
    messages = [
        {"text": "real text", "ts": None, "kind": "tweet"},
        {"text": "", "ts": None, "kind": "tweet"},
    ]

    X = Stage2Extractor("twibot").extract(_df(messages), HashingFakeEmbedder())

    assert X[0, 388] == 2.0
    assert X[0, 392] == 0.5
