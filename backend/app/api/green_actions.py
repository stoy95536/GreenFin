"""
Green Action Management API.

Allows farmers to add new green actions through the UI.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.models import GreenAction, GreenDimension, ActionLevel
from backend.app.repositories import get_green_action_repo

router = APIRouter(tags=["green_actions"])


class CreateGreenActionRequest(BaseModel):
    """Form to add a new green action."""
    farmer_id: str
    dimension: str  # 減量, 增匯, 循環, 綠色治理
    action_level: str  # BASIC, SUSTAINED, CERTIFIED
    description: str
    action_date: str  # ISO 8601


@router.post("/green-actions")
def api_create_green_action(request: CreateGreenActionRequest):
    """Create a new green action for a farmer."""
    # Validate dimension
    try:
        dimension = GreenDimension(request.dimension)
    except ValueError:
        valid = [d.value for d in GreenDimension]
        raise HTTPException(
            status_code=400,
            detail=f"無效的構面: {request.dimension}。有效值: {valid}",
        )

    # Validate action level
    try:
        action_level = ActionLevel(request.action_level)
    except ValueError:
        valid = [l.value for l in ActionLevel]
        raise HTTPException(
            status_code=400,
            detail=f"無效的等級: {request.action_level}。有效值: {valid}",
        )

    ga_repo = get_green_action_repo()
    action = GreenAction(
        farmer_id=request.farmer_id,
        dimension=dimension,
        action_level=action_level,
        description=request.description,
        action_date=request.action_date,
        evidence_record_ids=[],
    )
    ga_repo.create(action)

    return {
        "message": "綠色行動已新增",
        "action": action.model_dump(),
    }


@router.get("/farmers/{farmer_id}/green-actions")
def api_get_farmer_green_actions(farmer_id: str):
    """List all green actions for a farmer."""
    ga_repo = get_green_action_repo()
    actions = ga_repo.find_by(farmer_id=farmer_id)
    return {
        "farmer_id": farmer_id,
        "count": len(actions),
        "actions": [a.model_dump() for a in actions],
    }
