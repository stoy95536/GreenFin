"""
GATE-02 Tests: Domain Model Validation

Verifies:
- All models can be instantiated with valid data
- Field validation works (required fields, constraints)
- Enums are enforced
- EntityBase generates ID and timestamps
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.models import (
    User, UserRole, FarmerProfile, BankInstitution,
    Farm, Crop,
    Document, DocumentField, StandardizedRecord,
    DataDomain, DocumentStatus, SourceLevel,
    VerificationResult, Anomaly, AnomalyType, AnomalySeverity,
    GreenAction, GreenDimension, ActionLevel, ExperienceTransaction,
    IndicatorResult, DataHealthResult, DataHealthStatus,
    RuleSet, Authorization, AuthorizationStatus, BankCase,
    AuditLog, AuditEventType,
)


class TestEntityBase:
    """Test base entity behavior."""

    def test_auto_generates_id(self):
        user = User(username="x", display_name="X", role=UserRole.FARMER)
        assert user.id is not None
        assert len(user.id) > 0

    def test_auto_generates_created_at(self):
        user = User(username="x", display_name="X", role=UserRole.FARMER)
        assert user.created_at is not None

    def test_touch_updates_updated_at(self):
        user = User(username="x", display_name="X", role=UserRole.FARMER)
        assert user.updated_at is None
        user.touch()
        assert user.updated_at is not None

    def test_explicit_id_is_preserved(self):
        user = User(id="my-id", username="x", display_name="X", role=UserRole.FARMER)
        assert user.id == "my-id"


class TestUserModels:
    """Test User, FarmerProfile, BankInstitution."""

    def test_user_requires_username(self):
        with pytest.raises(Exception):
            User(display_name="X", role=UserRole.FARMER)

    def test_user_role_enum(self):
        user = User(username="a", display_name="A", role=UserRole.BANK)
        assert user.role == UserRole.BANK

    def test_farmer_profile(self):
        fp = FarmerProfile(user_id="u1", real_name="陳小農")
        assert fp.real_name == "陳小農"
        assert fp.farm_ids == []

    def test_bank_institution(self):
        bank = BankInstitution(code="812", name="台新銀行")
        assert bank.code == "812"


class TestFarmModels:
    """Test Farm, Crop."""

    def test_farm_creation(self):
        farm = Farm(farmer_id="f1", name="綠田農場")
        assert farm.name == "綠田農場"
        assert farm.crop_ids == []

    def test_crop_creation(self):
        crop = Crop(farm_id="farm1", name="稻米", variety="台南11號")
        assert crop.variety == "台南11號"


class TestDocumentModels:
    """Test Document, DocumentField, StandardizedRecord."""

    def test_document_defaults(self):
        doc = Document(farmer_id="f1", filename="test.pdf", domain=DataDomain.IDENTITY)
        assert doc.status == DocumentStatus.UPLOADED
        assert doc.source_level == SourceLevel.V1

    def test_document_field_confidence_range(self):
        field = DocumentField(document_id="d1", field_name="amount", confidence=0.95)
        assert field.confidence == 0.95

    def test_document_field_invalid_confidence(self):
        with pytest.raises(Exception):
            DocumentField(document_id="d1", field_name="x", confidence=1.5)

    def test_standardized_record(self):
        rec = StandardizedRecord(
            document_id="d1", farmer_id="f1",
            domain=DataDomain.TRANSACTION, record_type="sales",
            data={"amount": 50000},
        )
        assert rec.data["amount"] == 50000


class TestVerificationModels:
    """Test VerificationResult, Anomaly."""

    def test_verification_result(self):
        vr = VerificationResult(
            record_id="r1", source_level=SourceLevel.V3,
            reason="Official verification passed",
        )
        assert vr.source_level == SourceLevel.V3

    def test_anomaly_types(self):
        a = Anomaly(
            record_id="r1", anomaly_type=AnomalyType.EXPIRED,
            severity=AnomalySeverity.CRITICAL, description="Expired doc",
        )
        assert a.anomaly_type == AnomalyType.EXPIRED
        assert a.is_resolved is False


class TestGreenActionModels:
    """Test GreenAction, ExperienceTransaction."""

    def test_green_action(self):
        ga = GreenAction(
            farmer_id="f1", dimension=GreenDimension.REDUCTION,
            action_level=ActionLevel.CERTIFIED,
            description="有機認證", action_date="2026-01-01",
        )
        assert ga.dimension == GreenDimension.REDUCTION

    def test_experience_transaction(self):
        et = ExperienceTransaction(
            farmer_id="f1", green_action_id="ga1",
            dimension=GreenDimension.CIRCULAR,
            base_value=50, source_recognition_ratio=1.0,
            effective_value=50.0, rule_version="GREENFIN_DEMO_V1",
            calculated_at="2026-08-17T10:00:00+08:00",
        )
        assert et.effective_value == 50.0

    def test_experience_ratio_bounds(self):
        with pytest.raises(Exception):
            ExperienceTransaction(
                farmer_id="f1", green_action_id="ga1",
                dimension=GreenDimension.CIRCULAR,
                base_value=50, source_recognition_ratio=1.5,  # > 1.0
                effective_value=75.0, rule_version="V1",
                calculated_at="2026-08-17T10:00:00+08:00",
            )


class TestIndicatorModels:
    """Test IndicatorResult, DataHealthResult."""

    def test_indicator_result(self):
        ir = IndicatorResult(
            farmer_id="f1", indicator_type="completeness",
            score=85.0, level="L4",
            rule_version="GREENFIN_DEMO_V1",
            calculated_at="2026-08-17T10:00:00+08:00",
        )
        assert ir.score == 85.0

    def test_indicator_score_bounds(self):
        with pytest.raises(Exception):
            IndicatorResult(
                farmer_id="f1", indicator_type="completeness",
                score=150.0, level="L5",  # > 100
                rule_version="V1", calculated_at="now",
            )

    def test_data_health_result(self):
        dh = DataHealthResult(
            farmer_id="f1", domain=DataDomain.IDENTITY,
            status=DataHealthStatus.GREEN,
            reasons=["Data complete"], actions=[],
            rule_version="GREENFIN_DEMO_V1",
            calculated_at="2026-08-17T10:00:00+08:00",
        )
        assert dh.status == DataHealthStatus.GREEN

    def test_data_health_requires_reasons_list(self):
        dh = DataHealthResult(
            farmer_id="f1", domain=DataDomain.TRANSACTION,
            status=DataHealthStatus.RED,
            rule_version="V1", calculated_at="now",
        )
        assert dh.reasons == []  # defaults to empty list


class TestAuthorizationModels:
    """Test RuleSet, Authorization, BankCase."""

    def test_rule_set(self):
        rs = RuleSet(version="GREENFIN_DEMO_V1", name="Demo V1", config={"x": 1})
        assert rs.is_active is True

    def test_authorization(self):
        auth = Authorization(
            farmer_id="f1", institution_id="b1",
            purpose="Loan", data_scope=["IDENTITY"],
            start_at="2026-01-01", expire_at="2026-12-31",
        )
        assert auth.status == AuthorizationStatus.ACTIVE

    def test_bank_case(self):
        bc = BankCase(
            authorization_id="a1", institution_id="b1",
            farmer_id="f1", case_number="CASE-001",
        )
        assert bc.status == "open"


class TestAuditLog:
    """Test AuditLog."""

    def test_audit_log(self):
        al = AuditLog(
            event_type=AuditEventType.DOCUMENT_UPLOADED,
            actor_id="u1", target_id="d1", target_type="Document",
        )
        assert al.event_type == AuditEventType.DOCUMENT_UPLOADED
