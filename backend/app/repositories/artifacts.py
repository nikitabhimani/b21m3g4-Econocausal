from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUTPUTS = PROJECT_ROOT / "outputs"


class ArtifactRepository:
    """Reads validated generated ML and uplift artifacts."""

    def _json(self, filename: str) -> dict:
        with (OUTPUTS / filename).open(encoding="utf-8") as source:
            payload = json.load(source)
        _assert_finite(payload, filename)
        return payload

    def causal_summary(self) -> dict:
        return self._json("causal_summary.json")

    def uplift_results(self) -> dict:
        return self._json("uplift_results.json")

    def scenario_comparison(self) -> dict:
        return self._json("scenario_comparison.json")

    def predictions(self) -> pd.DataFrame:
        frame = pd.read_csv(OUTPUTS / "causal_predictions.csv")
        required = {"customer_id", "baseline_probability", "treatment_probability", "ite"}
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"Causal predictions missing columns: {', '.join(sorted(missing))}")
        if not frame[list(required)].apply(lambda column: pd.api.types.is_numeric_dtype(column)).all():
            raise ValueError("Causal predictions contain non-numeric values.")
        if not frame[list(required)].apply(lambda column: column.map(math.isfinite)).all().all():
            raise ValueError("Causal predictions contain non-finite values.")
        return frame


def _assert_finite(value, location: str) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"Non-finite value in {location}")
    if isinstance(value, dict):
        for key, child in value.items():
            _assert_finite(child, f"{location}.{key}")
    elif isinstance(value, list):
        for child in value:
            _assert_finite(child, location)
