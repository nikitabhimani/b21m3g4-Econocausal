from fastapi import APIRouter, Query

from ..schemas.contracts import (
    CausalSummaryResponse,
    RecommendationListResponse,
    SummaryResponse,
)
from ..services.causal_service import build_causal_summary, get_top_ite_customers
from ..services.data_service import build_summary, get_customer_by_id, load_customer_data
from ..services.optimization_service import build_recommendations

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


from pydantic import BaseModel

class RetrainRequest(BaseModel):
    model_type: str = "t_learner"
    base_estimator: str = "gradient_boosting"
    seed: int = 42

@router.post("/causal/retrain")
def retrain_model(request: RetrainRequest) -> dict:
    import sys
    import os
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
        import importlib
        import train
        import predict
        import diagnostics
        
        # Reload modules to run with the updated config.yaml
        importlib.reload(train)
        importlib.reload(predict)
        importlib.reload(diagnostics)
        
        train.main()
        predict.main()
        diagnostics.main()
        
    except Exception as e:
        import traceback
        return {
            "error": f"Failed to execute training pipeline: {str(e)}",
            "trace": traceback.format_exc()
        }
        
    # 3. Return the updated causal summary
    return build_causal_summary()


@router.get("/causal/uplift")
def get_uplift_results() -> dict:
    import json
    import os
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    project_root = os.path.dirname(backend_dir)
    uplift_path = os.path.join(project_root, "outputs", "uplift_results.json")
    if not os.path.exists(uplift_path):
        return {"error": "Uplift results not found. Please run generate_uplift_outputs.py first."}
    with open(uplift_path, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/causal/scenarios")
def get_scenario_comparison() -> dict:
    import json
    import os
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    project_root = os.path.dirname(backend_dir)
    scenarios_path = os.path.join(project_root, "outputs", "scenario_comparison.json")
    if not os.path.exists(scenarios_path):
        return {"error": "Scenario comparison results not found. Please run generate_uplift_outputs.py first."}
    with open(scenarios_path, "r", encoding="utf-8") as f:
        return json.load(f)
