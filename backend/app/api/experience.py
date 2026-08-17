"""
Experience API Endpoints.

Handles:
- POST /api/experience/calculate — calculate experience for a green action
- GET /api/farmers/{id}/experience — get experience summary
- GET /api/farmers/{id}/experience/history — get transaction history
- POST /api/farmers/{id}/experience/recalculate — recalculate all
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.repositories import get_green_action_repo
from backend.app.services.experience.calculate import (
    ExperienceError,
    calculate_experience,
    get_farmer_experience_history,
    get_farmer_experience_summary,
    recalculate_farmer_experience,
)

router = APIRouter(tags=["experience"])


class CalculateRequest(BaseModel):
    """Request to calculate experience for a green action."""
    green_action_id: str


@router.post("/experience/calculate")
def api_calculate_experience(request: CalculateRequest):
    """
    Calculate experience value for a specific green action.

    The action must exist and not have been calculated before.
    """
    ga_repo = get_green_action_repo()
    action = ga_repo.get_by_id(request.green_action_id)
    if not action:
        raise HTTPException(status_code=404, detail="綠色行動不存在")

    if not action.is_active:
        raise HTTPException(status_code=400, detail="此綠色行動已停用，無法計算經驗值")

    try:
        transaction = calculate_experience(action)
    except ExperienceError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "transaction": transaction.model_dump(),
        "message": f"經驗值計算完成: {transaction.effective_value} 點",
    }


@router.get("/farmers/{farmer_id}/experience")
def api_get_experience_summary(farmer_id: str):
    """Get farmer's experience summary (total, dimensions, level)."""
    summary = get_farmer_experience_summary(farmer_id)
    return summary


@router.get("/farmers/{farmer_id}/experience/history")
def api_get_experience_history(farmer_id: str):
    """Get farmer's full experience transaction history."""
    transactions = get_farmer_experience_history(farmer_id)
    return {
        "farmer_id": farmer_id,
        "count": len(transactions),
        "transactions": [t.model_dump() for t in transactions],
    }


@router.post("/farmers/{farmer_id}/experience/recalculate")
def api_recalculate_experience(farmer_id: str):
    """
    Recalculate all experience for a farmer from scratch.

    Used when rules change or green actions are updated.
    """
    summary = recalculate_farmer_experience(farmer_id)
    return {
        "message": "經驗值已重新計算",
        "summary": summary,
    }


@router.post("/farmers/{farmer_id}/recalculate-all")
def api_recalculate_all(farmer_id: str):
    """
    Recalculate experience, indicators and Data Health in one transaction-like step.

    This orchestration belongs on the server: the frontend previously fired three
    sequential POSTs, so a failure on the second left the farmer with a partially
    recalculated, inconsistent state. Order matters — indicators and green maturity
    read experience results, so experience must be recomputed first.
    """
    from backend.app.services.indicators.calculate import calculate_all_indicators
    from backend.app.services.data_health.calculate import calculate_all_data_health

    experience = recalculate_farmer_experience(farmer_id)
    indicators = calculate_all_indicators(farmer_id)
    data_health = calculate_all_data_health(farmer_id)

    health_summary: dict[str, int] = {}
    for result in data_health:
        health_summary[result.status.value] = health_summary.get(result.status.value, 0) + 1

    return {
        "message": "已重新計算經驗值、四大指標與 Data Health",
        "farmer_id": farmer_id,
        "experience": experience,
        "indicators": {i.indicator_type: {"score": i.score, "level": i.level} for i in indicators},
        "data_health_summary": health_summary,
        "rule_version": experience.get("rule_version"),
    }
