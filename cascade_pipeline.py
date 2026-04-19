from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

from botdetector_pipeline import (
    AMRDeltaRefiner,
    FeatureConfig,
    Stage1MetadataModel,
    Stage2BaseContentModel,
    Stage3StructuralModel,
    StageThresholds,
    TextEmbedder,
    TrainedSystem,
    build_meta12_table,
    entropy_from_p,
    gate_amr,
    gate_stage3,
    logit,
    oof_meta12_predictions,
    sigmoid,
    train_meta12,
    train_meta123,
)
from features.stage1 import STAGE1_TWITTER_COLUMNS, Stage1Extractor
from features.stage2 import Stage2Extractor
from features.stage3 import Stage3Extractor


def infer_dataset(df: pd.DataFrame, cfg: FeatureConfig | None = None) -> str:
    if cfg is not None and list(cfg.stage1_numeric_cols) == list(STAGE1_TWITTER_COLUMNS):
        return "twibot"
    if "screen_name" in df.columns or "domain_list" in df.columns:
        return "twibot"
    return "botsim"


class CascadePipeline:
    def __init__(
        self,
        dataset: str,
        cfg: FeatureConfig | None = None,
        *,
        random_state: int = 42,
        embedder: TextEmbedder | None = None,
    ) -> None:
        if dataset not in {"botsim", "twibot"}:
            raise ValueError(f"unknown dataset: {dataset!r}")
        self.dataset = dataset
        self.random_state = random_state
        self.embedder = embedder
        self.cfg = cfg or self._default_cfg(dataset)
        self.stage1_extractor = Stage1Extractor(dataset)
        self.stage2_extractor = Stage2Extractor(dataset)
        self.stage3_extractor = Stage3Extractor(dataset)

    def fit(
        self,
        S1: pd.DataFrame,
        S2: pd.DataFrame,
        edges_S1: pd.DataFrame,
        edges_S2: pd.DataFrame,
        th: StageThresholds,
        *,
        nodes_total: int | None = None,
        embedder: TextEmbedder | None = None,
    ) -> TrainedSystem:
        embedder = embedder or self.embedder or TextEmbedder()

        X1_tr = self.stage1_extractor.extract(S1)
        y1_tr = S1["label"].to_numpy(dtype=np.int64)
        stage1 = Stage1MetadataModel(use_isotonic=False, random_state=self.random_state).fit(X1_tr, y1_tr)

        X2_tr = self.stage2_extractor.extract(
            S1,
            embedder,
            max_msgs=self.cfg.max_messages_per_account,
            max_chars=self.cfg.max_chars_per_message,
        )
        stage2a = Stage2BaseContentModel(use_isotonic=False, random_state=self.random_state).fit(X2_tr, y1_tr)
        out2a_S1 = stage2a.predict(X2_tr)

        h_amr_S1 = self.stage2_extractor.extract_amr(
            S1,
            embedder,
            max_chars=self.cfg.max_chars_per_message,
        )
        amr_refiner = AMRDeltaRefiner(lr=0.05, epochs=400, l2=1e-3, random_state=self.random_state)
        amr_refiner.fit(h_amr_S1, out2a_S1["z2a"], y1_tr)

        X3_tr = self.stage3_extractor.extract(S1, edges_S1, num_nodes_total=nodes_total)
        stage3 = Stage3StructuralModel(use_isotonic=False, random_state=self.random_state).fit(X3_tr, y1_tr)

        y2 = S2["label"].to_numpy(dtype=np.int64)
        out1_S2 = stage1.predict(self.stage1_extractor.extract(S2))
        X2_S2 = self.stage2_extractor.extract(
            S2,
            embedder,
            max_msgs=self.cfg.max_messages_per_account,
            max_chars=self.cfg.max_chars_per_message,
        )
        out2a_S2 = stage2a.predict(X2_S2)

        amr_mask = gate_amr(out2a_S2["p2a"], out2a_S2["n2"], out1_S2["z1"], out2a_S2["z2a"], th)
        z2 = np.asarray(out2a_S2["z2a"], dtype=np.float64).copy()
        if amr_mask.any():
            h_amr_S2 = self.stage2_extractor.extract_amr(
                S2.loc[amr_mask],
                embedder,
                max_chars=self.cfg.max_chars_per_message,
            )
            z2[amr_mask] = amr_refiner.refine(z2[amr_mask], h_amr_S2)

        p2 = sigmoid(z2)
        out2_S2 = {
            "z2": z2,
            "p2": p2,
            "u2": entropy_from_p(p2),
            "n2": out2a_S2["n2"],
        }
        X_meta12_S2 = build_meta12_table(out1_S2, out2_S2, amr_used=amr_mask.astype(np.float32))
        p12_oof = oof_meta12_predictions(X_meta12_S2, y2, n_splits=5, random_state=self.random_state)
        meta12 = train_meta12(X_meta12_S2, y2)

        stage3_mask = gate_stage3(p12_oof, out1_S2["n1"], out2_S2["n2"], th)
        X3_S2 = self.stage3_extractor.extract(S2, edges_S2, num_nodes_total=nodes_total)
        out3_S2 = {
            "p3": np.full(len(S2), 0.5, dtype=np.float64),
            "z3": np.zeros(len(S2), dtype=np.float64),
            "n3": np.zeros(len(S2), dtype=np.float64),
        }
        if stage3_mask.any():
            pred3 = stage3.predict(X3_S2[stage3_mask])
            out3_S2["p3"][stage3_mask] = pred3["p3"]
            out3_S2["z3"][stage3_mask] = pred3["z3"]
            out3_S2["n3"][stage3_mask] = pred3["n3"]

        X_meta123_S2 = pd.DataFrame(
            {
                "z12": logit(p12_oof),
                "z3": out3_S2["z3"],
                "stage3_used": stage3_mask.astype(np.float32),
                "n1": out1_S2["n1"],
                "n2": out2_S2["n2"],
                "n3": out3_S2["n3"],
            }
        )
        meta123 = train_meta123(X_meta123_S2, y2)

        return TrainedSystem(
            cfg=replace(self.cfg),
            th=replace(th),
            embedder=embedder,
            stage1=stage1,
            stage2a=stage2a,
            amr_refiner=amr_refiner,
            meta12=meta12,
            stage3=stage3,
            meta123=meta123,
        )

    def predict(
        self,
        system: TrainedSystem,
        df: pd.DataFrame,
        edges_df: pd.DataFrame,
        *,
        nodes_total: int | None = None,
    ) -> pd.DataFrame:
        cfg = system.cfg
        th = system.th

        out1 = system.stage1.predict(self.stage1_extractor.extract(df))
        X2 = self.stage2_extractor.extract(
            df,
            system.embedder,
            max_msgs=cfg.max_messages_per_account,
            max_chars=cfg.max_chars_per_message,
        )
        out2a = system.stage2a.predict(X2)

        amr_mask = gate_amr(out2a["p2a"], out2a["n2"], out1["z1"], out2a["z2a"], th)
        z2 = np.asarray(out2a["z2a"], dtype=np.float64).copy()
        if amr_mask.any():
            h_amr = self.stage2_extractor.extract_amr(
                df.loc[amr_mask],
                system.embedder,
                max_chars=cfg.max_chars_per_message,
            )
            z2[amr_mask] = system.amr_refiner.refine(z2[amr_mask], h_amr)

        p2 = sigmoid(z2)
        out2 = {"z2": z2, "p2": p2, "u2": entropy_from_p(p2), "n2": out2a["n2"]}
        X_meta12 = build_meta12_table(out1, out2, amr_used=amr_mask.astype(np.float32))
        p12 = system.meta12.predict_proba(X_meta12.to_numpy(dtype=np.float32))[:, 1]

        stage3_mask = gate_stage3(p12, out1["n1"], out2["n2"], th)
        X3 = self.stage3_extractor.extract(df, edges_df, num_nodes_total=nodes_total)
        p3 = np.full(len(df), 0.5, dtype=np.float64)
        z3 = np.zeros(len(df), dtype=np.float64)
        n3 = np.zeros(len(df), dtype=np.float64)
        if stage3_mask.any():
            out3 = system.stage3.predict(X3[stage3_mask])
            p3[stage3_mask] = out3["p3"]
            z3[stage3_mask] = out3["z3"]
            n3[stage3_mask] = out3["n3"]

        X_meta123 = pd.DataFrame(
            {
                "z12": logit(p12),
                "z3": z3,
                "stage3_used": stage3_mask.astype(np.float32),
                "n1": out1["n1"],
                "n2": out2["n2"],
                "n3": n3,
            }
        )
        p_final = system.meta123.predict_proba(X_meta123.to_numpy(dtype=np.float32))[:, 1]

        return pd.DataFrame(
            {
                "account_id": df["account_id"].astype(str).values,
                "p1": out1["p1"],
                "n1": out1["n1"],
                "p2": p2,
                "n2": out2["n2"],
                "amr_used": amr_mask.astype(int),
                "p12": p12,
                "stage3_used": stage3_mask.astype(int),
                "p3": p3,
                "n3": n3,
                "p_final": p_final,
            }
        )

    @staticmethod
    def _default_cfg(dataset: str) -> FeatureConfig:
        if dataset == "twibot":
            return FeatureConfig(stage1_numeric_cols=list(STAGE1_TWITTER_COLUMNS))
        return FeatureConfig(stage1_numeric_cols=[])
