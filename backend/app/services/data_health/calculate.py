"""
Data Health Calculation Service.

Per RULES.md §5 and AGENTS.md §12:

Status:
- GREEN: 目前可供參考
- YELLOW: 可參考但需補強
- RED: 目前不宜使用
- GRAY: 未提供、未核驗、不適用或未授權

Priority order:
1. 不適用／未授權 → GRAY
2. 重大異常／核心缺件 → RED
3. 一般缺漏／即將到期／待確認 → YELLOW
4. 符合條件 → GREEN

Each result must include: status, reasons[], actions[], affected_evidence_ids, rule_version

RED does NOT mean loan rejected. GRAY does NOT mean poor performance.
"""

from datetime import date, datetime, timedelta

from backend.app.models import (
    AnomalySeverity,
    DataDomain,
    DataHealthResult,
    DataHealthStatus,
    SourceLevel,
)
from backend.app.models.base import now_taipei
from backend.app.repositories import (
    get_anomaly_repo,
    get_data_health_repo,
    get_document_repo,
    get_standardized_record_repo,
    get_verification_repo,
)
from backend.app.rules import get_active_engine


# Domains to assess
ALL_DOMAINS = [
    DataDomain.IDENTITY,
    DataDomain.LAND_CROP,
    DataDomain.TRANSACTION,
    DataDomain.INPUT_EQUIPMENT,
    DataDomain.GREEN_ACTION,
    DataDomain.CERTIFICATION,
    DataDomain.LOAN_PURPOSE,
]


def calculate_domain_health(farmer_id: str, domain: DataDomain) -> DataHealthResult:
    """
    Calculate data health for a single domain.

    Applies priority logic:
    1. No data at all → GRAY
    2. Critical anomalies or core fields missing → RED
    3. Minor issues, expiring soon, partial data → YELLOW
    4. All good → GREEN
    """
    engine = get_active_engine()
    dh_rules = engine.get_data_health_rules()

    rec_repo = get_standardized_record_repo()
    anomaly_repo = get_anomaly_repo()
    doc_repo = get_document_repo()

    records = rec_repo.find_by(farmer_id=farmer_id, domain=domain.value)
    documents = doc_repo.find_by(farmer_id=farmer_id, domain=domain.value)

    reasons: list[str] = []
    actions: list[str] = []
    affected_ids: list[str] = []

    # ─── Priority 1: GRAY — no data ──────────────────────────────────────────
    if not records and not documents:
        return DataHealthResult(
            farmer_id=farmer_id,
            domain=domain,
            status=DataHealthStatus.GRAY,
            reasons=["此領域尚未提供任何資料"],
            actions=[f"建議上傳{_domain_label(domain)}相關文件"],
            affected_evidence_ids=[],
            rule_version=engine.version,
            calculated_at=now_taipei(),
        )

    # Collect affected evidence
    affected_ids = [r.id for r in records]

    # ─── Priority 2: RED — critical issues ───────────────────────────────────
    # Check for critical anomalies
    all_anomalies = anomaly_repo.get_all()
    record_ids = {r.id for r in records}
    domain_anomalies = [
        a for a in all_anomalies
        if a.record_id in record_ids and not a.is_resolved
    ]
    critical_anomalies = [
        a for a in domain_anomalies
        if a.severity == AnomalySeverity.CRITICAL
    ]

    # Check for V0 records (unusable)
    v0_records = [r for r in records if r.source_level == SourceLevel.V0]

    # Check for invalid records
    invalid_records = [r for r in records if not r.is_valid]

    # Check required fields missing
    required_fields = dh_rules.domain_required_fields.get(domain.value, [])
    all_data_keys = set()
    for r in records:
        all_data_keys.update(r.data.keys())
    missing_required = [f for f in required_fields if f not in all_data_keys]

    if critical_anomalies or v0_records or invalid_records or missing_required:
        if critical_anomalies:
            reasons.append(f"存在 {len(critical_anomalies)} 個重大異常")
            actions.append("請檢視異常紀錄並進行人工覆核")
        if v0_records:
            reasons.append(f"{len(v0_records)} 筆紀錄來源無法核驗 (V0)")
            actions.append("建議重新提交有效佐證文件")
        if invalid_records:
            reasons.append(f"{len(invalid_records)} 筆紀錄已標記為無效")
            actions.append("請更新或移除無效紀錄")
        if missing_required:
            reasons.append(f"缺少必要欄位: {', '.join(missing_required)}")
            actions.append(f"請補充: {', '.join(missing_required)}")

        return DataHealthResult(
            farmer_id=farmer_id,
            domain=domain,
            status=DataHealthStatus.RED,
            reasons=reasons,
            actions=actions,
            affected_evidence_ids=affected_ids,
            rule_version=engine.version,
            calculated_at=now_taipei(),
        )

    # ─── Priority 3: YELLOW — minor issues ───────────────────────────────────
    warning_anomalies = [
        a for a in domain_anomalies
        if a.severity == AnomalySeverity.WARNING
    ]

    # Check for soon-to-expire data
    expiry_warning_days = dh_rules.expiry_warning_days
    expiring_soon = _check_expiring_soon(records, expiry_warning_days)

    # Check for V1 only (no V2/V3)
    source_levels = {r.source_level for r in records}
    only_v1 = source_levels == {SourceLevel.V1}

    if warning_anomalies or expiring_soon or only_v1:
        if warning_anomalies:
            reasons.append(f"存在 {len(warning_anomalies)} 個一般異常待確認")
            actions.append("建議檢視並解決異常")
        if expiring_soon:
            reasons.append(f"部分資料即將於 {expiry_warning_days} 天內到期")
            actions.append("建議更新即將到期的文件")
        if only_v1:
            reasons.append("所有資料僅為自行提交 (V1)，佐證強度有限")
            actions.append("建議取得第三方認證或官方核驗文件")

        return DataHealthResult(
            farmer_id=farmer_id,
            domain=domain,
            status=DataHealthStatus.YELLOW,
            reasons=reasons,
            actions=actions,
            affected_evidence_ids=affected_ids,
            rule_version=engine.version,
            calculated_at=now_taipei(),
        )

    # ─── Priority 4: GREEN — all good ────────────────────────────────────────
    reasons.append("資料完整且經核驗，目前可供參考")
    return DataHealthResult(
        farmer_id=farmer_id,
        domain=domain,
        status=DataHealthStatus.GREEN,
        reasons=reasons,
        actions=[],
        affected_evidence_ids=affected_ids,
        rule_version=engine.version,
        calculated_at=now_taipei(),
    )


