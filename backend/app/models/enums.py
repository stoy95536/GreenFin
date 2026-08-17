"""
GreenFin Domain Enums.

All enumerated types used across the domain model.
Per AGENTS.md and RULES.md specifications.
"""

from enum import Enum


class UserRole(str, Enum):
    """System user roles."""
    FARMER = "farmer"
    BANK = "bank"
    ADMIN = "admin"


class SourceLevel(str, Enum):
    """Source verification levels (V0-V3). See RULES.md §2."""
    V0 = "V0"  # 無法使用或確認異常
    V1 = "V1"  # 自行提交且部分佐證
    V2 = "V2"  # 可查核第三方文件
    V3 = "V3"  # 官方／合作系統直接核驗


class DataDomain(str, Enum):
    """Data domains per AGENTS.md §11."""
    IDENTITY = "IDENTITY"
    LAND_CROP = "LAND_CROP"
    TRANSACTION = "TRANSACTION"
    INPUT_EQUIPMENT = "INPUT_EQUIPMENT"
    GREEN_ACTION = "GREEN_ACTION"
    CERTIFICATION = "CERTIFICATION"
    LOAN_PURPOSE = "LOAN_PURPOSE"


class DataHealthStatus(str, Enum):
    """Data Health status colors. See RULES.md §5."""
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"
    GRAY = "GRAY"


class AnomalyType(str, Enum):
    """Required anomaly types per AGENTS.md §13."""
    DUPLICATE = "DUPLICATE"
    EXPIRED = "EXPIRED"
    FUTURE_DATE = "FUTURE_DATE"
    CONFLICT = "CONFLICT"
    INVALID_FORMAT = "INVALID_FORMAT"
    OCR_LOW_CONFIDENCE = "OCR_LOW_CONFIDENCE"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"


class AnomalySeverity(str, Enum):
    """Anomaly severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class GreenDimension(str, Enum):
    """Four green experience dimensions per RULES.md §3."""
    REDUCTION = "減量"
    SEQUESTRATION = "增匯"
    CIRCULAR = "循環"
    GOVERNANCE = "綠色治理"


class ActionLevel(str, Enum):
    """Green action levels determining base experience value."""
    BASIC = "BASIC"          # 單次基礎行為 = 20
    SUSTAINED = "SUSTAINED"  # 持續性措施 = 50
    CERTIFIED = "CERTIFIED"  # 正式驗證／重大投入 = 100


class ExperienceLevel(str, Enum):
    """Experience level labels per RULES.md §3."""
    L0 = "L0"  # 尚未建立 = 0
    L1 = "L1"  # 萌芽 = 1-200
    L2 = "L2"  # 成長 = 201-400
    L3 = "L3"  # 穩健 = 401-600
    L4 = "L4"  # 領航 = 601-800
    L5 = "L5"  # 示範 = 801-1000


class DocumentStatus(str, Enum):
    """Document processing status."""
    UPLOADED = "UPLOADED"
    OCR_COMPLETED = "OCR_COMPLETED"
    FIELDS_CONFIRMED = "FIELDS_CONFIRMED"
    NORMALIZED = "NORMALIZED"
    VERIFIED = "VERIFIED"


class AuthorizationStatus(str, Enum):
    """Authorization lifecycle status."""
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class AuditEventType(str, Enum):
    """Audit trail event types per AGENTS.md §32."""
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    OCR_COMPLETED = "OCR_COMPLETED"
    FIELD_CORRECTED = "FIELD_CORRECTED"
    VERIFICATION_UPDATED = "VERIFICATION_UPDATED"
    ANOMALY_DETECTED = "ANOMALY_DETECTED"
    EXPERIENCE_RECALCULATED = "EXPERIENCE_RECALCULATED"
    INDICATOR_RECALCULATED = "INDICATOR_RECALCULATED"
    DATA_HEALTH_UPDATED = "DATA_HEALTH_UPDATED"
    AUTHORIZATION_GRANTED = "AUTHORIZATION_GRANTED"
    AUTHORIZATION_REVOKED = "AUTHORIZATION_REVOKED"
    BANK_DATA_ACCESSED = "BANK_DATA_ACCESSED"
    REPORT_GENERATED = "REPORT_GENERATED"
