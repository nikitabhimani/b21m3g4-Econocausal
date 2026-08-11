from fastapi import APIRouter, Query

from app.schemas.contracts import (
    CausalSummaryResponse,
    RecommendationListResponse,
    SummaryResponse,
)
from app.services.causal_service import build_causal_summary, get_top_ite_customers
from app.services.data_service import build_summary, get_customer_by_id, load_customer_data
from app.services.optimization_service import build_recommendations

router = APIRouter(prefix="/api", tags=["Econocausal"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "econocausal"}


@router.get("/summary", response_model=SummaryResponse)
def get_summary() -> SummaryResponse:
    return build_summary()


@router.get("/customers/{customer_id}")
def get_customer(customer_id: int) -> dict:
    customer = get_customer_by_id(customer_id)
    if customer is None:
        return {"error": "customer not found"}
    return customer


@router.get("/causal/summary", response_model=CausalSummaryResponse)
def causal_summary() -> CausalSummaryResponse:
    return build_causal_summary()


@router.get("/causal/ite")
def causal_ite(limit: int = Query(default=10, ge=1, le=100)) -> list[dict]:
    return get_top_ite_customers(limit=limit)


@router.get("/recommendations", response_model=RecommendationListResponse)
def recommendations(
    budget: float = Query(default=1000000.0, ge=0),
    limit: int = Query(default=25, ge=1, le=100),
) -> RecommendationListResponse:
    return build_recommendations(budget=budget, limit=limit)
