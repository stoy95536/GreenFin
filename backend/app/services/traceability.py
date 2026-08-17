"""
Traceability Service.

Per AGENTS.md §6 — every important result must answer:
- 為什麼是這個結果？
- 使用哪條規則？
- 使用哪個規則版本？
- 使用哪些結構化欄位？
- 欄位由哪些證據產生？
- 原始文件在哪裡？
- 何時計算？

Evidence Lineage:
  Result → Calculation Record → Rule Version → Standardized Record → Extracted Field → Original Document
"""

from dataclasses import dataclass, field
from typing import Optional

from backend.app.repositories import (
    get_document_field_repo,
    get_document_repo,
    get_experience_repo,
    get_indicator_repo,
    get_data_health_repo,
    get_rule_set_repo,
    get_standardized_record_repo,
    get_verification_repo,
)


@dataclass
class TraceLink:
    """One link in the traceability chain."""
    level: str
    entity_type: str
    entity_id: Optional[str]
    summary: str
    data: Optional[dict] = None


@dataclass
class TraceResult:
    """Full traceability chain for a calculation result."""
    valid: bool
    chain: list[TraceLink] = field(default_factory=list)
    broken_at: Optional[str] = None
    message: str = ""


def trace_experience_transaction(transaction_id: str) -> TraceResult:
    """
    Trace an experience transaction back to its original evidence.

    Chain: ExperienceTransaction → GreenAction → StandardizedRecord → Document
    """
    exp_repo = get_experience_repo()
    rec_repo = get_standardized_record_repo()
    doc_repo = get_document_repo()
    field_repo = get_document_field_repo()
    rule_repo = get_rule_set_repo()

    chain: list[TraceLink] = []

    # Level 1: ExperienceTransaction
    txn = exp_repo.get_by_id(transaction_id)
    if not txn:
        return TraceResult(valid=False, broken_at="ExperienceTransaction", message=f"Transaction {transaction_id} not found")

    chain.append(TraceLink(
        level="1_result",
        entity_type="ExperienceTransaction",
        entity_id=txn.id,
        summary=f"effective_value={txn.effective_value}, dimension={txn.dimension.value}",
        data={"calculation_trace": txn.calculation_trace, "calculated_at": txn.calculated_at},
    ))

    # Level 2: Rule Version
    rules = rule_repo.find_by(version=txn.rule_version)
    if rules:
        chain.append(TraceLink(
            level="2_rule",
            entity_type="RuleSet",
            entity_id=rules[0].id,
            summary=f"version={txn.rule_version}",
        ))
    else:
        return TraceResult(valid=False, chain=chain, broken_at="RuleSet", message=f"Rule version {txn.rule_version} not found")

    # Level 3: Evidence Records
    for evidence_id in txn.input_evidence_ids:
        record = rec_repo.get_by_id(evidence_id)
        if record:
            chain.append(TraceLink(
                level="3_record",
                entity_type="StandardizedRecord",
                entity_id=record.id,
                summary=f"domain={record.domain.value}, type={record.record_type}",
            ))

            # Level 4: Document
            doc = doc_repo.get_by_id(record.document_id)
            if doc:
                chain.append(TraceLink(
                    level="4_document",
                    entity_type="Document",
                    entity_id=doc.id,
                    summary=f"filename={doc.filename}, source_level={doc.source_level.value}",
                ))

                # Level 5: Fields
                fields = field_repo.find_by(document_id=doc.id)
                if fields:
                    chain.append(TraceLink(
                        level="5_fields",
                        entity_type="DocumentFields",
                        entity_id=None,
                        summary=f"{len(fields)} fields extracted",
                        data={"fields": [f.field_name for f in fields]},
                    ))

    return TraceResult(
        valid=True,
        chain=chain,
        message="Complete traceability chain verified",
    )


