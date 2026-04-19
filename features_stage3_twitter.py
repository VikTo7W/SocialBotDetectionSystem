from __future__ import annotations

import numpy as np
import pandas as pd

from features.stage3 import STAGE3_TWITTER_COLUMNS, TWITTER_NATIVE_EDGE_TYPES, Stage3Extractor



def extract_stage3_features_twitter(
    accounts_df: pd.DataFrame,
    edges_df: pd.DataFrame,
    num_nodes_total: int | None = None,
) -> np.ndarray:
    # deprecated shim for legacy callers; shared implementation lives in features.stage3
    return Stage3Extractor("twibot").extract(accounts_df, edges_df, num_nodes_total=num_nodes_total)
