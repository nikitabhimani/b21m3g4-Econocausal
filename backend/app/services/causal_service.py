from __future__ import annotations

from ..repositories import ArtifactRepository


def build_causal_summary() -> dict:
    return ArtifactRepository().causal_summary()


def get_top_ite_customers(limit: int = 10) -> list[dict]:
    ranked = ArtifactRepository().predictions().sort_values("ite", ascending=False).head(limit)
    return ranked.to_dict(orient="records")
