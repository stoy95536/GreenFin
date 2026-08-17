"""
Four Indicators Calculation Service.

Per RULES.md §4, the four independent indicators are:
1. 資料完整度 (Completeness) — how complete is the farmer's data
2. 資料可信度 (Credibility) — how trustworthy/verifiable is the data
3. 經營成熟度 (Business Maturity) — how mature is the farming operation
4. 綠色成熟度 (Green Maturity) — how mature are green practices

Each indicator:
- Scored 0-100
- Level L1-L5
- Must NOT be averaged into a credit score (AGENTS.md §4.2)
- Must preserve rule_version, calculated_at, input_evidence_ids, calculation_trace
"""

from backend.app.models import (
    DataDomain,
    GreenDimension,
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
    get_verification_repo,
)
from backend.app.rules import get_active_engine


# ─── Level determination ──────────────────────────────────────────────────────

COMPLETENESS_LEVELS = [(95, "L5"), (80, "L4"), (60, "L3"), (40, "L2"), (0, "L1")]
CREDIBILITY_LEVELS = [(80, "L5"), (60, "L4"), (40, "L3"), (20, "L2"), (0, "L1")]
MATURITY_LEVELS = [(80, "L5"), (60, "L4"), (40, "L3"), (20, "L2"), (0, "L1")]


def _score_to_level(score: float, thresholds: list[tuple[int, str]]) -> str:
    """Convert a 0-100 score to level using thresholds."""
    for min_score, level in thresholds:
        if score >= min_score:
            return level
    return "L1"


# ─── Completeness ─────────────────────────────────────────────────────────────


