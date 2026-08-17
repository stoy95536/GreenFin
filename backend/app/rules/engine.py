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
    """
    Indicator calculation rules per RULES.md §4.

    Every number the four indicator calculations use must come from here, so that
    editing the rule set actually changes the results. Previously the calculators
    hardcoded their weights and thresholds while still stamping results with a
    rule_version, which made the provenance misleading.
    """

    # Tier weights and which tier each data domain belongs to (資料完整度)
    completeness_weights: dict[str, int]          # tier name → weight
    completeness_domain_tiers: dict[str, str]     # domain → tier name

    # 資料可信度 scoring
    credibility_factors: list[str]
    credibility_source_scores: dict[str, int]     # V0..V3 → 0..100
    credibility_anomaly_penalty_per: int
    credibility_anomaly_penalty_max: int
    credibility_traceability_bonus_max: int

    # 經營成熟度 scoring
    maturity_factors: list[str]
    maturity_variety_max: int
    maturity_volume_max: int
    maturity_volume_saturation_records: int
    maturity_document_max: int
    maturity_document_saturation_count: int
    maturity_transaction_bonus: int

    # 綠色成熟度 scoring
    green_maturity_factors: list[str]
    green_experience_max: int
    green_breadth_per_dimension: int
    green_quality_max: int

    # indicator → [[min,max], ...] ordered L1..L5
    level_thresholds: dict[str, list[list[int]]]

    def level_for(self, indicator_type: str, score: float) -> str:
        """
        Map a 0-100 score to an L1..L5 label using the configured bands.

        Falls back to the highest band whose lower bound the score reaches, so a
        config with gaps still yields a deterministic level.
        """
        bands = self.level_thresholds.get(indicator_type)
        if not bands:
            return "L1"

        level = "L1"
        for index, band in enumerate(bands, start=1):
            if not band:
                continue
            lower = band[0]
            if score >= lower:
                level = f"L{index}"
        return level


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
        """
        Get typed indicator calculation rules.

        Defaults mirror the GREENFIN_DEMO_V1 parameters so a partially-specified
        config still produces a complete, explicit rule object.
        """
        ind = self.config.get("indicators", {})
        completeness = ind.get("completeness", {})
        credibility = ind.get("credibility", {})
        maturity = ind.get("business_maturity", {})
        green = ind.get("green_maturity", {})

        default_bands = [[0, 19], [20, 39], [40, 59], [60, 79], [80, 100]]

        return IndicatorRules(
            # 資料完整度
            completeness_weights=ind.get("completeness_weights") or completeness.get(
                "tier_weights",
                {"core_required": 3, "important_supporting": 2, "supplementary": 1},
            ),
            completeness_domain_tiers=completeness.get("domain_tiers", {
                "IDENTITY": "core_required",
                "LAND_CROP": "core_required",
                "TRANSACTION": "important_supporting",
                "CERTIFICATION": "important_supporting",
                "GREEN_ACTION": "important_supporting",
                "INPUT_EQUIPMENT": "supplementary",
                "LOAN_PURPOSE": "supplementary",
            }),

            # 資料可信度
            credibility_factors=ind.get("credibility_factors", [
                "source_level", "expiry", "cross_consistency",
                "duplicates", "anomalies", "traceability",
            ]),
            credibility_source_scores=credibility.get(
                "source_level_scores", {"V0": 0, "V1": 33, "V2": 67, "V3": 100}
            ),
            credibility_anomaly_penalty_per=credibility.get("anomaly_penalty_per", 5),
            credibility_anomaly_penalty_max=credibility.get("anomaly_penalty_max", 30),
            credibility_traceability_bonus_max=credibility.get("traceability_bonus_max", 10),

            # 經營成熟度
            maturity_factors=ind.get("maturity_factors", [
                "record_period", "data_variety", "update_continuity",
                "missing_months", "cross_validation",
            ]),
            maturity_variety_max=maturity.get("variety_max", 40),
            maturity_volume_max=maturity.get("volume_max", 30),
            maturity_volume_saturation_records=maturity.get("volume_saturation_records", 20),
            maturity_document_max=maturity.get("document_max", 20),
            maturity_document_saturation_count=maturity.get("document_saturation_count", 10),
            maturity_transaction_bonus=maturity.get("transaction_bonus", 10),

            # 綠色成熟度
            green_maturity_factors=ind.get("green_maturity_factors", [
                "experience_value", "dimension_breadth", "duration",
                "v2_v3_ratio", "anomalies",
            ]),
            green_experience_max=green.get("experience_max", 40),
            green_breadth_per_dimension=green.get("breadth_per_dimension", 10),
            green_quality_max=green.get("quality_max", 20),

            level_thresholds=ind.get("level_thresholds", {
                "completeness": [[0, 39], [40, 59], [60, 79], [80, 94], [95, 100]],
                "credibility": default_bands,
                "business_maturity": default_bands,
                "green_maturity": default_bands,
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
