"""
Four Indicators API Endpoints.

Per AGENTS.md §4.2: four indicators must be presented independently,
NEVER averaged into a credit score.

- GET /api/farmers/{id}/indicators — get current indicator results
- POST /api/farmers/{id}/indicators/calculate — recalculate all four
"""

from fastapi import APIRouter

from backend.app.services.indicators.calculate import (
    calculate_all_indicators,
    get_farmer_indicators,
)

router = APIRouter(tags=["indicators"])


@router.get("/farmers/{farmer_id}/indicators")
def api_get_indicators(farmer_id: str):
    """
    Get the four analysis indicators for a farmer.

    Returns completeness, credibility, business_maturity, green_maturity.
    Each indicator is independent — they must NOT be combined into a single score.
    """
    results = get_farmer_indicators(farmer_id)

    indicators = {}
    for r in results:
        indicators[r.indicator_type] = {
            "score": r.score,
            "level": r.level,
            "details": r.details,
            "rule_version": r.rule_version,
            "calculated_at": r.calculated_at,
            # Required for "Explainable by Design" (AGENTS.md §6): the farmer must be
            # able to see how the score was produced, not just the number.
            "calculation_trace": r.calculation_trace,
        }

    return {
        "farmer_id": farmer_id,
        "indicator_count": len(results),
        "indicators": indicators,
        "note": "四項指標須獨立呈現，不得直接平均成信用總分",
    }


@router.post("/farmers/{farmer_id}/indicators/calculate")
def api_calculate_indicators(farmer_id: str):
    """
    Recalculate all four indicators for a farmer.

    Uses current data and active rule set.
    """
    results = calculate_all_indicators(farmer_id)

    indicators = {}
    for r in results:
        indicators[r.indicator_type] = {
            "score": r.score,
            "level": r.level,
            "calculation_trace": r.calculation_trace,
        }

    return {
        "farmer_id": farmer_id,
        "message": "四大指標已重新計算",
        "indicators": indicators,
        "rule_version": results[0].rule_version if results else None,
    }
