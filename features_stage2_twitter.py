from __future__ import annotations

import numpy as np
import pandas as pd

from features.stage2 import STAGE2_TWITTER_COLUMNS, Stage2Extractor


def extract_stage2_features_twitter(
    df: pd.DataFrame,
    embedder,
    max_msgs: int = 50,
    max_chars: int = 500,
) -> np.ndarray:
    # deprecated shim for legacy callers; shared implementation lives in features.stage2
    return Stage2Extractor("twibot").extract(df, embedder, max_msgs=max_msgs, max_chars=max_chars)
