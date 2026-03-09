
import numpy as np
import pandas as pd

def extract_stage1_matrix(df: pd.DataFrame) -> np.ndarray:
    """
    Stage 1 features derived from Users.csv columns described in README. :contentReference[oaicite:14]{index=14}
    We DO NOT use character_setting (bot-only). :contentReference[oaicite:15]{index=15}
    """
    name_len = df["username"].fillna("").astype(str).map(len).to_numpy(dtype=np.float32)
    post_num = df["submission_num"].to_numpy(dtype=np.float32)

    c1 = df["comment_num_1"].to_numpy(dtype=np.float32)
    c2 = df["comment_num_2"].to_numpy(dtype=np.float32)
    c_total = c1 + c2

    sr_num = df["subreddit_list"].map(lambda x: len(x) if isinstance(x, list) else 0).to_numpy(dtype=np.float32)

    # ratios with safe division
    eps = 1e-6
    post_c1 = post_num / (c1 + eps)
    post_c2 = post_num / (c2 + eps)
    post_ct = post_num / (c_total + eps)
    post_sr = post_num / (sr_num + eps)

    X = np.stack([
        name_len,
        post_num,
        c1,
        c2,
        c_total,
        sr_num,
        post_c1,
        post_c2,
        post_ct,
        post_sr
    ], axis=1)

    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    return X