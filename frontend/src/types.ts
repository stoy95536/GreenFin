/**
 * Backend contract types.
 *
 * These mirror the Pydantic models / API responses. They replaced the previous
 * `Promise<any>` client, which meant no part of the UI enforced the backend contract
 * and a renamed field would fail silently at runtime.
 *
 * If the backend contract changes, update here — TypeScript will then point at every
 * affected component.
 */

// ─── Enums (mirror backend/app/models/enums.py) ──────────────────────────────

export type SourceLevel = "V0" | "V1" | "V2" | "V3";

export type DataDomainKey =
  | "IDENTITY"
  | "LAND_CROP"
  | "TRANSACTION"
  | "INPUT_EQUIPMENT"
  | "GREEN_ACTION"
  | "CERTIFICATION"
  | "LOAN_PURPOSE";

export type DataHealthStatus = "GREEN" | "YELLOW" | "RED" | "GRAY";

export type DocumentStatus =
  | "UPLOADED"
  | "OCR_COMPLETED"
  | "FIELDS_CONFIRMED"
  | "NORMALIZED"
  | "VERIFIED";

export type AnomalySeverity = "INFO" | "WARNING" | "CRITICAL";

export type IndicatorType =
  | "completeness"
  | "credibility"
  | "business_maturity"
  | "green_maturity";

export type ExperienceLevel = "L0" | "L1" | "L2" | "L3" | "L4" | "L5";

// ─── Health ──────────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: string;
  app_name: string;
  environment: string;
  demo_mode: boolean;
  rule_version: string;
  database: string;
  data_files: number;
  farmers_count: number;
  timestamp: string;
}

// ─── Documents ───────────────────────────────────────────────────────────────

export interface DocumentEntity {
  id: string;
  farmer_id: string;
  filename: string;
  file_hash: string | null;
  file_path: string | null;
  mime_type: string | null;
  domain: DataDomainKey;
  source_level: SourceLevel;
  status: DocumentStatus;
  upload_note: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface DocumentFieldEntity {
  id: string;
  document_id: string;
  field_name: string;
  raw_value: string | null;
  normalized_value: string | null;
  confidence: number | null;
  source: string;
  manually_corrected: boolean;
}

export interface UploadResponse {
  document: DocumentEntity;
  fields: DocumentFieldEntity[];
  message: string;
}

export interface DocumentFieldsResponse {
  document_id: string;
  fields: DocumentFieldEntity[];
}

export interface FarmerDocumentsResponse {
  farmer_id: string;
  count: number;
  documents: DocumentEntity[];
}

export interface ConfirmResponse {
  document_id: string;
  status: string;
  fields: DocumentFieldEntity[];
  message: string;
}

// ─── Experience ──────────────────────────────────────────────────────────────

export interface ExperienceSummary {
  farmer_id: string;
  total_experience: number;
  level: ExperienceLevel;
  level_label: string;
  dimensions: Record<string, number>;
  transaction_count: number;
  annual_limit_per_dimension: number;
  total_limit: number;
  rule_version: string;
}

export interface ExperienceTransaction {
  id: string;
  farmer_id: string;
  green_action_id: string;
  dimension: string;
  base_value: number;
  source_recognition_ratio: number;
  effective_value: number;
  rule_version: string;
  calculated_at: string;
  input_evidence_ids: string[];
  calculation_trace: string | null;
}

export interface ExperienceHistoryResponse {
  farmer_id: string;
  count: number;
  transactions: ExperienceTransaction[];
}

// ─── Indicators ──────────────────────────────────────────────────────────────

export interface IndicatorSummary {
  score: number;
  level: string;
  details?: Record<string, unknown>;
  rule_version?: string;
  calculated_at?: string;
  calculation_trace?: string;
}

export interface IndicatorsResponse {
  farmer_id: string;
  indicator_count: number;
  indicators: Partial<Record<IndicatorType, IndicatorSummary>>;
  note: string;
}

// ─── Data Health ─────────────────────────────────────────────────────────────

export interface DomainHealth {
  status: DataHealthStatus;
  reasons: string[];
  actions: string[];
  rule_version?: string;
  calculated_at?: string;
}

export interface DataHealthResponse {
  farmer_id: string;
  domain_count: number;
  summary: Record<DataHealthStatus, number>;
  domains: Partial<Record<DataDomainKey, DomainHealth>>;
  note: string;
}

// ─── Anomalies ───────────────────────────────────────────────────────────────

export interface AnomalyEntity {
  id: string;
  record_id: string;
  document_id: string | null;
  anomaly_type: string;
  severity: AnomalySeverity;
  description: string;
  is_resolved: boolean;
  resolved_by: string | null;
  resolved_at: string | null;
}

export interface ReviewQueueResponse {
  farmer_id: string;
  count: number;
  items: AnomalyEntity[];
}

// ─── Recalculate-all ─────────────────────────────────────────────────────────

export interface RecalculateAllResponse {
  message: string;
  farmer_id: string;
  experience: ExperienceSummary;
  indicators: Record<string, { score: number; level: string }>;
  data_health_summary: Record<string, number>;
  rule_version: string | null;
}

// ─── Bank ────────────────────────────────────────────────────────────────────

export interface BankCaseSummary {
  authorization_id: string;
  farmer_id: string;
  farmer_name: string;
  purpose: string;
  data_scope: string[];
  start_at: string;
  expire_at: string;
}

export interface BankCasesResponse {
  institution_id: string;
  case_count: number;
  cases: BankCaseSummary[];
}

export interface IndicatorResultEntity {
  id: string;
  farmer_id: string;
  indicator_type: IndicatorType;
  score: number;
  level: string;
  details: Record<string, unknown>;
  rule_version: string;
  calculated_at: string;
  calculation_trace: string | null;
}

export interface DataHealthResultEntity {
  id: string;
  farmer_id: string;
  domain: DataDomainKey;
  status: DataHealthStatus;
  reasons: string[];
  actions: string[];
  affected_evidence_ids: string[];
  rule_version: string;
  calculated_at: string;
}

export interface FarmSummary {
  id: string;
  name: string;
  location: string | null;
  area_hectares: number | null;
}

export interface BankCaseDetailResponse {
  institution_id: string;
  farmer_id: string;
  profile: { id: string; real_name: string } | null;
  farms: FarmSummary[];
  experience: ExperienceSummary;
  indicators: IndicatorResultEntity[];
  data_health: DataHealthResultEntity[];
  anomalies: {
    total: number;
    unresolved: number;
    items: AnomalyEntity[];
  };
  disclaimer: string;
}

export interface VerificationResultEntity {
  id: string;
  record_id: string;
  source_level: SourceLevel;
  reason: string;
  verified_by: string;
  evidence_ids: string[];
}

export interface StandardizedRecordEntity {
  id: string;
  document_id: string;
  farmer_id: string;
  domain: DataDomainKey;
  record_type: string;
  data: Record<string, string>;
  source_level: SourceLevel;
  is_valid: boolean;
}

export interface EvidenceChainItem {
  document: DocumentEntity;
  fields: DocumentFieldEntity[];
  records: StandardizedRecordEntity[];
  verifications: VerificationResultEntity[];
}

export interface BankEvidenceResponse {
  institution_id: string;
  farmer_id: string;
  document_count: number;
  record_count: number;
  evidence: EvidenceChainItem[];
}