def calculate_completeness(farmer_id: str) -> IndicatorResult:
    """
    Calculate 資料完整度.

    Measures what proportion of expected data domains have records.
    Weighted: core_required=3, important_supporting=2, supplementary=1.
    """
    engine = get_active_engine()
    rec_repo = get_standardized_record_repo()
    records = rec_repo.find_by(farmer_id=farmer_id)

    # Define domain weights
    domain_weights = {
        DataDomain.IDENTITY.value: 3,       # core
        DataDomain.LAND_CROP.value: 3,      # core
        DataDomain.TRANSACTION.value: 2,    # important
        DataDomain.CERTIFICATION.value: 2,  # important
        DataDomain.GREEN_ACTION.value: 2,   # important
        DataDomain.INPUT_EQUIPMENT.value: 1,  # supplementary
        DataDomain.LOAN_PURPOSE.value: 1,   # supplementary
    }

    total_weight = sum(domain_weights.values())
    achieved_weight = 0
    details = {}

    # Check which domains have valid records
    farmer_domains = set()
    for r in records:
        if r.is_valid:
            farmer_domains.add(r.domain.value)

    for domain, weight in domain_weights.items():
        has_data = domain in farmer_domains
        details[domain] = {"has_data": has_data, "weight": weight}
        if has_data:
            achieved_weight += weight

    score = (achieved_weight / total_weight * 100) if total_weight > 0 else 0
    level = _score_to_level(score, COMPLETENESS_LEVELS)

    evidence_ids = [r.id for r in records if r.is_valid]
    trace = f"Domains covered: {len(farmer_domains)}/{len(domain_weights)}, weighted score: {achieved_weight}/{total_weight} = {score:.1f}%"

    result = IndicatorResult(
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
    return result


# ─── Credibility ──────────────────────────────────────────────────────────────


def calculate_credibility(farmer_id: str) -> IndicatorResult:
    """
    Calculate 資料可信度.

    Based on:
    - Source verification levels (V0-V3)
    - Expiry status
    - Anomaly count
    - Traceability (records linked to documents)
    """
    engine = get_active_engine()
    rec_repo = get_standardized_record_repo()
    ver_repo = get_verification_repo()
    anomaly_repo = get_anomaly_repo()

    records = rec_repo.find_by(farmer_id=farmer_id)
    if not records:
        result = IndicatorResult(
            farmer_id=farmer_id,
            indicator_type="credibility",
            score=0.0, level="L1",
            details={"reason": "no_records"},
            rule_version=engine.version,
            calculated_at=now_taipei(),
            calculation_trace="No records found, score=0",
        )
        return result

    # Factor 1: Average source level (V0=0, V1=33, V2=67, V3=100)
    level_scores = {"V0": 0, "V1": 33, "V2": 67, "V3": 100}
    source_total = 0
    for r in records:
        source_total += level_scores.get(r.source_level.value, 0)
    source_avg = source_total / len(records)

    # Factor 2: Anomaly penalty (each unresolved anomaly -5, max -30)
    all_anomalies = anomaly_repo.get_all()
    record_ids = {r.id for r in records}
    farmer_anomalies = [a for a in all_anomalies if a.record_id in record_ids and not a.is_resolved]
    anomaly_penalty = min(len(farmer_anomalies) * 5, 30)

    # Factor 3: Traceability bonus (records with document link)
    traceable = sum(1 for r in records if r.document_id)
    traceability_ratio = traceable / len(records) if records else 0
    traceability_bonus = traceability_ratio * 10  # max 10 points

    score = max(0, min(100, source_avg - anomaly_penalty + traceability_bonus))
    level = _score_to_level(score, CREDIBILITY_LEVELS)

    details = {
        "source_avg": round(source_avg, 1),
        "anomaly_penalty": anomaly_penalty,
        "traceability_bonus": round(traceability_bonus, 1),
        "record_count": len(records),
        "unresolved_anomalies": len(farmer_anomalies),
    }
    trace = (
        f"source_avg={source_avg:.1f} - anomaly_penalty={anomaly_penalty} "
        f"+ traceability_bonus={traceability_bonus:.1f} = {score:.1f}"
    )

    result = IndicatorResult(
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
    return result


# ─── Business Maturity ────────────────────────────────────────────────────────


def calculate_business_maturity(farmer_id: str) -> IndicatorResult:
    """
    Calculate 經營成熟度.

    Based on:
    - Record variety (how many different domains)
    - Record count (volume of evidence)
    - Document count (breadth of documentation)
    - Transaction records (economic activity)
    """
    engine = get_active_engine()
    rec_repo = get_standardized_record_repo()
    doc_repo = get_document_repo()

    records = rec_repo.find_by(farmer_id=farmer_id)
    documents = doc_repo.find_by(farmer_id=farmer_id)

    if not records and not documents:
        result = IndicatorResult(
            farmer_id=farmer_id,
            indicator_type="business_maturity",
            score=0.0, level="L1",
            details={"reason": "no_data"},
            rule_version=engine.version,
            calculated_at=now_taipei(),
            calculation_trace="No records or documents, score=0",
        )
        return result

    # Factor 1: Domain variety (max 7 domains, each worth ~14 points, max 40)
    domains_covered = set(r.domain.value for r in records)
    variety_score = min(len(domains_covered) / 7 * 40, 40)

    # Factor 2: Record volume (logarithmic, max 30 points)
    import math
    volume_score = min(math.log2(len(records) + 1) / math.log2(20) * 30, 30)

    # Factor 3: Document count (max 20 points)
    doc_score = min(len(documents) / 10 * 20, 20)

    # Factor 4: Has transaction records (10 points)
    has_transactions = any(r.domain.value == DataDomain.TRANSACTION.value for r in records)
    transaction_bonus = 10 if has_transactions else 0

    score = min(100, variety_score + volume_score + doc_score + transaction_bonus)
    level = _score_to_level(score, MATURITY_LEVELS)

    details = {
        "domains_covered": len(domains_covered),
        "record_count": len(records),
        "document_count": len(documents),
        "has_transactions": has_transactions,
        "variety_score": round(variety_score, 1),
        "volume_score": round(volume_score, 1),
        "doc_score": round(doc_score, 1),
    }
    trace = (
        f"variety={variety_score:.1f} + volume={volume_score:.1f} "
        f"+ docs={doc_score:.1f} + txn_bonus={transaction_bonus} = {score:.1f}"
    )

    result = IndicatorResult(
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
    return result


# ─── Green Maturity ───────────────────────────────────────────────────────────


def calculate_green_maturity(farmer_id: str) -> IndicatorResult:
    """
    Calculate 綠色成熟度.

    Based on:
    - Experience value total
    - Dimension breadth (how many of 4 dimensions)
    - V2/V3 ratio in green actions
    - Anomaly count in green domain

    Note: green_maturity references experience but is NOT equal to it (RULES.md §4).
    """
    engine = get_active_engine()
    exp_repo = get_experience_repo()
    ga_repo = get_green_action_repo()
    rec_repo = get_standardized_record_repo()

    transactions = exp_repo.find_by(farmer_id=farmer_id)
    actions = ga_repo.find_by(farmer_id=farmer_id)
    green_records = rec_repo.find_by(farmer_id=farmer_id, domain=DataDomain.GREEN_ACTION.value)

    if not transactions and not actions:
        result = IndicatorResult(
            farmer_id=farmer_id,
            indicator_type="green_maturity",
            score=0.0, level="L1",
            details={"reason": "no_green_data"},
            rule_version=engine.version,
            calculated_at=now_taipei(),
            calculation_trace="No green actions or experience, score=0",
        )
        return result

    # Factor 1: Experience value contribution (max 40 points, scaled to 1000 limit)
    total_exp = sum(t.effective_value for t in transactions)
    exp_score = min(total_exp / 1000 * 40, 40)

    # Factor 2: Dimension breadth (each of 4 dims = 10 points, max 40)
    active_dims = set(t.dimension.value for t in transactions if t.effective_value > 0)
    breadth_score = len(active_dims) * 10

    # Factor 3: V2/V3 ratio in green evidence (max 20 points)
    high_quality = sum(1 for r in green_records if r.source_level in (SourceLevel.V2, SourceLevel.V3))
    v2v3_ratio = high_quality / len(green_records) if green_records else 0
    quality_score = v2v3_ratio * 20

    score = min(100, exp_score + breadth_score + quality_score)
    level = _score_to_level(score, MATURITY_LEVELS)

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
        f"+ quality={quality_score:.1f} = {score:.1f}"
    )

    result = IndicatorResult(
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
    return result


# ─── Orchestration ────────────────────────────────────────────────────────────


def calculate_all_indicators(farmer_id: str) -> list[IndicatorResult]:
    """
    Calculate all four indicators for a farmer and persist results.

    Returns list of 4 IndicatorResult entities.
    """
    ind_repo = get_indicator_repo()

    # Remove existing results for this farmer
    existing = ind_repo.find_by(farmer_id=farmer_id)
    for e in existing:
        ind_repo.delete(e.id)

    results = [
        calculate_completeness(farmer_id),
        calculate_credibility(farmer_id),
        calculate_business_maturity(farmer_id),
        calculate_green_maturity(farmer_id),
    ]

    for r in results:
        ind_repo.create(r)

    return results


def get_farmer_indicators(farmer_id: str) -> list[IndicatorResult]:
    """Get stored indicator results for a farmer."""
    ind_repo = get_indicator_repo()
    return ind_repo.find_by(farmer_id=farmer_id)
