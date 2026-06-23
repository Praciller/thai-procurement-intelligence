export type ProcurementRecord = {
  id: string;
  source_name: string;
  dataset_type: "synthetic" | "official_snapshot";
  source_record_id: string | null;
  content_hash: string;
  project_name: string;
  agency_name: string | null;
  province: string | null;
  procurement_method: string | null;
  procurement_category: string | null;
  budget_amount: string | number | null;
  winning_amount: string | number | null;
  winner_name: string | null;
  announcement_date: string | null;
  contract_date: string | null;
  source_url: string | null;
  source_snapshot_id: string | null;
  source_retrieved_at: string | null;
  source_published_at: string | null;
  source_updated_at: string | null;
  source_license: string | null;
  source_checksum: string | null;
  mapping_version: string | null;
  is_synthetic: boolean;
  raw_text: string | null;
  normalized_text: string | null;
  imported_at: string;
  updated_at: string;
  created_at?: string;
  ai_summary?: string | null;
  relevance_score?: number | null;
};

export type RecordsResponse = {
  items: ProcurementRecord[];
  total: number;
  page: number;
  page_size: number;
};

export type AnalyticsBucket = {
  label: string;
  count: number;
  total_budget: string | number | null;
};

export type AnalyticsOverview = {
  total_records: number;
  total_budget: string | number;
  average_budget: string | number;
  records_by_province: AnalyticsBucket[];
  records_by_category: AnalyticsBucket[];
  records_by_month: AnalyticsBucket[];
  top_agencies: AnalyticsBucket[];
  top_projects: ProcurementRecord[];
};

export type IngestionRun = {
  id: string;
  source_name: string;
  snapshot_id: string | null;
  mapping_version: string | null;
  started_at: string;
  finished_at: string | null;
  status: string;
  total_rows: number;
  inserted_rows: number;
  updated_rows: number;
  skipped_rows: number;
  failed_rows: number;
  duplicate_rows: number;
  warning_rows: number;
  normalized_rows: number;
  unchanged_rows: number;
  error_message: string | null;
};

export type AssistantResponse = {
  answer: string;
  ai_enabled: boolean;
  citations: Array<{
    id: string;
    project_name: string;
    agency_name: string | null;
    source_url: string | null;
    source_record_id: string | null;
    source_snapshot_id: string | null;
  }>;
  retrieved_records: ProcurementRecord[];
};

export type DatasetStatus = {
  dataset_mode: "synthetic" | "official_snapshot";
  freshness_status: "not_applicable" | "unknown" | "current_snapshot" | "stale_snapshot";
  source: null | {
    snapshot_id: string;
    source_name: string;
    source_organization: string;
    source_url: string;
    retrieved_at: string;
    coverage_start: string | null;
    coverage_end: string | null;
    license: string;
    sha256: string;
    record_count_raw: number;
    mapping_version: string;
  };
  quality: null | {
    valid_records: number;
    rejected_records: number;
    duplicate_records: number;
    warning_records?: number;
    checksum_verified?: boolean;
  };
  latest_run: IngestionRun | null;
};

export type SummaryResponse = {
  procurement_id: string;
  provider: string;
  model: string;
  summary_text: string;
  cached: boolean;
};
