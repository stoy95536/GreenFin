"""
Four Indicators Calculation Service.

Per RULES.md §4, the four independent indicators are:
1. 資料完整度 (Completeness)
2. 資料可信度 (Credibility)
3. 經營成熟度 (Business Maturity)
4. 綠色成熟度 (Green Maturity)

Each indicator:
- Scored 0-100, level L1-L5
- Must NOT be averaged into a credit score (AGENTS.md §4.2)
- Preserves rule_version, calculated_at, input_evidence_ids, calculation_trace

Rule-driven guarantee (AGENTS.md §6/§7/§8):
  Every weight, threshold and cap is read from the active RuleSet via the rule engine.
  Nothing is hardcoded here. Changing the rule config changes the scores, which is
  what makes the rule_version stamped on each result meaningful.
"""

import math

from backend.app.models import (
    DataDomain,
    IndicatorResult,
    SourceLevel,
)
from backend.app.models.base import now_taipei
from backend.app.repositories import (
    get_anomaly_repo,
    get_document_repo,
    get_experience_repo,
    get_green_action_repo,
    get_indicator_repo,
    get_standardized_record_repo,
)
from backend.app.rules import get_active_engine
from backend.app.services import audit


def _empty_result(farmer_id: str, indicator_type: str, engine, reason: str) -> IndicatorResult:
    """Build a zero-score result with an explicit reason (never a silent 0)."""
    rules = engine.get_indicator_rules()
    return IndicatorResult(
        farmer_id=farmer_id,
        indicator_type=indicator_type,
        score=0.0,
        level=rules.level_for(indicator_type, 0.0),
        details={"reason": reason},
        rule_version=engine.version,
        calculated_at=now_taipei(),
        calculation_trace=(
            f"No qualifying data ({reason}), score=0 (rule_version={engine.version})"
        ),
    )


# ─── Completeness ─────────────────────────────────────────────────────────────


def calculate_completeness(farmer_id: str) -> IndicatorResult:
    """
    Calculate 資料完整度.

    Weighted coverage of expected data domains. Domain→tier mapping and tier weights
    both come from the rule config.
    """
    engine = get_active_engine()
    rules = engine.get_indicator_rules()

    records = get_standardized_record_repo().find_by(farmer_id=farmer_id)

    # Resolve each domain's weight from its configured tier
    domain_weights: dict[str, int] = {}
    for domain, tier in rules.completeness_domain_tiers.items():
        domain_weights[domain] = rules.completeness_weights.get(tier, 0)

    total_weight = sum(domain_weights.values())
    if total_weight == 0:
        return _empty_result(farmer_id, "completeness", engine, "no_domain_weights_configured")

    covered = {r.domain.value for r in records if r.is_valid}

    achieved_weight = 0
    details: dict[str, dict] = {}
    for domain, weight in domain_weights.items():
        has_data = domain in covered
        details[domain] = {
            "has_data": has_data,
            "tier": rules.completeness_domain_tiers.get(domain),
            "weight": weight,
        }
        if has_data:
            achieved_weight += weight

    score = achieved_weight / total_weight * 100
    level = rules.level_for("completeness", score)

    evidence_ids = [r.id for r in records if r.is_valid]
    trace = (
        f"domains_covered={len(covered)}/{len(domain_weights)}, "
        f"weighted={achieved_weight}/{total_weight} = {score:.1f}% "
        f"(rule_version={engine.version})"
    )

    return IndicatorResult(
        farmer_id=farmer_id,
        indicator_type="completeness",
        score=round(score, 1),
        level=level,
        details=details,
        rule_version=engine.version,
        calculated_at=now_taipei(),
        input_evidence_ids=evidence_ids,
        calculation_trace=trace,
    )


# ─── Credibility ──────────────────────────────────────────────────────────────


