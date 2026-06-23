import type {
  AnalyticsOverview,
  AssistantResponse,
  DatasetStatus,
  IngestionRun,
  ProcurementRecord,
  RecordsResponse,
  SummaryResponse,
} from "@/types/api";
import { resolveApiUrl } from "@/lib/api-url";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api";

type FetchOptions = RequestInit & {
  next?: { revalidate?: number };
};

export async function apiFetch<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const response = await fetch(getApiUrl(path), {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `API request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function getApiUrl(path: string) {
  return resolveApiUrl(path, {
    apiBaseUrl: API_BASE_URL,
    hasWindow: typeof window !== "undefined",
    siteUrl: process.env.NEXT_PUBLIC_SITE_URL,
    vercelUrl: process.env.VERCEL_URL,
  });
}

export async function safeApiFetch<T>(path: string, fallback: T, options: FetchOptions = {}): Promise<T> {
  try {
    return await apiFetch<T>(path, options);
  } catch {
    return fallback;
  }
}

export function formatMoney(value: string | number | null | undefined, locale = "en") {
  if (value === null || value === undefined || value === "") return locale === "th" ? "ไม่มีข้อมูล" : "Not available";
  const amount = Number(value);
  if (Number.isNaN(amount)) return String(value);
  return new Intl.NumberFormat(locale === "th" ? "th-TH" : "en-US", {
    style: "currency",
    currency: "THB",
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatDate(value: string | null | undefined, locale = "en") {
  if (!value) return locale === "th" ? "ไม่มีข้อมูล" : "Not available";
  return new Intl.DateTimeFormat(locale === "th" ? "th-TH" : "en-GB", { year: "numeric", month: "short", day: "2-digit" }).format(new Date(value));
}

export const emptyRecords: RecordsResponse = { items: [], total: 0, page: 1, page_size: 20 };

export const emptyAnalytics: AnalyticsOverview = {
  total_records: 0,
  total_budget: 0,
  average_budget: 0,
  records_by_province: [],
  records_by_category: [],
  records_by_month: [],
  top_agencies: [],
  top_projects: [],
};

export function getRecords(query = "") {
  return safeApiFetch<RecordsResponse>(`/records${query}`, emptyRecords, { cache: "no-store" });
}

export function getRecord(id: string) {
  return safeApiFetch<ProcurementRecord | null>(`/records/${id}`, null, { cache: "no-store" });
}

export function getSimilar(id: string) {
  return safeApiFetch<ProcurementRecord[]>(`/records/${id}/similar`, [], { cache: "no-store" });
}

export function getAnalytics() {
  return safeApiFetch<AnalyticsOverview>("/analytics/overview", emptyAnalytics, { cache: "no-store" });
}

export function getIngestionRuns() {
  return safeApiFetch<IngestionRun[]>("/ingestion/status", [], { cache: "no-store" });
}

export function getDatasetStatus() {
  return safeApiFetch<DatasetStatus>(
    "/dataset/status",
    { dataset_mode: "synthetic", freshness_status: "not_applicable", source: null, quality: null, latest_run: null },
    { cache: "no-store" },
  );
}

export function postSummary(id: string) {
  return apiFetch<SummaryResponse>(`/records/${id}/summary`, { method: "POST" });
}

export function askAssistant(question: string) {
  return apiFetch<AssistantResponse>("/assistant/ask", {
    method: "POST",
    body: JSON.stringify({ question, limit: 8 }),
  });
}
