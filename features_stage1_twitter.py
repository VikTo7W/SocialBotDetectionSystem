from __future__ import annotations

import numpy as np
import pandas as pd

from features.stage1 import STAGE1_TWITTER_COLUMNS, Stage1Extractor


def extract_stage1_matrix_twitter(
    df: pd.DataFrame,
    reference_time: pd.Timestamp | None = None,
) -> np.ndarray:
    # deprecated shim for legacy callers; shared implementation lives in features.stage1
    return Stage1Extractor("twibot").extract(df, reference_time=reference_time)
