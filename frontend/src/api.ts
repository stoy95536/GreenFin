/**
 * GreenFin API client.
 * All backend calls go through /api/ prefix (proxied by Vite in dev).
 */

const BASE = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || JSON.stringify(error));
  }
  return res.json();
}

// Health
export const getHealth = () => request<any>("/health");

// Farmers
export const getFarmerDocuments = (farmerId: string) =>
  request<any>(`/farmers/${farmerId}/documents`);

export const getExperienceSummary = (farmerId: string) =>
  request<any>(`/farmers/${farmerId}/experience`);

export const getExperienceHistory = (farmerId: string) =>
  request<any>(`/farmers/${farmerId}/experience/history`);

export const getIndicators = (farmerId: string) =>
  request<any>(`/farmers/${farmerId}/indicators`);

export const calculateIndicators = (farmerId: string) =>
  request<any>(`/farmers/${farmerId}/indicators/calculate`, { method: "POST" });

export const getDataHealth = (farmerId: string) =>
  request<any>(`/farmers/${farmerId}/data-health`);

export const calculateDataHealth = (farmerId: string) =>
  request<any>(`/farmers/${farmerId}/data-health/calculate`, { method: "POST" });

export const getReviewQueue = (farmerId: string) =>
  request<any>(`/farmers/${farmerId}/review-queue`);

export const recalculateExperience = (farmerId: string) =>
  request<any>(`/farmers/${farmerId}/experience/recalculate`, { method: "POST" });

// Documents
export const uploadDocument = async (
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

  const res = await fetch(`${BASE}/documents/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error((await res.json()).detail || "Upload failed");
  return res.json();
};

export const confirmFields = (docId: string, corrections: Record<string, string> = {}) =>
  request<any>(`/documents/${docId}/confirm`, {
    method: "POST",
    body: JSON.stringify({ corrections }),
  });

export const normalizeDocument = (docId: string) =>
  request<any>(`/documents/${docId}/normalize`, { method: "POST" });

export const verifyDocument = (docId: string) =>
  request<any>(`/documents/${docId}/verify`, { method: "POST" });

export const getDocumentFields = (docId: string) =>
  request<any>(`/documents/${docId}/fields`);
