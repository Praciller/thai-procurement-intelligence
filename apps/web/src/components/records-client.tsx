"use client";

import { useEffect, useMemo, useState, useTransition } from "react";
import { Download, Search } from "lucide-react";
import { getApiUrl, getRecordFacets, getRecords } from "@/lib/api";
import { getDictionary, normalizeLocale } from "@/lib/i18n";
import { buildRecordsQuery, getRecordsPagination, updateRecordsSearchState } from "@/lib/records-state.js";
import type { ProcurementRecord, RecordFacets, RecordsResponse } from "@/types/api";
import { EmptyState, RecordTable } from "@/components/ui";

const modes = ["keyword", "semantic", "hybrid"] as const;
const pageSize = 20;
const maxRankedResults = 5_000;

type Mode = (typeof modes)[number];
type SearchState = { q: string; province: string; category: string; mode: Mode; sort: string; page: number };

export function RecordsClient({
  initialRecords,
  initialApiUnavailable = false,
  locale = "en",
}: {
  initialRecords: RecordsResponse;
  initialApiUnavailable?: boolean;
  locale?: string;
}) {
  const normalizedLocale = normalizeLocale(locale);
  const dictionary = getDictionary(normalizedLocale);
  const text = dictionary.recordsClient;
  const tableLabels = { ...dictionary.table, ...dictionary.common };
  const [search, setSearch] = useState<SearchState>({
    q: "",
    province: "",
    category: "",
    mode: "keyword",
    sort: "date_desc",
    page: initialRecords.page,
  });
  const { q, province, category, mode, sort, page } = search;
  const [data, setData] = useState(initialRecords);
  const [apiUnavailable, setApiUnavailable] = useState(initialApiUnavailable);
  const [facets, setFacets] = useState<RecordFacets>({ provinces: [], categories: [] });
  const [facetsUnavailable, setFacetsUnavailable] = useState(false);
  const [isPending, startTransition] = useTransition();

  const updateSearch = (changes: Partial<SearchState>) => {
    setSearch((current) => updateRecordsSearchState(current, changes));
  };
  const query = useMemo(() => buildRecordsQuery(search, pageSize), [search]);

  useEffect(() => {
    let alive = true;
    startTransition(async () => {
      const result = await getRecords(query);
      if (!alive) return;
      if (result.ok) {
        setData(result.data);
        setApiUnavailable(false);
      } else {
        setData({ items: [], total: 0, page, page_size: pageSize });
        setApiUnavailable(true);
      }
    });
    return () => {
      alive = false;
    };
  }, [page, query]);

  useEffect(() => {
    let alive = true;
    void getRecordFacets().then((result) => {
      if (!alive) return;
      if (result.ok) {
        setFacets(result.data);
        setFacetsUnavailable(false);
      } else {
        setFacetsUnavailable(true);
      }
    });
    return () => {
      alive = false;
    };
  }, []);

  const provinces = ["", ...new Set([...facets.provinces, province].filter(Boolean))];
  const categories = ["", ...new Set([...facets.categories, category].filter(Boolean))];
  const pagination = getRecordsPagination(data.total, page, data.page_size, mode !== "keyword" && Boolean(q.trim()), maxRankedResults);
  const sortDisabled = mode !== "keyword" && Boolean(q.trim());
  const pageLabel = text.pageLabel
    .replace("{page}", page.toLocaleString(normalizedLocale === "th" ? "th-TH" : "en-US"))
    .replace("{totalPages}", pagination.totalPages.toLocaleString(normalizedLocale === "th" ? "th-TH" : "en-US"));

  return (
    <div className="grid gap-5 lg:grid-cols-[18rem_1fr]">
      <aside className="rounded-lg border border-border bg-surface p-4">
        <div className="space-y-4">
          <label className="block text-sm font-medium">
            {text.keyword}
            <span className="mt-2 flex items-center gap-2 rounded-md border border-border bg-background px-3">
              <Search size={16} className="text-muted" />
              <input
                className="min-h-10 w-full bg-transparent text-sm outline-none"
                value={q}
                onChange={(event) => {
                  updateSearch({ q: event.target.value });
                }}
                placeholder={text.keywordPlaceholder}
              />
            </span>
          </label>
          <label className="block text-sm font-medium">
            {text.province}
            <select
              className="mt-2 min-h-10 w-full rounded-md border border-border bg-background px-3 text-sm"
              value={province}
              onChange={(event) => {
                updateSearch({ province: event.target.value });
              }}
            >
              {provinces.map((item) => (
                <option key={item || "all"} value={item}>
                  {item || text.allProvinces}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm font-medium">
            {text.category}
            <select
              className="mt-2 min-h-10 w-full rounded-md border border-border bg-background px-3 text-sm"
              value={category}
              onChange={(event) => {
                updateSearch({ category: event.target.value });
              }}
            >
              {categories.map((item) => (
                <option key={item || "all"} value={item}>
                  {item || text.allCategories}
                </option>
              ))}
            </select>
          </label>
          {facetsUnavailable && <p role="status" className="text-xs text-muted">{text.facetsUnavailable}</p>}
          <fieldset>
            <legend className="text-sm font-medium">{text.searchMode}</legend>
            <div className="mt-2 grid grid-cols-3 rounded-md border border-border bg-background p-1">
              {modes.map((item) => (
                <button
                  key={item}
                  className={`min-h-9 rounded px-2 text-xs font-medium capitalize ${mode === item ? "bg-accent text-background" : "text-muted hover:bg-surface"}`}
                  onClick={() => {
                    updateSearch({ mode: item });
                  }}
                  type="button"
                >
                  {text.modeLabels[item]}
                </button>
              ))}
            </div>
          </fieldset>
          <label className="block text-sm font-medium">
            {text.sort}
            <select
              className="mt-2 min-h-10 w-full rounded-md border border-border bg-background px-3 text-sm disabled:opacity-50"
              value={sort}
              disabled={sortDisabled}
              onChange={(event) => {
                updateSearch({ sort: event.target.value });
              }}
            >
              <option value="date_desc">{text.sortOptions.date_desc}</option>
              <option value="date_asc">{text.sortOptions.date_asc}</option>
              <option value="budget_desc">{text.sortOptions.budget_desc}</option>
              <option value="budget_asc">{text.sortOptions.budget_asc}</option>
            </select>
            {sortDisabled && <span className="mt-1 block text-xs text-muted">{text.sortKeywordOnly}</span>}
          </label>
          <a
            className="focus-ring inline-flex min-h-10 w-full items-center justify-center gap-2 rounded-md border border-border bg-background px-3 text-sm font-medium hover:bg-surface-strong"
            href={getApiUrl("/export/records.csv")}
          >
            <Download size={16} />
            {text.exportCsv}
          </a>
        </div>
      </aside>

      <section aria-live="polite">
        <div className="mb-3 flex items-center justify-between text-sm text-muted">
          <span>{isPending ? text.updatingResults : `${data.total.toLocaleString(normalizedLocale === "th" ? "th-TH" : "en-US")} ${text.records}`}</span>
          <span>{text.modeLabels[mode]}</span>
        </div>
        {pagination.hasRankedWindowLimit && <p className="mb-3 text-sm text-muted">{text.rankedWindowLimit}</p>}
        {isPending ? (
          <div className="space-y-3 rounded-lg border border-border bg-surface p-4" aria-label={text.updatingResults}>
            <div className="h-5 w-44 animate-pulse rounded bg-surface-strong" />
            <div className="h-12 animate-pulse rounded bg-surface-strong" />
            <div className="h-12 animate-pulse rounded bg-surface-strong" />
            <div className="h-12 animate-pulse rounded bg-surface-strong" />
          </div>
        ) : apiUnavailable ? (
          <EmptyState title={text.apiUnavailableTitle} body={text.apiUnavailableBody} />
        ) : data.items.length === 0 ? (
          <EmptyState title={text.noResultsTitle} body={text.noResultsBody} />
        ) : (
          <RecordTable records={data.items as ProcurementRecord[]} labels={tableLabels} locale={normalizedLocale} />
        )}
        <nav className="mt-4 flex items-center justify-between gap-3" aria-label={text.paginationLabel}>
          <button
            className="focus-ring min-h-10 rounded-md border border-border bg-background px-3 text-sm disabled:cursor-not-allowed disabled:opacity-50"
            type="button"
            disabled={page <= 1 || isPending}
            onClick={() => setSearch((current) => ({ ...current, page: Math.max(1, current.page - 1) }))}
          >
            {text.previousPage}
          </button>
          <span className="text-sm text-muted" aria-live="polite">{pageLabel}</span>
          <button
            className="focus-ring min-h-10 rounded-md border border-border bg-background px-3 text-sm disabled:cursor-not-allowed disabled:opacity-50"
            type="button"
            disabled={pagination.nextDisabled || isPending}
            onClick={() => setSearch((current) => ({ ...current, page: current.page + 1 }))}
          >
            {text.nextPage}
          </button>
        </nav>
      </section>
    </div>
  );
}