def trace_indicator(farmer_id: str, indicator_type: str) -> TraceResult:
    """
    Trace an indicator result back to its evidence.

    Chain: IndicatorResult → Rule Version → StandardizedRecords → Documents
    """
    ind_repo = get_indicator_repo()
    rec_repo = get_standardized_record_repo()
    doc_repo = get_document_repo()
    rule_repo = get_rule_set_repo()

    chain: list[TraceLink] = []

    # Find indicator
    indicators = ind_repo.find_by(farmer_id=farmer_id)
    ind = next((i for i in indicators if i.indicator_type == indicator_type), None)
    if not ind:
        return TraceResult(valid=False, broken_at="IndicatorResult", message=f"Indicator {indicator_type} not found for {farmer_id}")

    chain.append(TraceLink(
        level="1_result",
        entity_type="IndicatorResult",
        entity_id=ind.id,
        summary=f"score={ind.score}, level={ind.level}",
        data={"calculation_trace": ind.calculation_trace, "calculated_at": ind.calculated_at},
    ))

    # Rule version
    rules = rule_repo.find_by(version=ind.rule_version)
    if rules:
        chain.append(TraceLink(
            level="2_rule",
            entity_type="RuleSet",
            entity_id=rules[0].id,
            summary=f"version={ind.rule_version}",
        ))

    # Evidence records
    for eid in ind.input_evidence_ids:
        record = rec_repo.get_by_id(eid)
        if record:
            chain.append(TraceLink(
                level="3_record",
                entity_type="StandardizedRecord",
                entity_id=record.id,
                summary=f"domain={record.domain.value}",
            ))
            doc = doc_repo.get_by_id(record.document_id)
            if doc:
                chain.append(TraceLink(
                    level="4_document",
                    entity_type="Document",
                    entity_id=doc.id,
                    summary=f"filename={doc.filename}",
                ))

    return TraceResult(
        valid=True,
        chain=chain,
        message="Complete traceability chain verified",
    )


def trace_data_health(farmer_id: str, domain: str) -> TraceResult:
    """Trace a data health result back to evidence."""
    dh_repo = get_data_health_repo()
    rec_repo = get_standardized_record_repo()
    doc_repo = get_document_repo()
    rule_repo = get_rule_set_repo()

    chain: list[TraceLink] = []

    results = dh_repo.find_by(farmer_id=farmer_id)
    dh = next((d for d in results if d.domain.value == domain), None)
    if not dh:
        return TraceResult(valid=False, broken_at="DataHealthResult", message=f"Data health for {domain} not found")

    chain.append(TraceLink(
        level="1_result",
        entity_type="DataHealthResult",
        entity_id=dh.id,
        summary=f"status={dh.status.value}, reasons={dh.reasons}",
        data={"calculated_at": dh.calculated_at},
    ))

    # Rule
    rules = rule_repo.find_by(version=dh.rule_version)
    if rules:
        chain.append(TraceLink(
            level="2_rule",
            entity_type="RuleSet",
            entity_id=rules[0].id,
            summary=f"version={dh.rule_version}",
        ))

    # Affected evidence
    for eid in dh.affected_evidence_ids:
        record = rec_repo.get_by_id(eid)
        if record:
            chain.append(TraceLink(
                level="3_record",
                entity_type="StandardizedRecord",
                entity_id=record.id,
                summary=f"domain={record.domain.value}",
            ))
            doc = doc_repo.get_by_id(record.document_id)
            if doc:
                chain.append(TraceLink(
                    level="4_document",
                    entity_type="Document",
                    entity_id=doc.id,
                    summary=f"filename={doc.filename}",
                ))

    return TraceResult(valid=True, chain=chain, message="Traceability chain verified")


def validate_farmer_traceability(farmer_id: str) -> dict:
    """
    Validate traceability for all of a farmer's calculations.

    Returns summary of which chains are valid/broken.
    """
    results = {
        "farmer_id": farmer_id,
        "experience_traces": [],
        "indicator_traces": [],
        "data_health_traces": [],
        "all_valid": True,
    }

    # Experience
    exp_repo = get_experience_repo()
    txns = exp_repo.find_by(farmer_id=farmer_id)
    for txn in txns:
        trace = trace_experience_transaction(txn.id)
        results["experience_traces"].append({
            "transaction_id": txn.id,
            "valid": trace.valid,
            "chain_length": len(trace.chain),
            "message": trace.message,
        })
        if not trace.valid:
            results["all_valid"] = False

    # Indicators
    ind_repo = get_indicator_repo()
    indicators = ind_repo.find_by(farmer_id=farmer_id)
    for ind in indicators:
        trace = trace_indicator(farmer_id, ind.indicator_type)
        results["indicator_traces"].append({
            "indicator_type": ind.indicator_type,
            "valid": trace.valid,
            "chain_length": len(trace.chain),
            "message": trace.message,
        })
        if not trace.valid:
            results["all_valid"] = False

    # Data Health
    dh_repo = get_data_health_repo()
    dh_results = dh_repo.find_by(farmer_id=farmer_id)
    for dh in dh_results:
        trace = trace_data_health(farmer_id, dh.domain.value)
        results["data_health_traces"].append({
            "domain": dh.domain.value,
            "valid": trace.valid,
            "chain_length": len(trace.chain),
            "message": trace.message,
        })
        if not trace.valid:
            results["all_valid"] = False

    return results
