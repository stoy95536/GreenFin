"""
GreenFin Rule Engine.

Central module for:
- Loading rule configurations from the RuleSet repository
- Version selection (active vs historical)
- Providing typed access to experience, indicator, and data health rules
- Recording calculation traces

Per AGENTS.md §8:
- Current Demo Rule Set: GREENFIN_DEMO_V1
- Rule changes must not silently overwrite historical calculations
- Every calculation preserves: rule_version, calculated_at, input_evidence_ids, calculation_trace
"""

from dataclasses import dataclass, field
from typing import Optional

from backend.app.models import RuleSet
from backend.app.models.base import now_taipei
from backend.app.repositories import get_rule_set_repo


class RuleEngineError(Exception):
    """Raised when rule engine encounters a configuration problem."""
    pass


# ─── Typed Rule Configurations ────────────────────────────────────────────────


@dataclass
class ExperienceRules:
    """Experience calculation rules per RULES.md §3."""
    dimensions: list[str]
    annual_limit_per_dimension: int
    total_limit: int
    base_values: dict[str, int]  # ActionLevel → base value
    source_ratios: dict[str, float]  # SourceLevel → ratio
    levels: dict[str, list[int]]  # Level → [min, max]


@dataclass
class IndicatorRules:
    """Indicator calculation rules per RULES.md §4."""
    completeness_weights: dict[str, int]  # priority → weight
    credibility_factors: list[str]
    maturity_factors: list[str]
    green_maturity_factors: list[str]
    level_thresholds: dict[str, list[list[int]]]  # indicator → [[min,max],...]


@dataclass
class DataHealthRules:
    """Data Health rules per RULES.md §5."""
    priority_order: list[str]  # GRAY → RED → YELLOW → GREEN
    domain_required_fields: dict[str, list[str]]
    expiry_warning_days: int
    critical_anomaly_types: list[str]


@dataclass
class CalculationTrace:
    """Record of a single calculation for traceability."""
    rule_version: str
    calculated_at: str
    input_evidence_ids: list[str] = field(default_factory=list)
    calculation_trace: str = ""


# ─── Rule Engine ──────────────────────────────────────────────────────────────


