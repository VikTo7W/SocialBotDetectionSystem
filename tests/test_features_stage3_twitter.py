import numpy as np
import pandas as pd

from features.stage3 import STAGE3_TWITTER_COLUMNS, Stage3Extractor, build_graph_features_nodeidx


def _accounts():
    return pd.DataFrame([
        {"node_idx": 0},
        {"node_idx": 1},
        {"node_idx": 2},
    ])


def test_stage3_twitter_empty_edges_are_zero():
    X = Stage3Extractor("twibot").extract(_accounts(), pd.DataFrame({
        "src": np.array([], dtype=np.int32),
        "dst": np.array([], dtype=np.int32),
        "etype": np.array([], dtype=np.int8),
        "weight": np.array([], dtype=np.float32),
    }))

    assert X.shape == (3, len(STAGE3_TWITTER_COLUMNS))
    assert np.allclose(X, 0.0)


def test_stage3_twitter_following_and_follower_values():
    edges = pd.DataFrame({
        "src": np.array([0, 2], dtype=np.int32),
        "dst": np.array([1, 0], dtype=np.int32),
        "etype": np.array([0, 1], dtype=np.int8),
        "weight": np.array([1.0, 2.0], dtype=np.float32),
    })

    X = Stage3Extractor("twibot").extract(_accounts(), edges)

    assert X.shape == (3, len(STAGE3_TWITTER_COLUMNS))
    assert X[0, 1] == 1.0
    assert X[0, 3] == 2.0
    assert X[0, 4] == 1.0
    assert X[0, 7] == 1.0
    assert X[0, 10] == 1.0
    assert X[1, 0] == 1.0
    assert X[2, 1] == 1.0


def test_stage3_twitter_absent_type2_block_stays_zero():
    edges = pd.DataFrame({
        "src": np.array([0], dtype=np.int32),
        "dst": np.array([1], dtype=np.int32),
        "etype": np.array([0], dtype=np.int8),
        "weight": np.array([1.0], dtype=np.float32),
    })

    X = Stage3Extractor("twibot").extract(_accounts(), edges)

    assert np.allclose(X[:, 14:18], 0.0)
