from pydantic import BaseModel, Field


class SummaryResponse(BaseModel):
    customers: int
    treated_customers: int
    control_customers: int
    treatment_rate: float
    purchase_rate: float
    average_true_ite: float
    total_revenue: float
    total_discount_cost: float


class CausalSummaryResponse(BaseModel):
    average_ite: float
    median_ite: float
    positive_ite_share: float
    top_positive_ite: float
    top_negative_ite: float


class RecommendationItem(BaseModel):
    customer_id: int
    predicted_ite: float
    recommended_discount: float
    expected_profit: float
    expected_cost: float


class RecommendationListResponse(BaseModel):
    budget: float
    total_recommended_customers: int
    total_expected_profit: float
    total_expected_cost: float
    recommendations: list[RecommendationItem] = Field(default_factory=list)
