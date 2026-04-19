from __future__ import annotations

import numpy as np
import pandas as pd

from features.stage2 import Stage2Extractor


def extract_stage2_features(
    df: pd.DataFrame,
    embedder,
    max_msgs: int = 50,
    max_chars: int = 500,
) -> np.ndarray:
    # deprecated shim for legacy callers; shared implementation lives in features.stage2
    return Stage2Extractor("botsim").extract(df, embedder, max_msgs=max_msgs, max_chars=max_chars)
