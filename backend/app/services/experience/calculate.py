"""
Experience Calculation Service.

Per RULES.md §3:
- Four dimensions: 減量, 增匯, 循環, 綠色治理
- Annual limit per dimension: 250
- Total limit: 1000
- Formula: effective_value = base_value × source_recognition_ratio
- Base values: BASIC=20, SUSTAINED=50, CERTIFIED=100
- Source ratios: V3=1.0, V2=1.0, V1=0.5, V0=0.0

Per AGENTS.md §8:
- Every calculation preserves: rule_version, calculated_at, input_evidence_ids, calculation_trace
"""

from datetime import datetime, timezone
from typing import Optional

from backend.app.models import (
    ActionLevel,
    ExperienceLevel,
    ExperienceTransaction,
    GreenAction,
    GreenDimension,
    SourceLevel,
)
from backend.app.models.base import now_taipei
from backend.app.repositories import (
    get_experience_repo,
    get_green_action_repo,
    get_verification_repo,
    get_standardized_record_repo,
)
from backend.app.rules import get_active_engine


class ExperienceError(Exception):
    """Experience calculation error."""
    pass


def calculate_experience(green_action: GreenAction) -> ExperienceTransaction:
    """
    Calculate experience value for a single green action.

    Steps:
    1. Get base value from action level (via rule engine)
    2. Determine source recognition ratio from evidence verification level
    3. Check dimension annual limit
    4. Check total limit
    5. Check duplicate protection
    6. Create ExperienceTransaction with full trace

    Args:
        green_action: The GreenAction to calculate experience for.

    Returns:
        Created ExperienceTransaction.

    Raises:
        ExperienceError: If calculation cannot proceed.
    """
    engine = get_active_engine()
    exp_rules = engine.get_experience_rules()
    exp_repo = get_experience_repo()

    # Step 1: Get base value
    base_value = exp_rules.base_values.get(green_action.action_level.value)
    if base_value is None:
        raise ExperienceError(f"Unknown action level: {green_action.action_level}")

    # Step 2: Determine source recognition ratio
    source_ratio = _determine_source_ratio(green_action, exp_rules.source_ratios)

    # Step 3: Calculate effective value
    effective_value = base_value * source_ratio

    # Step 4: Check duplicate protection
    existing = exp_repo.find_by(green_action_id=green_action.id)
    if existing:
        raise ExperienceError(
            f"此綠色行動已計算過經驗值 (transaction_id: {existing[0].id})"
        )

    # Step 5: Check dimension annual limit
    dimension_total = _get_dimension_annual_total(
        green_action.farmer_id, green_action.dimension
    )
    if dimension_total + effective_value > exp_rules.annual_limit_per_dimension:
        # Cap at limit
        remaining = max(0, exp_rules.annual_limit_per_dimension - dimension_total)
        effective_value = min(effective_value, remaining)

    # Step 6: Check total limit
    total = _get_farmer_total(green_action.farmer_id)
    if total + effective_value > exp_rules.total_limit:
        remaining = max(0, exp_rules.total_limit - total)
        effective_value = min(effective_value, remaining)

    # Build evidence IDs list
    evidence_ids = list(green_action.evidence_record_ids)

    # Build calculation trace
    trace_text = (
        f"{green_action.action_level.value}({base_value}) "
        f"× source_ratio({source_ratio}) = {effective_value}"
    )
    if effective_value < base_value * source_ratio:
        trace_text += " (capped by limit)"

    # Create transaction
    transaction = ExperienceTransaction(
        farmer_id=green_action.farmer_id,
        green_action_id=green_action.id,
        dimension=green_action.dimension,
        base_value=base_value,
        source_recognition_ratio=source_ratio,
        effective_value=effective_value,
        rule_version=engine.version,
        calculated_at=now_taipei(),
        input_evidence_ids=evidence_ids,
        calculation_trace=trace_text,
    )
    exp_repo.create(transaction)

    return transaction