def calculate_credibility(farmer_id: str) -> IndicatorResult:
    """
    Calculate 資料可信度.

    Average source-level score, minus an anomaly penalty, plus a traceability bonus.
    All coefficients come from the rule config.
    """
    engine = get_active_engine()
    rules = engine.get_indicator_rules()

    records = get_standardized_record_repo().find_by(farmer_id=farmer_id)
    if not records:
        return _empty_result(farmer_id, "credibility", engine, "no_records")

    # Factor 1: average configured score for each record's source level
    source_total = sum(
        rules.credibility_source_scores.get(r.source_level.value, 0) for r in records
    )
    source_avg = source_total / len(records)

    # Factor 2: unresolved anomaly penalty (capped)
    record_ids = {r.id for r in records}
    unresolved = [
        a for a in get_anomaly_repo().get_all()
        if a.record_id in record_ids and not a.is_resolved
    ]
    anomaly_penalty = min(
        len(unresolved) * rules.credibility_anomaly_penalty_per,
        rules.credibility_anomaly_penalty_max,
    )

    # Factor 3: traceability bonus — proportion of records linked to a document
    traceable = sum(1 for r in records if r.document_id)
    traceability_ratio = traceable / len(records)
    traceability_bonus = traceability_ratio * rules.credibility_traceability_bonus_max

    score = max(0.0, min(100.0, source_avg - anomaly_penalty + traceability_bonus))
    level = rules.level_for("credibility", score)

    details = {
        "source_avg": round(source_avg, 1),
        "anomaly_penalty": anomaly_penalty,
        "traceability_bonus": round(traceability_bonus, 1),
        "record_count": len(records),
        "unresolved_anomalies": len(unresolved),
    }
    trace = (
        f"source_avg={source_avg:.1f} - anomaly_penalty={anomaly_penalty} "
        f"+ traceability_bonus={traceability_bonus:.1f} = {score:.1f} "
        f"(rule_version={engine.version})"
    )

    return IndicatorResult(
        farmer_id=farmer_id,
        indicator_type="credibility",
        score=round(score, 1),
        level=level,
        details=details,
        rule_version=engine.version,
        calculated_at=now_taipei(),
        input_evidence_ids=[r.id for r in records],
        calculation_trace=trace,
    )


# ─── Business Maturity ────────────────────────────────────────────────────────


def calculate_business_maturity(farmer_id: str) -> IndicatorResult:
    """
    Calculate 經營成熟度.

    Domain variety + record volume (log-saturating) + document count + a bonus for
    having transaction records. All caps and saturation points are configured.
    """
    engine = get_active_engine()
    rules = engine.get_indicator_rules()

    records = get_standardized_record_repo().find_by(farmer_id=farmer_id)
    documents = get_document_repo().find_by(farmer_id=farmer_id)

    if not records and not documents:
        return _empty_result(farmer_id, "business_maturity", engine, "no_data")

    total_domains = len(rules.completeness_domain_tiers) or len(DataDomain)

    # Factor 1: domain variety
    domains_covered = {r.domain.value for r in records}
    variety_score = min(
        len(domains_covered) / total_domains * rules.maturity_variety_max,
        rules.maturity_variety_max,
    )

    # Factor 2: record volume, log-saturating toward the configured saturation point
    saturation = max(2, rules.maturity_volume_saturation_records)
    volume_score = min(
        math.log2(len(records) + 1) / math.log2(saturation) * rules.maturity_volume_max,
        rules.maturity_volume_max,
    )

    # Factor 3: document count
    doc_saturation = max(1, rules.maturity_document_saturation_count)
    doc_score = min(
        len(documents) / doc_saturation * rules.maturity_document_max,
        rules.maturity_document_max,
    )

    # Factor 4: economic activity evidence
    has_transactions = any(r.domain == DataDomain.TRANSACTION for r in records)
    transaction_bonus = rules.maturity_transaction_bonus if has_transactions else 0

    score = min(100.0, variety_score + volume_score + doc_score + transaction_bonus)
    level = rules.level_for("business_maturity", score)

    details = {
        "domains_covered": len(domains_covered),
        "record_count": len(records),
        "document_count": len(documents),
        "has_transactions": has_transactions,
        "variety_score": round(variety_score, 1),
        "volume_score": round(volume_score, 1),
        "doc_score": round(doc_score, 1),
        "transaction_bonus": transaction_bonus,
    }
    trace = (
        f"variety={variety_score:.1f} + volume={volume_score:.1f} "
        f"+ docs={doc_score:.1f} + txn_bonus={transaction_bonus} = {score:.1f} "
        f"(rule_version={engine.version})"
    )

    return IndicatorResult(
        farmer_id=farmer_id,
        indicator_type="business_maturity",
        score=round(score, 1),
        level=level,
        details=details,
        rule_version=engine.version,
        calculated_at=now_taipei(),
        input_evidence_ids=[r.id for r in records],
        calculation_trace=trace,
    )


