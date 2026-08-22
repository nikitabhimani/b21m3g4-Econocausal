import pytest
from fastapi import HTTPException

from backend.app.api import routes


def test_health_endpoint():
    assert routes.health_check()["status"] == "ok"


def test_customer_list_endpoint_uses_repository(monkeypatch):
    monkeypatch.setattr(routes, "list_customers", lambda **_: ([{"customer_id": 1}], 1))
    response = routes.customers(offset=0, limit=1, segment=None, search=None)
    assert response.model_dump() == {"items": [{"customer_id": 1}], "total": 1, "offset": 0, "limit": 1}


def test_missing_customer_returns_404(monkeypatch):
    monkeypatch.setattr(routes, "get_customer_by_id", lambda _: None)
    with pytest.raises(HTTPException) as error:
        routes.get_customer(999999)
    assert error.value.status_code == 404
    assert error.value.detail == "customer not found"


def test_recommendations_passes_budget_to_optimizer(monkeypatch):
    captured = {}

    def fake_recommendations(*, budget, limit):
        captured.update(budget=budget, limit=limit)
        return {
            "budget": budget,
            "total_recommended_customers": 1,
            "total_expected_profit": 12.0,
            "total_expected_cost": 10.0,
            "recommendations": [{"customer_id": 1, "predicted_ite": 0.2, "recommended_discount": 0.1, "expected_profit": 12.0, "expected_cost": 10.0}],
        }

    monkeypatch.setattr(routes, "build_recommendations", fake_recommendations)
    response = routes.recommendations(budget=25000, limit=10)
    assert response["budget"] == 25000
    assert captured == {"budget": 25000.0, "limit": 10}


def test_optimize_endpoint_exposes_lp_method(monkeypatch):
    captured = {}

    def fake_optimization(*, budget, method):
        captured.update(budget=budget, method=method)
        return {
            "budget": budget,
            "method": method,
            "total_recommended_customers": 0,
            "total_expected_profit": 0.0,
            "total_expected_cost": 0.0,
            "recommendations": [],
        }

    monkeypatch.setattr(routes, "build_optimization", fake_optimization)
    response = routes.optimize(budget=100.0, method="lp")
    assert response["method"] == "lp"
    assert captured == {"budget": 100.0, "method": "lp"}