def get_farmer_experience_summary(farmer_id: str) -> dict:
    """
    Get a farmer's experience summary.

    Returns:
        Dict with total, per-dimension breakdown, level, and transaction count.
    """
    engine = get_active_engine()
    exp_rules = engine.get_experience_rules()
    exp_repo = get_experience_repo()

    transactions = exp_repo.find_by(farmer_id=farmer_id)

    # Per-dimension totals
    dimension_totals: dict[str, float] = {}
    for dim in exp_rules.dimensions:
        dim_txns = [t for t in transactions if t.dimension.value == dim]
        dimension_totals[dim] = sum(t.effective_value for t in dim_txns)

    total = sum(dimension_totals.values())
    level = _determine_level(total, exp_rules.levels)

    return {
        "farmer_id": farmer_id,
        "total_experience": total,
        "level": level,
        "level_label": _get_level_label(level),
        "dimensions": dimension_totals,
        "transaction_count": len(transactions),
        "annual_limit_per_dimension": exp_rules.annual_limit_per_dimension,
        "total_limit": exp_rules.total_limit,
        "rule_version": engine.version,
    }


def get_farmer_experience_history(farmer_id: str) -> list[ExperienceTransaction]:
    """Get all experience transactions for a farmer, ordered by creation."""
    exp_repo = get_experience_repo()
    return exp_repo.find_by(farmer_id=farmer_id)


def recalculate_farmer_experience(farmer_id: str) -> dict:
    """
    Recalculate all experience for a farmer from their green actions.

    Clears existing transactions and recalculates from scratch.
    Used when rules change or actions are updated.

    Returns:
        New experience summary.
    """
    exp_repo = get_experience_repo()
    ga_repo = get_green_action_repo()

    # Clear existing transactions for this farmer
    existing = exp_repo.find_by(farmer_id=farmer_id)
    for txn in existing:
        exp_repo.delete(txn.id)

    # Get all active green actions
    actions = ga_repo.find_by(farmer_id=farmer_id)
    active_actions = [a for a in actions if a.is_active]

    # Recalculate each
    for action in active_actions:
        try:
            calculate_experience(action)
        except ExperienceError:
            pass  # Skip actions that can't be calculated (e.g., over limit)

    return get_farmer_experience_summary(farmer_id)


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _determine_source_ratio(green_action: GreenAction, source_ratios: dict[str, float]) -> float:
    """
    Determine source recognition ratio based on evidence verification level.

    Looks at the verification results of the action's evidence records.
    Uses the lowest verification level found.
    """
    if not green_action.evidence_record_ids:
        # No evidence → treat as V1 (self-submitted)
        return source_ratios.get("V1", 0.5)

    ver_repo = get_verification_repo()
    rec_repo = get_standardized_record_repo()

    # Find the lowest source level among evidence
    lowest_level = SourceLevel.V3  # Start optimistic

    for record_id in green_action.evidence_record_ids:
        # Check verification results
        verifications = ver_repo.find_by(record_id=record_id)
        if verifications:
            for v in verifications:
                level_order = {"V0": 0, "V1": 1, "V2": 2, "V3": 3}
                if level_order.get(v.source_level.value, 0) < level_order.get(lowest_level.value, 3):
                    lowest_level = v.source_level
        else:
            # No verification → check record's source level
            record = rec_repo.get_by_id(record_id)
            if record:
                level_order = {"V0": 0, "V1": 1, "V2": 2, "V3": 3}
                if level_order.get(record.source_level.value, 0) < level_order.get(lowest_level.value, 3):
                    lowest_level = record.source_level
            else:
                lowest_level = SourceLevel.V1

    return source_ratios.get(lowest_level.value, 0.5)


def _get_dimension_annual_total(farmer_id: str, dimension: GreenDimension) -> float:
    """Get current year's total for a dimension."""
    exp_repo = get_experience_repo()
    transactions = exp_repo.find_by(farmer_id=farmer_id)

    current_year = str(datetime.now(timezone.utc).year)
    return sum(
        t.effective_value
        for t in transactions
        if t.dimension == dimension and current_year in t.calculated_at
    )


def _get_farmer_total(farmer_id: str) -> float:
    """Get farmer's total experience value."""
    exp_repo = get_experience_repo()
    transactions = exp_repo.find_by(farmer_id=farmer_id)
    return sum(t.effective_value for t in transactions)


def _determine_level(total: float, levels: dict[str, list[int]]) -> str:
    """Determine experience level from total value."""
    for level_name, (min_val, max_val) in sorted(
        levels.items(), key=lambda x: x[1][1], reverse=True
    ):
        if total >= min_val:
            return level_name
    return "L0"


def _get_level_label(level: str) -> str:
    """Get Chinese label for experience level."""
    labels = {
        "L0": "尚未建立",
        "L1": "萌芽",
        "L2": "成長",
        "L3": "穩健",
        "L4": "領航",
        "L5": "示範",
    }
    return labels.get(level, "未知")