# ─── Green Maturity ───────────────────────────────────────────────────────────


def calculate_green_maturity(farmer_id: str) -> IndicatorResult:
    """
    Calculate 綠色成熟度.

    Experience contribution + dimension breadth + V2/V3 evidence quality.

    Note per RULES.md §4: this references experience but is deliberately NOT equal to
    it, and must never be converted into a credit score.
    """
    engine = get_active_engine()
    rules = engine.get_indicator_rules()
    exp_rules = engine.get_experience_rules()

    transactions = get_experience_repo().find_by(farmer_id=farmer_id)
    actions = get_green_action_repo().find_by(farmer_id=farmer_id)
    green_records = get_standardized_record_repo().find_by(
        farmer_id=farmer_id, domain=DataDomain.GREEN_ACTION.value
    )

    if not transactions and not actions:
        return _empty_result(farmer_id, "green_maturity", engine, "no_green_data")

    # Factor 1: experience contribution, scaled against the configured total limit
    total_exp = sum(t.effective_value for t in transactions)
    total_limit = exp_rules.total_limit or 1
    exp_score = min(total_exp / total_limit * rules.green_experience_max, rules.green_experience_max)

    # Factor 2: dimension breadth, capped at the configured dimension count
    active_dims = {t.dimension.value for t in transactions if t.effective_value > 0}
    max_breadth = len(exp_rules.dimensions) * rules.green_breadth_per_dimension
    breadth_score = min(len(active_dims) * rules.green_breadth_per_dimension, max_breadth)

    # Factor 3: proportion of green evidence at V2/V3
    high_quality = sum(
        1 for r in green_records if r.source_level in (SourceLevel.V2, SourceLevel.V3)
    )
    v2v3_ratio = high_quality / len(green_records) if green_records else 0.0
    quality_score = v2v3_ratio * rules.green_quality_max

    score = min(100.0, exp_score + breadth_score + quality_score)
    level = rules.level_for("green_maturity", score)

    details = {
        "total_experience": total_exp,
        "active_dimensions": len(active_dims),
        "green_record_count": len(green_records),
        "v2_v3_ratio": round(v2v3_ratio, 2),
        "exp_score": round(exp_score, 1),
        "breadth_score": breadth_score,
        "quality_score": round(quality_score, 1),
    }
    trace = (
        f"exp_contribution={exp_score:.1f} + breadth={breadth_score} "
        f"+ quality={quality_score:.1f} = {score:.1f} "
        f"(rule_version={engine.version})"
    )

    return IndicatorResult(
        farmer_id=farmer_id,
        indicator_type="green_maturity",
        score=round(score, 1),
        level=level,
        details=details,
        rule_version=engine.version,
        calculated_at=now_taipei(),
        input_evidence_ids=[t.id for t in transactions],
        calculation_trace=trace,
    )


# ─── Orchestration ────────────────────────────────────────────────────────────


def calculate_all_indicators(farmer_id: str) -> list[IndicatorResult]:
    """
    Calculate all four indicators for a farmer and persist results.

    Existing results for the farmer are replaced. Returns the 4 new results.
    """
    ind_repo = get_indicator_repo()

    for existing in ind_repo.find_by(farmer_id=farmer_id):
        ind_repo.delete(existing.id)

    results = [
        calculate_completeness(farmer_id),
        calculate_credibility(farmer_id),
        calculate_business_maturity(farmer_id),
        calculate_green_maturity(farmer_id),
    ]

    for result in results:
        ind_repo.create(result)

    audit.indicator_recalculated(
        farmer_id=farmer_id,
        rule_version=results[0].rule_version if results else "unknown",
        scores={r.indicator_type: r.score for r in results},
    )

    return results


def get_farmer_indicators(farmer_id: str) -> list[IndicatorResult]:
    """Get stored indicator results for a farmer."""
    return get_indicator_repo().find_by(farmer_id=farmer_id)
