from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from ..schemas.contracts import (
    CausalSummaryResponse,
    CustomerListResponse,
    RecommendationListResponse,
    SummaryResponse,
)
from ..services.causal_service import build_causal_summary, get_top_ite_customers
from ..services.data_service import build_summary, get_customer_by_id, list_customers
from ..services.optimization_service import build_optimization, build_recommendations, build_uplift

router = APIRouter(prefix="/api", tags=["Econocausal"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "econocausal"}


@router.get("/summary", response_model=SummaryResponse)
def get_summary() -> SummaryResponse:
    return build_summary()


@router.get("/customers", response_model=CustomerListResponse)
def customers(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=25, ge=1, le=100),
    segment: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=100),
) -> CustomerListResponse:
    """Page and filter customers from PostgreSQL, or the documented file fallback."""
    items, total = list_customers(offset=offset, limit=limit, segment=segment, search=search)
    return CustomerListResponse(items=items, total=total, offset=offset, limit=limit)


@router.get("/customers/{customer_id}")
def get_customer(customer_id: int) -> dict:
    customer = get_customer_by_id(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="customer not found")
    return customer


@router.get("/causal/summary", response_model=CausalSummaryResponse)
def causal_summary() -> CausalSummaryResponse:
    return build_causal_summary()


@router.get("/causal/ite")
def causal_ite(limit: int = Query(default=10, ge=1, le=100)) -> list[dict]:
    return get_top_ite_customers(limit=limit)


@router.get("/uplift")
def uplift() -> dict:
    """Return the validated uplift metric and scenario artifacts."""
    return build_uplift()


@router.get("/recommendations", response_model=RecommendationListResponse)
def recommendations(
    budget: float = Query(default=1000000.0, ge=0),
    limit: int = Query(default=25, ge=1, le=100),
) -> RecommendationListResponse:
    return build_recommendations(budget=budget, limit=limit)


@router.get("/optimize", response_model=RecommendationListResponse)
def optimize(
    budget: float = Query(default=1000000.0, ge=0),
    method: Literal["greedy"] = Query(default="greedy"),
) -> RecommendationListResponse:
    return build_optimization(budget=budget, method=method)


from pydantic import BaseModel

class RetrainRequest(BaseModel):
    model_type: Literal["t_learner", "x_learner", "dml"] = "dml"
    base_estimator: Literal["gradient_boosting", "random_forest", "linear", "lightgbm"] = "gradient_boosting"
    seed: int = 42

@router.post("/causal/retrain")
def retrain_model(request: RetrainRequest) -> dict:
    import os
    import subprocess
    import sys
    import yaml
    
    # 1. Update config.yaml with new parameters
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    project_root = os.path.dirname(backend_dir)
    config_path = os.path.join(project_root, "causal_ml", "config.yaml")
    
    if not os.path.exists(config_path):
        return {"error": "Causal ML configuration file not found."}
        
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
        
    config["model"]["type"] = request.model_type
    config["model"]["base_estimator"] = request.base_estimator
    config["model"]["seed"] = request.seed
    
    with open(config_path, "w") as f:
        yaml.safe_dump(config, f)
        
    # 2. Add causal_ml directory to Python path and execute scripts
    causal_ml_dir = os.path.join(project_root, "causal_ml")
    if causal_ml_dir not in sys.path:
        sys.path.append(causal_ml_dir)
        
    try:
        subprocess.run([sys.executable, os.path.join(project_root, "scripts", "run_causal_pipeline.py")], check=True, cwd=project_root)
        
    except Exception as e:
        import traceback
        return {
            "error": f"Failed to execute training pipeline: {str(e)}",
            "trace": traceback.format_exc()
        }
        
    # 3. Return the updated causal summary
    return build_causal_summary()
