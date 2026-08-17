"""
Rule Engine API Endpoints.

Provides access to rule configuration for transparency and traceability.
Per AGENTS.md §8: rule versions must be accessible and explainable.
"""

from fastapi import APIRouter, HTTPException

from backend.app.repositories import get_rule_set_repo
from backend.app.rules.engine import RuleEngine, RuleEngineError, get_active_engine

router = APIRouter(prefix="/rules", tags=["rules"])


@router.get("/active")
def api_get_active_rules():
    """Get the currently active rule set configuration."""
    try:
        engine = get_active_engine()
    except RuleEngineError as e:
        raise HTTPException(status_code=500, detail=str(e))

    errors = engine.validate_config()

    return {
        "version": engine.version,
        "rule_set": engine.rule_set.model_dump(),
        "validation_errors": errors,
        "is_valid": len(errors) == 0,
    }


@router.get("/active/experience")
def api_get_experience_rules():
    """Get experience calculation rules (base values, ratios, limits)."""
    try:
        engine = get_active_engine()
        rules = engine.get_experience_rules()
    except RuleEngineError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "version": engine.version,
        "dimensions": rules.dimensions,
        "annual_limit_per_dimension": rules.annual_limit_per_dimension,
        "total_limit": rules.total_limit,
        "base_values": rules.base_values,
        "source_ratios": rules.source_ratios,
        "levels": rules.levels,
    }


@router.get("/active/indicators")
def api_get_indicator_rules():
    """Get indicator calculation rules."""
    try:
        engine = get_active_engine()
        rules = engine.get_indicator_rules()
    except RuleEngineError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "version": engine.version,
        "completeness_weights": rules.completeness_weights,
        "credibility_factors": rules.credibility_factors,
        "maturity_factors": rules.maturity_factors,
        "green_maturity_factors": rules.green_maturity_factors,
        "level_thresholds": rules.level_thresholds,
    }


@router.get("/active/data-health")
def api_get_data_health_rules():
    """Get data health rules."""
    try:
        engine = get_active_engine()
        rules = engine.get_data_health_rules()
    except RuleEngineError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "version": engine.version,
        "priority_order": rules.priority_order,
        "domain_required_fields": rules.domain_required_fields,
        "expiry_warning_days": rules.expiry_warning_days,
        "critical_anomaly_types": rules.critical_anomaly_types,
    }


@router.get("/{version}")
def api_get_rules_by_version(version: str):
    """Get a specific rule set by version identifier."""
    try:
        engine = RuleEngine(version=version)
    except RuleEngineError:
        raise HTTPException(status_code=404, detail=f"Rule version '{version}' not found")

    return {
        "version": engine.version,
        "rule_set": engine.rule_set.model_dump(),
        "validation_errors": engine.validate_config(),
    }


@router.get("")
def api_list_rule_versions():
    """List all available rule set versions."""
    repo = get_rule_set_repo()
    rule_sets = repo.get_all()
    return {
        "count": len(rule_sets),
        "versions": [
            {
                "version": rs.version,
                "name": rs.name,
                "is_active": rs.is_active,
                "id": rs.id,
            }
            for rs in rule_sets
        ],
    }
