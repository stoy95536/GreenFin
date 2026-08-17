"""
Traceability API Endpoints.

Per AGENTS.md §6: Evidence First, Rule Driven, Explainable by Design.
"""

from fastapi import APIRouter, HTTPException

from backend.app.services.traceability import (
    trace_experience_transaction,
    trace_indicator,
    trace_data_health,
    validate_farmer_traceability,
)

router = APIRouter(prefix="/traceability", tags=["traceability"])


@router.get("/experience/{transaction_id}")
def api_trace_experience(transaction_id: str):
    """Trace an experience transaction back to original evidence."""
    result = trace_experience_transaction(transaction_id)
    if not result.valid:
        raise HTTPException(status_code=404, detail=result.message)
    return {
        "valid": result.valid,
        "chain": [{"level": l.level, "type": l.entity_type, "id": l.entity_id, "summary": l.summary, "data": l.data} for l in result.chain],
        "message": result.message,
    }


@router.get("/indicator/{farmer_id}/{indicator_type}")
def api_trace_indicator(farmer_id: str, indicator_type: str):
    """Trace an indicator result back to original evidence."""
    result = trace_indicator(farmer_id, indicator_type)
    if not result.valid:
        raise HTTPException(status_code=404, detail=result.message)
    return {
        "valid": result.valid,
        "chain": [{"level": l.level, "type": l.entity_type, "id": l.entity_id, "summary": l.summary, "data": l.data} for l in result.chain],
        "message": result.message,
    }


@router.get("/data-health/{farmer_id}/{domain}")
def api_trace_data_health(farmer_id: str, domain: str):
    """Trace a data health result back to evidence."""
    result = trace_data_health(farmer_id, domain)
    if not result.valid:
        raise HTTPException(status_code=404, detail=result.message)
    return {
        "valid": result.valid,
        "chain": [{"level": l.level, "type": l.entity_type, "id": l.entity_id, "summary": l.summary, "data": l.data} for l in result.chain],
        "message": result.message,
    }


@router.get("/validate/{farmer_id}")
def api_validate_traceability(farmer_id: str):
    """Validate all traceability chains for a farmer."""
    results = validate_farmer_traceability(farmer_id)
    return results
