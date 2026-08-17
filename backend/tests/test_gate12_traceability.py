"""
GATE-12 Tests: Traceability

Verifies that all major calculations can be traced:
  Result → Calculation → Rule Version → Structured Record → Evidence → Original Document

Per DEVELOPMENT_PLAN.md: all major calculations must pass traceability.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.models import (
    DataDomain, DataHealthResult, DataHealthStatus, Document, DocumentField,
    DocumentStatus, ExperienceTransaction, GreenDimension, IndicatorResult,
    RuleSet, SourceLevel, StandardizedRecord,
)
from backend.app.repositories import (
    get_data_health_repo, get_document_field_repo, get_document_repo,
    get_experience_repo, get_indicator_repo, get_rule_set_repo,
    get_standardized_record_repo,
)
from backend.app.services.traceability import (
    trace_data_health,
    trace_experience_transaction,
    trace_indicator,
    validate_farmer_traceability,
)


def _seed_traceable_data():
    """Create a complete traceable data set."""
    get_rule_set_repo().clear()
    get_document_repo().clear()
    get_document_field_repo().clear()
    get_standardized_record_repo().clear()
    get_experience_repo().clear()
    get_indicator_repo().clear()
    get_data_health_repo().clear()

    # Rule
    get_rule_set_repo().create(RuleSet(
        id="rs-trace", version="TRACE_V1", name="Trace Test", is_active=True,
        config={"experience": {
            "dimensions": ["減量", "增匯", "循環", "綠色治理"],
            "annual_limit_per_dimension": 250, "total_limit": 1000,
            "base_values": {"BASIC": 20, "SUSTAINED": 50, "CERTIFIED": 100},
            "source_ratios": {"V3": 1.0, "V2": 1.0, "V1": 0.5, "V0": 0.0},
            "levels": {"L0": [0, 0], "L1": [1, 200], "L2": [201, 400],
                       "L3": [401, 600], "L4": [601, 800], "L5": [801, 1000]},
        }},
    ))

    # Document
    get_document_repo().create(Document(
        id="trace-doc", farmer_id="farmer-trace", filename="organic_cert.pdf",
        domain=DataDomain.CERTIFICATION, source_level=SourceLevel.V3,
        status=DocumentStatus.VERIFIED,
    ))

    # Fields
    get_document_field_repo().create(DocumentField(
        id="trace-field-1", document_id="trace-doc",
        field_name="認證機構", raw_value="慈心基金會",
        normalized_value="慈心基金會", confidence=0.95,
    ))
    get_document_field_repo().create(DocumentField(
        id="trace-field-2", document_id="trace-doc",
        field_name="有效期限", raw_value="2027-06-30",
        normalized_value="2027-06-30", confidence=0.92,
    ))

    # Record
    get_standardized_record_repo().create(StandardizedRecord(
        id="trace-rec", document_id="trace-doc", farmer_id="farmer-trace",
        domain=DataDomain.CERTIFICATION, record_type="certification_record",
        source_level=SourceLevel.V3, data={"認證機構": "慈心基金會", "有效期限": "2027-06-30"},
    ))

    # Experience Transaction
    get_experience_repo().create(ExperienceTransaction(
        id="trace-exp", farmer_id="farmer-trace", green_action_id="ga-trace",
        dimension=GreenDimension.REDUCTION, base_value=100,
        source_recognition_ratio=1.0, effective_value=100.0,
        rule_version="TRACE_V1", calculated_at="2026-08-17T10:00:00+08:00",
        input_evidence_ids=["trace-rec"],
        calculation_trace="CERTIFIED(100) × V3(1.0) = 100",
    ))

    # Indicator
    get_indicator_repo().create(IndicatorResult(
        id="trace-ind", farmer_id="farmer-trace",
        indicator_type="completeness", score=85.0, level="L4",
        rule_version="TRACE_V1", calculated_at="2026-08-17T10:00:00+08:00",
        input_evidence_ids=["trace-rec"],
        calculation_trace="Domain coverage: 1/7 weighted",
    ))

    # Data Health
    get_data_health_repo().create(DataHealthResult(
        id="trace-dh", farmer_id="farmer-trace",
        domain=DataDomain.CERTIFICATION, status=DataHealthStatus.GREEN,
        reasons=["認證有效"], actions=[],
        affected_evidence_ids=["trace-rec"],
        rule_version="TRACE_V1", calculated_at="2026-08-17T10:00:00+08:00",
    ))


class TestExperienceTraceability:
    """Test experience transaction traceability."""

    def test_valid_chain(self, test_data_dir):
        _seed_traceable_data()
        result = trace_experience_transaction("trace-exp")
        assert result.valid is True
        assert len(result.chain) >= 4  # result, rule, record, document

    def test_chain_includes_rule_version(self, test_data_dir):
        _seed_traceable_data()
        result = trace_experience_transaction("trace-exp")
        rule_links = [l for l in result.chain if l.level == "2_rule"]
        assert len(rule_links) == 1
        assert "TRACE_V1" in rule_links[0].summary

    def test_chain_includes_document(self, test_data_dir):
        _seed_traceable_data()
        result = trace_experience_transaction("trace-exp")
        doc_links = [l for l in result.chain if l.level == "4_document"]
        assert len(doc_links) >= 1
        assert "organic_cert.pdf" in doc_links[0].summary

    def test_chain_includes_fields(self, test_data_dir):
        _seed_traceable_data()
        result = trace_experience_transaction("trace-exp")
        field_links = [l for l in result.chain if l.level == "5_fields"]
        assert len(field_links) >= 1

    def test_nonexistent_transaction(self, test_data_dir):
        _seed_traceable_data()
        result = trace_experience_transaction("nonexistent")
        assert result.valid is False
        assert result.broken_at == "ExperienceTransaction"


class TestIndicatorTraceability:
    """Test indicator result traceability."""

    def test_valid_chain(self, test_data_dir):
        _seed_traceable_data()
        result = trace_indicator("farmer-trace", "completeness")
        assert result.valid is True
        assert len(result.chain) >= 3

    def test_includes_calculation_trace(self, test_data_dir):
        _seed_traceable_data()
        result = trace_indicator("farmer-trace", "completeness")
        result_link = result.chain[0]
        assert result_link.data["calculation_trace"] is not None

    def test_nonexistent_indicator(self, test_data_dir):
        _seed_traceable_data()
        result = trace_indicator("farmer-trace", "nonexistent_type")
        assert result.valid is False


class TestDataHealthTraceability:
    """Test data health traceability."""

    def test_valid_chain(self, test_data_dir):
        _seed_traceable_data()
        result = trace_data_health("farmer-trace", "CERTIFICATION")
        assert result.valid is True
        assert len(result.chain) >= 3

    def test_includes_status_and_reasons(self, test_data_dir):
        _seed_traceable_data()
        result = trace_data_health("farmer-trace", "CERTIFICATION")
        first = result.chain[0]
        assert "GREEN" in first.summary

    def test_nonexistent_domain(self, test_data_dir):
        _seed_traceable_data()
        result = trace_data_health("farmer-trace", "NONEXISTENT")
        assert result.valid is False


class TestValidateAllTraceability:
    """Test full farmer traceability validation."""

    def test_all_valid(self, test_data_dir):
        _seed_traceable_data()
        results = validate_farmer_traceability("farmer-trace")
        assert results["all_valid"] is True

    def test_has_experience_traces(self, test_data_dir):
        _seed_traceable_data()
        results = validate_farmer_traceability("farmer-trace")
        assert len(results["experience_traces"]) == 1
        assert results["experience_traces"][0]["valid"] is True

    def test_has_indicator_traces(self, test_data_dir):
        _seed_traceable_data()
        results = validate_farmer_traceability("farmer-trace")
        assert len(results["indicator_traces"]) == 1

    def test_has_data_health_traces(self, test_data_dir):
        _seed_traceable_data()
        results = validate_farmer_traceability("farmer-trace")
        assert len(results["data_health_traces"]) == 1

    def test_empty_farmer_is_valid(self, test_data_dir):
        _seed_traceable_data()
        results = validate_farmer_traceability("farmer-no-data")
        assert results["all_valid"] is True  # No data = nothing broken
