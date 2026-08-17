"""
GreenFin Demo Seed Data.

Creates 3 demo cases per AGENTS.md §18:
- Case A (陳小農): Healthy — V2/V3, complete, GREEN
- Case B (林阿花): Needs Improvement — V1, partial, YELLOW
- Case C (王大明): Abnormal — V0, duplicates/expired, RED

All data is clearly DEMO / SIMULATED per AGENTS.md §18.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

# Windows consoles default to a legacy codepage (e.g. cp950) when stdout is piped,
# which crashes on the checkmarks below. Force UTF-8 so the script is safe to pipe.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from backend.app.repositories import (
    get_data_dir,
    get_anomaly_repo,
    get_authorization_repo,
    get_audit_log_repo,
    get_bank_case_repo,
    get_bank_repo,
    get_crop_repo,
    get_data_health_repo,
    get_document_field_repo,
    get_document_repo,
    get_experience_repo,
    get_farm_repo,
    get_farmer_repo,
    get_green_action_repo,
    get_indicator_repo,
    get_rule_set_repo,
    get_standardized_record_repo,
    get_user_repo,
    get_verification_repo,
)
from backend.app.models import (
    ActionLevel,
    Anomaly,
    AnomalySeverity,
    AnomalyType,
    AuditEventType,
    AuditLog,
    Authorization,
    AuthorizationStatus,
    BankCase,
    BankInstitution,
    Crop,
    DataDomain,
    DataHealthResult,
    DataHealthStatus,
    Document,
    DocumentField,
    DocumentStatus,
    ExperienceTransaction,
    Farm,
    FarmerProfile,
    GreenAction,
    GreenDimension,
    IndicatorResult,
    RuleSet,
    SourceLevel,
    StandardizedRecord,
    User,
    UserRole,
    VerificationResult,
)

# ─── Fixed IDs for demo reproducibility ───────────────────────────────────────

# Users
USER_A_ID = "user-farmer-a"
USER_B_ID = "user-farmer-b"
USER_C_ID = "user-farmer-c"
USER_BANK_ID = "user-bank-001"

# Farmers
FARMER_A_ID = "farmer-a-chen"
FARMER_B_ID = "farmer-b-lin"
FARMER_C_ID = "farmer-c-wang"

# Farms
FARM_A_ID = "farm-a-green-field"
FARM_B_ID = "farm-b-sunrise"
FARM_C_ID = "farm-c-old-plot"

# Crops
CROP_A_ID = "crop-a-rice"
CROP_B_ID = "crop-b-vegetables"
CROP_C_ID = "crop-c-fruit"

# Documents
DOC_A1_ID = "doc-a1-cert"
DOC_A2_ID = "doc-a2-invoice"
DOC_B1_ID = "doc-b1-photo"
DOC_C1_ID = "doc-c1-expired"
DOC_C2_ID = "doc-c2-duplicate"

# Records
REC_A1_ID = "rec-a1-certification"
REC_A2_ID = "rec-a2-transaction"
REC_B1_ID = "rec-b1-activity"
REC_C1_ID = "rec-c1-expired-cert"
REC_C2_ID = "rec-c2-duplicate"

# Green Actions
GA_A1_ID = "ga-a1-organic"
GA_A2_ID = "ga-a2-solar"
GA_B1_ID = "ga-b1-compost"
GA_C1_ID = "ga-c1-claim"

# Bank
BANK_ID = "bank-taishin"

# Authorization
AUTH_A_ID = "auth-a-to-bank"

# Rule Set
RULESET_ID = "ruleset-demo-v1"


def seed_all():
    """Populate all JSON data files with demo seed data."""
    print("Seeding GreenFin demo data...")
    print(f"Data directory: {get_data_dir()}")

    # ─── Rule Set ─────────────────────────────────────────────────────────────
    rule_repo = get_rule_set_repo()
    rule_repo.clear()
    rule_repo.create(RuleSet(
        id=RULESET_ID,
        version="GREENFIN_DEMO_V1",
        name="Demo Rule Set V1",
        description="Initial demo rules for experience, indicators, and data health.",
        config={
            "experience": {
                "dimensions": ["減量", "增匯", "循環", "綠色治理"],
                "annual_limit_per_dimension": 250,
                "total_limit": 1000,
                "base_values": {"BASIC": 20, "SUSTAINED": 50, "CERTIFIED": 100},
                "source_ratios": {"V3": 1.0, "V2": 1.0, "V1": 0.5, "V0": 0.0},
                "levels": {
                    "L0": [0, 0], "L1": [1, 200], "L2": [201, 400],
                    "L3": [401, 600], "L4": [601, 800], "L5": [801, 1000],
                },
            },
            "indicators": {
                # 資料完整度: which tier each domain belongs to, and each tier's weight
                "completeness": {
                    "tier_weights": {
                        "core_required": 3,
                        "important_supporting": 2,
                        "supplementary": 1,
                    },
                    "domain_tiers": {
                        "IDENTITY": "core_required",
                        "LAND_CROP": "core_required",
                        "TRANSACTION": "important_supporting",
                        "CERTIFICATION": "important_supporting",
                        "GREEN_ACTION": "important_supporting",
                        "INPUT_EQUIPMENT": "supplementary",
                        "LOAN_PURPOSE": "supplementary",
                    },
                },
                # 資料可信度 scoring coefficients
                "credibility": {
                    "source_level_scores": {"V0": 0, "V1": 33, "V2": 67, "V3": 100},
                    "anomaly_penalty_per": 5,
                    "anomaly_penalty_max": 30,
                    "traceability_bonus_max": 10,
                },
                # 經營成熟度 scoring caps and saturation points
                "business_maturity": {
                    "variety_max": 40,
                    "volume_max": 30,
                    "volume_saturation_records": 20,
                    "document_max": 20,
                    "document_saturation_count": 10,
                    "transaction_bonus": 10,
                },
                # 綠色成熟度 scoring caps
                "green_maturity": {
                    "experience_max": 40,
                    "breadth_per_dimension": 10,
                    "quality_max": 20,
                },
                # Descriptive factor lists (documentation of what each indicator considers)
                "credibility_factors": [
                    "source_level", "expiry", "cross_consistency",
                    "duplicates", "anomalies", "traceability",
                ],
                "maturity_factors": [
                    "record_period", "data_variety", "update_continuity",
                    "missing_months", "cross_validation",
                ],
                "green_maturity_factors": [
                    "experience_value", "dimension_breadth", "duration",
                    "v2_v3_ratio", "anomalies",
                ],
                # L1..L5 bands per indicator
                "level_thresholds": {
                    "completeness": [[0, 39], [40, 59], [60, 79], [80, 94], [95, 100]],
                    "credibility": [[0, 19], [20, 39], [40, 59], [60, 79], [80, 100]],
                    "business_maturity": [[0, 19], [20, 39], [40, 59], [60, 79], [80, 100]],
                    "green_maturity": [[0, 19], [20, 39], [40, 59], [60, 79], [80, 100]],
                },
            },
            "data_health": {
                "priority_order": ["GRAY", "RED", "YELLOW", "GREEN"],
                "domain_required_fields": {
                    "IDENTITY": ["姓名"],
                    "LAND_CROP": ["面積"],
                    "TRANSACTION": ["交易金額", "交易日期"],
                    "GREEN_ACTION": ["活動名稱"],
                    "CERTIFICATION": ["認證機構", "有效期限"],
                    "LOAN_PURPOSE": ["申貸用途"],
                },
                "expiry_warning_days": 90,
                "critical_anomaly_types": [
                    "EXPIRED", "VERIFICATION_FAILED", "MISSING_REQUIRED_FIELD",
                ],
            },
        },
        is_active=True,
    ))
    print("  ✓ RuleSet")

    # ─── Users ────────────────────────────────────────────────────────────────
    user_repo = get_user_repo()
    user_repo.clear()
    user_repo.create(User(id=USER_A_ID, username="chen_farmer", display_name="陳小農", role=UserRole.FARMER))
    user_repo.create(User(id=USER_B_ID, username="lin_farmer", display_name="林阿花", role=UserRole.FARMER))
    user_repo.create(User(id=USER_C_ID, username="wang_farmer", display_name="王大明", role=UserRole.FARMER))
    user_repo.create(User(id=USER_BANK_ID, username="taishin_reviewer", display_name="台新銀行審查員", role=UserRole.BANK))
    user_repo.create(User(id="user-admin", username="admin", display_name="系統管理員", role=UserRole.ADMIN))
    print("  ✓ Users (5)")

    # ─── Farmers ──────────────────────────────────────────────────────────────
    farmer_repo = get_farmer_repo()
    farmer_repo.clear()
    farmer_repo.create(FarmerProfile(
        id=FARMER_A_ID, user_id=USER_A_ID, real_name="陳小農",
        phone="0912-345-678", address="台南市後壁區", farm_ids=[FARM_A_ID],
    ))
    farmer_repo.create(FarmerProfile(
        id=FARMER_B_ID, user_id=USER_B_ID, real_name="林阿花",
        phone="0923-456-789", address="嘉義縣民雄鄉", farm_ids=[FARM_B_ID],
    ))
    farmer_repo.create(FarmerProfile(
        id=FARMER_C_ID, user_id=USER_C_ID, real_name="王大明",
        phone="0934-567-890", address="雲林縣斗六市", farm_ids=[FARM_C_ID],
    ))
    print("  ✓ Farmers (3)")

    # ─── Banks ────────────────────────────────────────────────────────────────
    bank_repo = get_bank_repo()
    bank_repo.clear()
    bank_repo.create(BankInstitution(
        id=BANK_ID, code="812", name="台新國際商業銀行 (DEMO)",
        contact_email="demo@taishinbank.example",
    ))
    print("  ✓ Banks (1)")

    # ─── Farms ────────────────────────────────────────────────────────────────
    farm_repo = get_farm_repo()
    farm_repo.clear()
    farm_repo.create(Farm(
        id=FARM_A_ID, farmer_id=FARMER_A_ID, name="綠田友善農場",
        location="台南市後壁區新嘉里", area_hectares=2.5, crop_ids=[CROP_A_ID],
    ))
    farm_repo.create(Farm(
        id=FARM_B_ID, farmer_id=FARMER_B_ID, name="日出有機園",
        location="嘉義縣民雄鄉", area_hectares=1.2, crop_ids=[CROP_B_ID],
    ))
    farm_repo.create(Farm(
        id=FARM_C_ID, farmer_id=FARMER_C_ID, name="舊園地",
        location="雲林縣斗六市", area_hectares=0.8, crop_ids=[CROP_C_ID],
    ))
    print("  ✓ Farms (3)")

    # ─── Crops ────────────────────────────────────────────────────────────────
    crop_repo = get_crop_repo()
    crop_repo.clear()
    crop_repo.create(Crop(id=CROP_A_ID, farm_id=FARM_A_ID, name="稻米", variety="台南11號", planting_season="一期作"))
    crop_repo.create(Crop(id=CROP_B_ID, farm_id=FARM_B_ID, name="有機蔬菜", variety="小白菜", planting_season="全年"))
    crop_repo.create(Crop(id=CROP_C_ID, farm_id=FARM_C_ID, name="芒果", variety="愛文", planting_season="夏季"))
    print("  ✓ Crops (3)")

    # ─── Documents ────────────────────────────────────────────────────────────
    doc_repo = get_document_repo()
    doc_repo.clear()
    # Case A: Verified documents
    doc_repo.create(Document(
        id=DOC_A1_ID, farmer_id=FARMER_A_ID, filename="有機認證書_2026.pdf",
        domain=DataDomain.CERTIFICATION, source_level=SourceLevel.V3,
        status=DocumentStatus.VERIFIED, file_hash="abc123def456",
    ))
    doc_repo.create(Document(
        id=DOC_A2_ID, farmer_id=FARMER_A_ID, filename="農會出貨單_202601.pdf",
        domain=DataDomain.TRANSACTION, source_level=SourceLevel.V2,
        status=DocumentStatus.VERIFIED, file_hash="def789ghi012",
    ))
    # Case B: Self-submitted
    doc_repo.create(Document(
        id=DOC_B1_ID, farmer_id=FARMER_B_ID, filename="堆肥照片_20260315.jpg",
        domain=DataDomain.GREEN_ACTION, source_level=SourceLevel.V1,
        status=DocumentStatus.FIELDS_CONFIRMED, file_hash="jkl345mno678",
    ))
    # Case C: Problematic
    doc_repo.create(Document(
        id=DOC_C1_ID, farmer_id=FARMER_C_ID, filename="過期農藥證明_2023.pdf",
        domain=DataDomain.CERTIFICATION, source_level=SourceLevel.V0,
        status=DocumentStatus.UPLOADED, file_hash="pqr901stu234",
    ))
    doc_repo.create(Document(
        id=DOC_C2_ID, farmer_id=FARMER_C_ID, filename="過期農藥證明_2023_copy.pdf",
        domain=DataDomain.CERTIFICATION, source_level=SourceLevel.V0,
        status=DocumentStatus.UPLOADED, file_hash="pqr901stu234",  # Same hash = duplicate
    ))
    print("  ✓ Documents (5)")

    # ─── Document Fields ──────────────────────────────────────────────────────
    field_repo = get_document_field_repo()
    field_repo.clear()
    field_repo.create(DocumentField(
        id="field-a1-cert-org", document_id=DOC_A1_ID,
        field_name="認證機構", raw_value="慈心有機農業發展基金會",
        normalized_value="慈心有機農業發展基金會", confidence=0.98, source="ocr",
    ))
    field_repo.create(DocumentField(
        id="field-a1-cert-expiry", document_id=DOC_A1_ID,
        field_name="有效期限", raw_value="2027/06/30",
        normalized_value="2027-06-30", confidence=0.95, source="ocr",
    ))
    field_repo.create(DocumentField(
        id="field-a2-amount", document_id=DOC_A2_ID,
        field_name="出貨金額", raw_value="NT$125,000",
        normalized_value="125000", confidence=0.92, source="ocr",
    ))
    field_repo.create(DocumentField(
        id="field-b1-desc", document_id=DOC_B1_ID,
        field_name="活動描述", raw_value="自製堆肥施用",
        normalized_value="自製堆肥施用", confidence=0.6, source="ocr", manually_corrected=True,
    ))
    field_repo.create(DocumentField(
        id="field-c1-expiry", document_id=DOC_C1_ID,
        field_name="有效期限", raw_value="2023/12/31",
        normalized_value="2023-12-31", confidence=0.85, source="ocr",
    ))
    print("  ✓ Document Fields (5)")

    # ─── Standardized Records ─────────────────────────────────────────────────
    rec_repo = get_standardized_record_repo()
    rec_repo.clear()
    rec_repo.create(StandardizedRecord(
        id=REC_A1_ID, document_id=DOC_A1_ID, farmer_id=FARMER_A_ID,
        domain=DataDomain.CERTIFICATION, record_type="organic_certification",
        source_level=SourceLevel.V3, is_valid=True,
        data={"issuer": "慈心有機農業發展基金會", "expiry": "2027-06-30", "scope": "有機稻米"},
    ))
    rec_repo.create(StandardizedRecord(
        id=REC_A2_ID, document_id=DOC_A2_ID, farmer_id=FARMER_A_ID,
        domain=DataDomain.TRANSACTION, record_type="sales_record",
        source_level=SourceLevel.V2, is_valid=True,
        data={"buyer": "後壁區農會", "amount": 125000, "date": "2026-01-15", "product": "稻米"},
    ))
    rec_repo.create(StandardizedRecord(
        id=REC_B1_ID, document_id=DOC_B1_ID, farmer_id=FARMER_B_ID,
        domain=DataDomain.GREEN_ACTION, record_type="green_activity",
        source_level=SourceLevel.V1, is_valid=True,
        data={"activity": "自製堆肥施用", "date": "2026-03-15", "area": "0.5公頃"},
    ))
    rec_repo.create(StandardizedRecord(
        id=REC_C1_ID, document_id=DOC_C1_ID, farmer_id=FARMER_C_ID,
        domain=DataDomain.CERTIFICATION, record_type="pesticide_cert",
        source_level=SourceLevel.V0, is_valid=False,
        data={"issuer": "不明機構", "expiry": "2023-12-31", "note": "已過期"},
    ))
    rec_repo.create(StandardizedRecord(
        id=REC_C2_ID, document_id=DOC_C2_ID, farmer_id=FARMER_C_ID,
        domain=DataDomain.CERTIFICATION, record_type="pesticide_cert",
        source_level=SourceLevel.V0, is_valid=False,
        data={"issuer": "不明機構", "expiry": "2023-12-31", "note": "重複文件"},
    ))
    print("  ✓ Standardized Records (5)")

    # ─── Verification Results ─────────────────────────────────────────────────
    ver_repo = get_verification_repo()
    ver_repo.clear()
    ver_repo.create(VerificationResult(
        id="ver-a1", record_id=REC_A1_ID, source_level=SourceLevel.V3,
        reason="有機認證書經系統查核為有效 (DEMO SIMULATED)", evidence_ids=[DOC_A1_ID],
    ))
    ver_repo.create(VerificationResult(
        id="ver-a2", record_id=REC_A2_ID, source_level=SourceLevel.V2,
        reason="農會出貨單為可查核第三方文件 (DEMO SIMULATED)", evidence_ids=[DOC_A2_ID],
    ))
    ver_repo.create(VerificationResult(
        id="ver-b1", record_id=REC_B1_ID, source_level=SourceLevel.V1,
        reason="照片為自行提交，僅部分佐證 (DEMO SIMULATED)", evidence_ids=[DOC_B1_ID],
    ))
    ver_repo.create(VerificationResult(
        id="ver-c1", record_id=REC_C1_ID, source_level=SourceLevel.V0,
        reason="文件已過期且來源無法確認 (DEMO SIMULATED)", evidence_ids=[DOC_C1_ID],
    ))
    print("  ✓ Verification Results (4)")

    # ─── Anomalies ────────────────────────────────────────────────────────────
    anomaly_repo = get_anomaly_repo()
    anomaly_repo.clear()
    anomaly_repo.create(Anomaly(
        id="anom-c1-expired", record_id=REC_C1_ID, document_id=DOC_C1_ID,
        anomaly_type=AnomalyType.EXPIRED, severity=AnomalySeverity.CRITICAL,
        description="農藥使用證明已於 2023-12-31 過期 (DEMO)",
    ))
    anomaly_repo.create(Anomaly(
        id="anom-c2-duplicate", record_id=REC_C2_ID, document_id=DOC_C2_ID,
        anomaly_type=AnomalyType.DUPLICATE, severity=AnomalySeverity.WARNING,
        description="與 doc-c1-expired 檔案 hash 相同，疑似重複上傳 (DEMO)",
    ))
    anomaly_repo.create(Anomaly(
        id="anom-c1-verfail", record_id=REC_C1_ID, document_id=DOC_C1_ID,
        anomaly_type=AnomalyType.VERIFICATION_FAILED, severity=AnomalySeverity.CRITICAL,
        description="來源核驗失敗，無法確認文件真實性 (DEMO)",
    ))
    print("  ✓ Anomalies (3)")

    # ─── Green Actions ────────────────────────────────────────────────────────
    ga_repo = get_green_action_repo()
    ga_repo.clear()
    ga_repo.create(GreenAction(
        id=GA_A1_ID, farmer_id=FARMER_A_ID, dimension=GreenDimension.REDUCTION,
        action_level=ActionLevel.CERTIFIED, description="取得有機認證，減少化學農藥使用",
        action_date="2026-01-10", evidence_record_ids=[REC_A1_ID],
    ))
    ga_repo.create(GreenAction(
        id=GA_A2_ID, farmer_id=FARMER_A_ID, dimension=GreenDimension.REDUCTION,
        action_level=ActionLevel.SUSTAINED, description="安裝太陽能抽水設備，持續使用中",
        action_date="2025-08-01", evidence_record_ids=[],
    ))
    ga_repo.create(GreenAction(
        id=GA_B1_ID, farmer_id=FARMER_B_ID, dimension=GreenDimension.CIRCULAR,
        action_level=ActionLevel.BASIC, description="自製堆肥施用於田間",
        action_date="2026-03-15", evidence_record_ids=[REC_B1_ID],
    ))
    ga_repo.create(GreenAction(
        id=GA_C1_ID, farmer_id=FARMER_C_ID, dimension=GreenDimension.GOVERNANCE,
        action_level=ActionLevel.BASIC, description="自稱參加農業課程（無佐證）",
        action_date="2026-02-01", evidence_record_ids=[REC_C1_ID], is_active=False,
    ))
    print("  ✓ Green Actions (4)")

    # ─── Experience Transactions ──────────────────────────────────────────────
    exp_repo = get_experience_repo()
    exp_repo.clear()
    exp_repo.create(ExperienceTransaction(
        id="exp-a1", farmer_id=FARMER_A_ID, green_action_id=GA_A1_ID,
        dimension=GreenDimension.REDUCTION, base_value=100,
        source_recognition_ratio=1.0, effective_value=100.0,
        rule_version="GREENFIN_DEMO_V1", calculated_at="2026-08-17T10:00:00+08:00",
        input_evidence_ids=[DOC_A1_ID, REC_A1_ID],
        calculation_trace="CERTIFIED(100) × V3(1.0) = 100",
    ))
    exp_repo.create(ExperienceTransaction(
        id="exp-a2", farmer_id=FARMER_A_ID, green_action_id=GA_A2_ID,
        dimension=GreenDimension.REDUCTION, base_value=50,
        source_recognition_ratio=1.0, effective_value=50.0,
        rule_version="GREENFIN_DEMO_V1", calculated_at="2026-08-17T10:00:00+08:00",
        input_evidence_ids=[],
        calculation_trace="SUSTAINED(50) × V2(1.0) = 50 (ASSUMPTION: 設備佐證為V2)",
    ))
    exp_repo.create(ExperienceTransaction(
        id="exp-b1", farmer_id=FARMER_B_ID, green_action_id=GA_B1_ID,
        dimension=GreenDimension.CIRCULAR, base_value=20,
        source_recognition_ratio=0.5, effective_value=10.0,
        rule_version="GREENFIN_DEMO_V1", calculated_at="2026-08-17T10:00:00+08:00",
        input_evidence_ids=[DOC_B1_ID, REC_B1_ID],
        calculation_trace="BASIC(20) × V1(0.5) = 10",
    ))
    exp_repo.create(ExperienceTransaction(
        id="exp-c1", farmer_id=FARMER_C_ID, green_action_id=GA_C1_ID,
        dimension=GreenDimension.GOVERNANCE, base_value=20,
        source_recognition_ratio=0.0, effective_value=0.0,
        rule_version="GREENFIN_DEMO_V1", calculated_at="2026-08-17T10:00:00+08:00",
        input_evidence_ids=[DOC_C1_ID, REC_C1_ID],
        calculation_trace="BASIC(20) × V0(0.0) = 0 (來源不可使用，不認列)",
    ))
    print("  ✓ Experience Transactions (4)")

    # ─── Indicator Results ────────────────────────────────────────────────────
    ind_repo = get_indicator_repo()
    ind_repo.clear()
    # Case A: High scores
    for indicator, score, level in [
        ("completeness", 88.0, "L4"), ("credibility", 82.0, "L5"),
        ("business_maturity", 70.0, "L3"), ("green_maturity", 75.0, "L4"),
    ]:
        ind_repo.create(IndicatorResult(
            id=f"ind-a-{indicator}", farmer_id=FARMER_A_ID,
            indicator_type=indicator, score=score, level=level,
            rule_version="GREENFIN_DEMO_V1", calculated_at="2026-08-17T10:00:00+08:00",
            input_evidence_ids=[REC_A1_ID, REC_A2_ID],
            calculation_trace=f"DEMO simulated {indicator} for Case A (Healthy)",
        ))
    # Case B: Medium scores
    for indicator, score, level in [
        ("completeness", 52.0, "L2"), ("credibility", 35.0, "L2"),
        ("business_maturity", 40.0, "L2"), ("green_maturity", 25.0, "L2"),
    ]:
        ind_repo.create(IndicatorResult(
            id=f"ind-b-{indicator}", farmer_id=FARMER_B_ID,
            indicator_type=indicator, score=score, level=level,
            rule_version="GREENFIN_DEMO_V1", calculated_at="2026-08-17T10:00:00+08:00",
            input_evidence_ids=[REC_B1_ID],
            calculation_trace=f"DEMO simulated {indicator} for Case B (Needs Improvement)",
        ))
    # Case C: Low scores
    for indicator, score, level in [
        ("completeness", 15.0, "L1"), ("credibility", 5.0, "L1"),
        ("business_maturity", 10.0, "L1"), ("green_maturity", 0.0, "L1"),
    ]:
        ind_repo.create(IndicatorResult(
            id=f"ind-c-{indicator}", farmer_id=FARMER_C_ID,
            indicator_type=indicator, score=score, level=level,
            rule_version="GREENFIN_DEMO_V1", calculated_at="2026-08-17T10:00:00+08:00",
            input_evidence_ids=[REC_C1_ID, REC_C2_ID],
            calculation_trace=f"DEMO simulated {indicator} for Case C (Abnormal)",
        ))
    print("  ✓ Indicator Results (12)")

    # ─── Data Health Results ──────────────────────────────────────────────────
    dh_repo = get_data_health_repo()
    dh_repo.clear()
    # Case A: Mostly GREEN
    for domain, status, reasons, actions in [
        (DataDomain.IDENTITY, DataHealthStatus.GREEN, ["身分資料完整且已核驗"], []),
        (DataDomain.LAND_CROP, DataHealthStatus.GREEN, ["土地與作物資料完整"], []),
        (DataDomain.TRANSACTION, DataHealthStatus.GREEN, ["交易紀錄由農會提供 (V2)"], []),
        (DataDomain.GREEN_ACTION, DataHealthStatus.GREEN, ["有機認證有效 (V3)"], []),
        (DataDomain.CERTIFICATION, DataHealthStatus.GREEN, ["認證在效期內"], []),
        (DataDomain.LOAN_PURPOSE, DataHealthStatus.GRAY, ["尚未申貸"], []),
    ]:
        dh_repo.create(DataHealthResult(
            id=f"dh-a-{domain.value.lower()}", farmer_id=FARMER_A_ID,
            domain=domain, status=status, reasons=reasons, actions=actions,
            rule_version="GREENFIN_DEMO_V1", calculated_at="2026-08-17T10:00:00+08:00",
        ))
    # Case B: Mix of YELLOW
    for domain, status, reasons, actions in [
        (DataDomain.IDENTITY, DataHealthStatus.GREEN, ["身分資料基本完整"], []),
        (DataDomain.LAND_CROP, DataHealthStatus.YELLOW, ["土地面積待補地籍證明"], ["建議補上地籍謄本"]),
        (DataDomain.TRANSACTION, DataHealthStatus.YELLOW, ["僅有部分交易紀錄"], ["建議補充近6個月出貨資料"]),
        (DataDomain.GREEN_ACTION, DataHealthStatus.YELLOW, ["照片佐證強度不足 (V1)"], ["建議取得第三方認證"]),
        (DataDomain.CERTIFICATION, DataHealthStatus.GRAY, ["未提供認證文件"], ["可申請產銷履歷認證"]),
        (DataDomain.LOAN_PURPOSE, DataHealthStatus.GRAY, ["尚未申貸"], []),
    ]:
        dh_repo.create(DataHealthResult(
            id=f"dh-b-{domain.value.lower()}", farmer_id=FARMER_B_ID,
            domain=domain, status=status, reasons=reasons, actions=actions,
            rule_version="GREENFIN_DEMO_V1", calculated_at="2026-08-17T10:00:00+08:00",
        ))
    # Case C: RED dominant
    for domain, status, reasons, actions in [
        (DataDomain.IDENTITY, DataHealthStatus.YELLOW, ["部分身分資料待確認"], ["補充身分證正反面"]),
        (DataDomain.LAND_CROP, DataHealthStatus.RED, ["土地資料缺失，無法確認經營範圍"], ["需補土地相關證明"]),
        (DataDomain.TRANSACTION, DataHealthStatus.RED, ["無有效交易紀錄"], ["需補充任何出貨或銷售證明"]),
        (DataDomain.GREEN_ACTION, DataHealthStatus.RED, ["綠色行動來源無法核驗 (V0)"], ["需重新提交有效佐證"]),
        (DataDomain.CERTIFICATION, DataHealthStatus.RED, ["認證已過期且重複上傳"], ["需取得有效認證或移除過期文件"]),
        (DataDomain.LOAN_PURPOSE, DataHealthStatus.GRAY, ["尚未申貸"], []),
    ]:
        dh_repo.create(DataHealthResult(
            id=f"dh-c-{domain.value.lower()}", farmer_id=FARMER_C_ID,
            domain=domain, status=status, reasons=reasons, actions=actions,
            rule_version="GREENFIN_DEMO_V1", calculated_at="2026-08-17T10:00:00+08:00",
        ))
    print("  ✓ Data Health Results (18)")

    # ─── Authorization ────────────────────────────────────────────────────────
    auth_repo = get_authorization_repo()
    auth_repo.clear()
    auth_repo.create(Authorization(
        id=AUTH_A_ID, farmer_id=FARMER_A_ID, institution_id=BANK_ID,
        purpose="農業設備貸款申請之授信補充資料",
        data_scope=["IDENTITY", "LAND_CROP", "TRANSACTION", "GREEN_ACTION", "CERTIFICATION"],
        start_at="2026-08-01T00:00:00+08:00", expire_at="2026-11-01T00:00:00+08:00",
        status=AuthorizationStatus.ACTIVE,
    ))
    print("  ✓ Authorizations (1)")

    # ─── Bank Cases ───────────────────────────────────────────────────────────
    case_repo = get_bank_case_repo()
    case_repo.clear()
    case_repo.create(BankCase(
        id="case-a-taishin", authorization_id=AUTH_A_ID,
        institution_id=BANK_ID, farmer_id=FARMER_A_ID,
        case_number="DEMO-2026-001", status="reviewing",
    ))
    print("  ✓ Bank Cases (1)")

    # ─── Audit Logs ───────────────────────────────────────────────────────────
    audit_repo = get_audit_log_repo()
    audit_repo.clear()
    # Just a couple of sample entries
    audit_repo.create(AuditLog(
        id="audit-001", event_type=AuditEventType.AUTHORIZATION_GRANTED,
        actor_id=USER_A_ID, target_id=AUTH_A_ID, target_type="Authorization",
        details={"institution": "台新銀行", "purpose": "農業設備貸款"},
    ))
    audit_repo.create(AuditLog(
        id="audit-002", event_type=AuditEventType.BANK_DATA_ACCESSED,
        actor_id=USER_BANK_ID, target_id=FARMER_A_ID, target_type="FarmerProfile",
        details={"case": "DEMO-2026-001", "action": "查看四大指標"},
    ))
    print("  ✓ Audit Logs (2)")

    print(f"\n✓ Seed complete. Data files in: {get_data_dir()}")
    print("  Case A (陳小農): Healthy — GREEN")
    print("  Case B (林阿花): Needs Improvement — YELLOW")
    print("  Case C (王大明): Abnormal — RED")


if __name__ == "__main__":
    seed_all()