def calculate_all_data_health(farmer_id: str) -> list[DataHealthResult]:
    """
    Calculate data health for all domains and persist results.

    Returns list of DataHealthResult for each domain.
    """
    dh_repo = get_data_health_repo()

    # Clear existing results
    existing = dh_repo.find_by(farmer_id=farmer_id)
    for e in existing:
        dh_repo.delete(e.id)

    results = []
    for domain in ALL_DOMAINS:
        result = calculate_domain_health(farmer_id, domain)
        dh_repo.create(result)
        results.append(result)

    return results


def get_farmer_data_health(farmer_id: str) -> list[DataHealthResult]:
    """Get stored data health results for a farmer."""
    dh_repo = get_data_health_repo()
    return dh_repo.find_by(farmer_id=farmer_id)


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _check_expiring_soon(records, warning_days: int) -> bool:
    """Check if any record has a date field expiring within warning_days."""
    threshold = date.today() + timedelta(days=warning_days)
    date_fields = ["有效期限", "expiry", "到期日"]

    for record in records:
        for field_name in date_fields:
            value = record.data.get(field_name)
            if value:
                d = _parse_date(value)
                if d and date.today() <= d <= threshold:
                    return True
    return False


def _parse_date(value: str) -> date | None:
    """Parse date string."""
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _domain_label(domain: DataDomain) -> str:
    """Get Chinese label for domain."""
    labels = {
        DataDomain.IDENTITY: "身分與資格",
        DataDomain.LAND_CROP: "土地與作物",
        DataDomain.TRANSACTION: "經營與交易",
        DataDomain.INPUT_EQUIPMENT: "投入與設備",
        DataDomain.GREEN_ACTION: "綠色行動",
        DataDomain.CERTIFICATION: "認證與治理",
        DataDomain.LOAN_PURPOSE: "申貸用途",
    }
    return labels.get(domain, domain.value)
