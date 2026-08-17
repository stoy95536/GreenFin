"""
Data Health API Endpoints.

Per AGENTS.md §12:
- RED does not mean rejected
- GRAY does not mean poor performance
- Each result includes status, reason, and recommended_action
"""

from fastapi import APIRouter

from backend.app.services.data_health.calculate import (
    calculate_all_data_health,
    get_farmer_data_health,
)

router = APIRouter(tags=["data_health"])


@router.get("/farmers/{farmer_id}/data-health")
def api_get_data_health(farmer_id: str):
    """
    Get per-domain data health status for a farmer.

    Each domain shows GREEN/YELLOW/RED/GRAY with reasons and actions.
    """
    results = get_farmer_data_health(farmer_id)

    domains = {}
    for r in results:
        domains[r.domain.value] = {
            "status": r.status.value,
            "reasons": r.reasons,
            "actions": r.actions,
            "rule_version": r.rule_version,
            "calculated_at": r.calculated_at,
        }

    # Summary counts
    status_counts = {"GREEN": 0, "YELLOW": 0, "RED": 0, "GRAY": 0}
    for r in results:
        status_counts[r.status.value] += 1

    return {
        "farmer_id": farmer_id,
        "domain_count": len(results),
        "summary": status_counts,
        "domains": domains,
        "note": "RED 不代表拒貸；GRAY 不代表表現差",
    }


@router.post("/farmers/{farmer_id}/data-health/calculate")
def api_calculate_data_health(farmer_id: str):
    """
    Recalculate data health for all domains.

    Uses current data and active rule set.
    """
    results = calculate_all_data_health(farmer_id)

    domains = {}
    for r in results:
        domains[r.domain.value] = {
            "status": r.status.value,
            "reasons": r.reasons,
            "actions": r.actions,
        }

    status_counts = {"GREEN": 0, "YELLOW": 0, "RED": 0, "GRAY": 0}
    for r in results:
        status_counts[r.status.value] += 1

    return {
        "farmer_id": farmer_id,
        "message": "Data Health 已重新計算",
        "summary": status_counts,
        "domains": domains,
    }
