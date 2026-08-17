/**
 * GreenFin API client.
 *
 * Every backend call goes through here (proxied to the backend by Vite in dev), and
 * every function has a concrete return type from types.ts. The bank pages previously
 * bypassed this module with raw fetch() calls and their own hardcoded institution id,
 * duplicating error handling; they now use these helpers too.
 */

import type {
  BankCaseDetailResponse,
  BankCasesResponse,
  BankEvidenceResponse,
  ConfirmResponse,
  DataHealthResponse,
  DocumentFieldsResponse,
  ExperienceHistoryResponse,
  ExperienceSummary,
  FarmerDocumentsResponse,
  HealthResponse,
  IndicatorsResponse,
  RecalculateAllResponse,
  ReviewQueueResponse,
  UploadResponse,
} from "./types";

const BASE = "/api";

/** Demo institution. Single source of truth — was duplicated across 3 bank pages. */
export const DEMO_INSTITUTION_ID = "bank-taishin";

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }

  /** True when the backend refused for authorization reasons. */
  get isForbidden(): boolean {
    return this.status === 403;
  }
}

/** Pull a human-readable message out of FastAPI's varied error shapes. */
function extractMessage(payload: unknown, fallback: string): string {
  if (typeof payload === "string") return payload;
  if (payload && typeof payload === "object") {
    const detail = (payload as { detail?: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (detail && typeof detail === "object") {
      const message = (detail as { message?: unknown }).message;
      if (typeof message === "string") return message;
      return JSON.stringify(detail);
    }
  }
  return fallback;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers:
      options?.body instanceof FormData
        ? options.headers
        : { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });

  if (!res.ok) {
    const payload = await res.json().catch(() => null);
    throw new ApiError(res.status, extractMessage(payload, res.statusText));
  }

  return res.json() as Promise<T>;
}

// ─── Health ──────────────────────────────────────────────────────────────────

export const getHealth = () => request<HealthResponse>("/health");

// ─── Farmer: documents ───────────────────────────────────────────────────────

export const getFarmerDocuments = (farmerId: string) =>
  request<FarmerDocumentsResponse>(`/farmers/${farmerId}/documents`);

export const getDocumentFields = (docId: string) =>
  request<DocumentFieldsResponse>(`/documents/${docId}/fields`);

export const uploadDocument = (
  file: File,
  farmerId: string,
  domain: string,
  sourceLevel = "V1"
) => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("farmer_id", farmerId);
  formData.append("domain", domain);
  formData.append("source_level", sourceLevel);

  return request<UploadResponse>("/documents/upload", {
    method: "POST",
    body: formData,
  });
};

export const confirmFields = (
  docId: string,
  corrections: Record<string, string> = {}
) =>
  request<ConfirmResponse>(`/documents/${docId}/confirm`, {
    method: "POST",
    body: JSON.stringify({ corrections }),
  });

export const normalizeDocument = (docId: string) =>
  request<{ document_id: string; message: string }>(
    `/documents/${docId}/normalize`,
    { method: "POST" }
  );

export const verifyDocument = (docId: string) =>
  request<{ document_id: string; status: string; anomaly_count: number }>(
    `/documents/${docId}/verify`,
    { method: "POST" }
  );

/** Run the full post-upload pipeline: confirm → normalize → verify. */
export const processDocument = async (docId: string) => {
  await confirmFields(docId);
  await normalizeDocument(docId);
  return verifyDocument(docId);
};

// ─── Farmer: analysis ────────────────────────────────────────────────────────

export const getExperienceSummary = (farmerId: string) =>
  request<ExperienceSummary>(`/farmers/${farmerId}/experience`);

export const getExperienceHistory = (farmerId: string) =>
  request<ExperienceHistoryResponse>(`/farmers/${farmerId}/experience/history`);

export const getIndicators = (farmerId: string) =>
  request<IndicatorsResponse>(`/farmers/${farmerId}/indicators`);

export const calculateIndicators = (farmerId: string) =>
  request<{ farmer_id: string; message: string }>(
    `/farmers/${farmerId}/indicators/calculate`,
    { method: "POST" }
  );

export const getDataHealth = (farmerId: string) =>
  request<DataHealthResponse>(`/farmers/${farmerId}/data-health`);

export const calculateDataHealth = (farmerId: string) =>
  request<{ farmer_id: string; message: string }>(
    `/farmers/${farmerId}/data-health/calculate`,
    { method: "POST" }
  );

export const getReviewQueue = (farmerId: string) =>
  request<ReviewQueueResponse>(`/farmers/${farmerId}/review-queue`);

/**
 * Recalculate experience + indicators + data health in one backend call.
 *
 * Replaces three sequential client-side POSTs, where a mid-sequence failure left
 * the farmer in a partially recalculated state.
 */
export const recalculateAll = (farmerId: string) =>
  request<RecalculateAllResponse>(`/farmers/${farmerId}/recalculate-all`, {
    method: "POST",
  });

// ─── Bank ────────────────────────────────────────────────────────────────────

export const getBankCases = (institutionId: string = DEMO_INSTITUTION_ID) =>
  request<BankCasesResponse>(`/bank/${institutionId}/cases`);

export const getBankCaseDetail = (
  farmerId: string,
  institutionId: string = DEMO_INSTITUTION_ID
) => request<BankCaseDetailResponse>(`/bank/${institutionId}/cases/${farmerId}`);

export const getBankCaseEvidence = (
  farmerId: string,
  institutionId: string = DEMO_INSTITUTION_ID
) =>
  request<BankEvidenceResponse>(
    `/bank/${institutionId}/cases/${farmerId}/evidence`
  );
