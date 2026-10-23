"use client";

import { useEffect, useMemo, useState, useTransition } from "react";
import { Download, Search } from "lucide-react";
import { getApiUrl, searchRecords } from "@/lib/api";
import { getDictionary, normalizeLocale } from "@/lib/i18n";
import type { ProcurementRecord, RecordFacets, RecordsResponse } from "@/types/api";
import { EmptyState, RecordTable } from "@/components/ui";

const modes = ["keyword", "semantic", "hybrid"] as const;

type Mode = (typeof modes)[number];

export function RecordsClient({ initialRecords, facets, locale = "en" }: { initialRecords: RecordsResponse; facets: RecordFacets; locale?: string }) {
  const normalizedLocale = normalizeLocale(locale);
  const dictionary = getDictionary(normalizedLocale);
  const text = dictionary.recordsClient;
  const provinces = ["", ...facets.provinces];
  const categories = ["", ...facets.categories];
  const tableLabels = { ...dictionary.table, ...dictionary.common };
  const [q, setQ] = useState("");
  const [province, setProvince] = useState("");
  const [category, setCategory] = useState("");
  const [mode, setMode] = useState<Mode>("keyword");
  const [sort, setSort] = useState("date_desc");
  const [data, setData] = useState(initialRecords);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [isPending, startTransition] = useTransition();

  const query = useMemo(() => {
    const params = new URLSearchParams({ page: String(page), page_size: "20", search_mode: mode, sort });
    if (q) params.set("q", q);
    if (province) params.set("province", province);
    if (category) params.set("category", category);
    return `?${params.toString()}`;
  }, [category, mode, page, province, q, sort]);

  useEffect(() => {
    let alive = true;
    startTransition(async () => {
      setError(null);
      try {
        const next = await searchRecords(query);
        if (!alive) return;
        setData(next);
      } catch {
        if (!alive) return;
        setError(text.noApiBody);
      }
    });
    return () => {
      alive = false;
    };
  }, [initialRecords.total, query, text.noApiBody]);

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
                onChange={(event) => { setQ(event.target.value); setPage(1); }}
                placeholder={text.keywordPlaceholder}
              />
            </span>
          </label>
          <label className="block text-sm font-medium">
            {text.province}
            <select className="mt-2 min-h-10 w-full rounded-md border border-border bg-background px-3 text-sm" value={province} onChange={(event) => { setProvince(event.target.value); setPage(1); }}>
              {provinces.map((item) => (
                <option key={item || "all"} value={item}>
                  {item || text.allProvinces}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm font-medium">
            {text.category}
            <select className="mt-2 min-h-10 w-full rounded-md border border-border bg-background px-3 text-sm" value={category} onChange={(event) => { setCategory(event.target.value); setPage(1); }}>
              {categories.map((item) => (
                <option key={item || "all"} value={item}>
                  {item || text.allCategories}
                </option>
              ))}
            </select>
          </label>
          <fieldset>
            <legend className="text-sm font-medium">{text.searchMode}</legend>
            <div className="mt-2 grid grid-cols-3 rounded-md border border-border bg-background p-1">
              {modes.map((item) => (
                <button
                  key={item}
                  className={`min-h-9 rounded px-2 text-xs font-medium capitalize ${mode === item ? "bg-accent text-background" : "text-muted hover:bg-surface"}`}
                  onClick={() => { setMode(item); setPage(1); }}
                  aria-pressed={mode === item}
                  type="button"
                >
                  {text.modeLabels[item]}
                </button>
              ))}
            </div>
          </fieldset>
          <label className="block text-sm font-medium">
            {text.sort}
            <select className="mt-2 min-h-10 w-full rounded-md border border-border bg-background px-3 text-sm" value={sort} onChange={(event) => { setSort(event.target.value); setPage(1); }}>
              <option value="date_desc">{text.sortOptions.date_desc}</option>
              <option value="date_asc">{text.sortOptions.date_asc}</option>
              <option value="budget_desc">{text.sortOptions.budget_desc}</option>
              <option value="budget_asc">{text.sortOptions.budget_asc}</option>
            </select>
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
        {isPending ? (
          <div className="space-y-3 rounded-lg border border-border bg-surface p-4" aria-label={text.updatingResults}>
            <div className="h-5 w-44 animate-pulse rounded bg-surface-strong" />
            <div className="h-12 animate-pulse rounded bg-surface-strong" />
            <div className="h-12 animate-pulse rounded bg-surface-strong" />
            <div className="h-12 animate-pulse rounded bg-surface-strong" />
          </div>
        ) : error ? (
          <EmptyState title={text.noApiTitle} body={error} />
        ) : (
          <>
            <RecordTable records={data.items as ProcurementRecord[]} labels={tableLabels} locale={normalizedLocale} />
            {mode === "keyword" && data.total > data.page_size ? (
              <nav aria-label="Search result pages" className="mt-4 flex items-center justify-between gap-3 text-sm">
                <button type="button" className="focus-ring rounded-md border border-border px-3 py-2 disabled:opacity-40" disabled={isPending || page <= 1} onClick={() => setPage((current) => Math.max(1, current - 1))}>{text.previousPage}</button>
                <span aria-live="polite">{text.pageOf(page, Math.ceil(data.total / data.page_size))}</span>
                <button type="button" className="focus-ring rounded-md border border-border px-3 py-2 disabled:opacity-40" disabled={isPending || page >= Math.ceil(data.total / data.page_size)} onClick={() => setPage((current) => current + 1)}>{text.nextPage}</button>
              </nav>
            ) : null}
          </>
        )}
      </section>
    </div>
  );
}
