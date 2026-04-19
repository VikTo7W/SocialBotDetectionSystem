import numpy as np
import pandas as pd
from features.stage1 import Stage1Extractor

def extract_stage1_matrix(df: pd.DataFrame) -> np.ndarray:
    # deprecated shim for legacy callers; shared implementation lives in features.stage1
    return Stage1Extractor("botsim").extract(df)