class RuleEngine:
    """
    Central rule engine that loads and provides typed access to rules.

    Usage:
        engine = RuleEngine()
        exp_rules = engine.get_experience_rules()
        trace = engine.create_trace(evidence_ids=["doc-1"], trace="BASIC(20) × V2(1.0) = 20")
    """

    def __init__(self, version: Optional[str] = None):
        """
        Initialize rule engine.

        Args:
            version: Specific rule version to load. If None, loads active version.
        """
        self._rule_set: Optional[RuleSet] = None
        self._version = version
        self._load()

    def _load(self):
        """Load rule set from repository."""
        repo = get_rule_set_repo()

        if self._version:
            results = repo.find_by(version=self._version)
            if not results:
                raise RuleEngineError(f"Rule version '{self._version}' not found")
            self._rule_set = results[0]
        else:
            results = repo.find_by(is_active=True)
            if not results:
                raise RuleEngineError("No active rule set found")
            self._rule_set = results[0]

    @property
    def version(self) -> str:
        """Current rule version identifier."""
        return self._rule_set.version

    @property
    def rule_set(self) -> RuleSet:
        """The full RuleSet entity."""
        return self._rule_set

    @property
    def config(self) -> dict:
        """Raw config dict from the rule set."""
        return self._rule_set.config

    def get_experience_rules(self) -> ExperienceRules:
        """Get typed experience calculation rules."""
        exp = self.config.get("experience", {})
        return ExperienceRules(
            dimensions=exp.get("dimensions", ["減量", "增匯", "循環", "綠色治理"]),
            annual_limit_per_dimension=exp.get("annual_limit_per_dimension", 250),
            total_limit=exp.get("total_limit", 1000),
            base_values=exp.get("base_values", {"BASIC": 20, "SUSTAINED": 50, "CERTIFIED": 100}),
            source_ratios=exp.get("source_ratios", {"V3": 1.0, "V2": 1.0, "V1": 0.5, "V0": 0.0}),
            levels=exp.get("levels", {
                "L0": [0, 0], "L1": [1, 200], "L2": [201, 400],
                "L3": [401, 600], "L4": [601, 800], "L5": [801, 1000],
            }),
        )

    def get_indicator_rules(self) -> IndicatorRules:
        """Get typed indicator calculation rules."""
        ind = self.config.get("indicators", {})
        return IndicatorRules(
            completeness_weights=ind.get("completeness_weights", {
                "core_required": 3,
                "important_supporting": 2,
                "supplementary": 1,
            }),
            credibility_factors=ind.get("credibility_factors", [
                "source_level", "expiry", "cross_consistency",
                "duplicates", "anomalies", "traceability",
            ]),
            maturity_factors=ind.get("maturity_factors", [
                "record_period", "data_variety", "update_continuity",
                "missing_months", "cross_validation",
            ]),
            green_maturity_factors=ind.get("green_maturity_factors", [
                "experience_value", "dimension_breadth", "duration",
                "v2_v3_ratio", "anomalies",
            ]),
            level_thresholds=ind.get("level_thresholds", {
                "completeness": [[0, 39], [40, 59], [60, 79], [80, 94], [95, 100]],
                "credibility": [[0, 19], [20, 39], [40, 59], [60, 79], [80, 100]],
            }),
        )

    def get_data_health_rules(self) -> DataHealthRules:
        """Get typed data health rules."""
        dh = self.config.get("data_health", {})
        return DataHealthRules(
            priority_order=dh.get("priority_order", ["GRAY", "RED", "YELLOW", "GREEN"]),
            domain_required_fields=dh.get("domain_required_fields", {
                "IDENTITY": ["姓名"],
                "LAND_CROP": ["面積"],
                "TRANSACTION": ["交易金額", "交易日期"],
                "GREEN_ACTION": ["活動名稱"],
                "CERTIFICATION": ["認證機構", "有效期限"],
                "LOAN_PURPOSE": ["申貸用途"],
            }),
            expiry_warning_days=dh.get("expiry_warning_days", 90),
            critical_anomaly_types=dh.get("critical_anomaly_types", [
                "EXPIRED", "VERIFICATION_FAILED", "MISSING_REQUIRED_FIELD",
            ]),
        )

    def create_trace(
        self,
        evidence_ids: Optional[list[str]] = None,
        trace: str = "",
    ) -> CalculationTrace:
        """
        Create a calculation trace record.

        Per AGENTS.md §8: every calculation must preserve rule_version, calculated_at,
        input_evidence_ids, and calculation_trace.
        """
        return CalculationTrace(
            rule_version=self.version,
            calculated_at=now_taipei(),
            input_evidence_ids=evidence_ids or [],
            calculation_trace=trace,
        )

    def validate_config(self) -> list[str]:
        """
        Validate the current rule configuration.

        Returns list of validation errors (empty = valid).
        """
        errors = []

        # Check experience rules
        exp = self.config.get("experience")
        if not exp:
            errors.append("Missing 'experience' section in config")
        else:
            if not exp.get("base_values"):
                errors.append("Missing experience.base_values")
            if not exp.get("source_ratios"):
                errors.append("Missing experience.source_ratios")
            if exp.get("total_limit", 0) <= 0:
                errors.append("experience.total_limit must be > 0")
            bv = exp.get("base_values", {})
            for level in ("BASIC", "SUSTAINED", "CERTIFIED"):
                if level not in bv:
                    errors.append(f"Missing base_value for action level: {level}")
            sr = exp.get("source_ratios", {})
            for src in ("V0", "V1", "V2", "V3"):
                if src not in sr:
                    errors.append(f"Missing source_ratio for: {src}")

        return errors


# ─── Convenience ──────────────────────────────────────────────────────────────


def get_active_engine() -> RuleEngine:
    """Get the rule engine loaded with the currently active rule set."""
    return RuleEngine()


def get_engine_for_version(version: str) -> RuleEngine:
    """Get the rule engine for a specific rule version."""
    return RuleEngine(version=version)
