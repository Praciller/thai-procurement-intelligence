"use client";

import { useEffect, useMemo, useState, useTransition } from "react";
import { Download, Search } from "lucide-react";
import { getApiUrl, getRecords } from "@/lib/api";
import { getDictionary, normalizeLocale } from "@/lib/i18n";
import type { ProcurementRecord, RecordsResponse } from "@/types/api";
import { EmptyState, RecordTable } from "@/components/ui";

const syntheticProvinces = ["Bangkok", "Chiang Mai", "Phuket", "Khon Kaen", "Chonburi", "Songkhla"];
const syntheticCategories = ["IT", "Construction", "Medical Supplies", "Education", "Utilities", "Transport", "Office Equipment"];
const modes = ["keyword", "semantic", "hybrid"] as const;

type Mode = (typeof modes)[number];

export function RecordsClient({ initialRecords, locale = "en" }: { initialRecords: RecordsResponse; locale?: string }) {
  const normalizedLocale = normalizeLocale(locale);
  const dictionary = getDictionary(normalizedLocale);
  const text = dictionary.recordsClient;
  const official = initialRecords.items.some((record) => !record.is_synthetic);
  const provinces = [
    "",
    ...new Set(
      official
        ? initialRecords.items.map((record) => record.province).filter((value): value is string => Boolean(value))
        : syntheticProvinces,
    ),
  ];
  const categories = [
    "",
    ...new Set(
      official
        ? initialRecords.items.map((record) => record.procurement_category).filter((value): value is string => Boolean(value))
        : syntheticCategories,
    ),
  ];
  const tableLabels = { ...dictionary.table, ...dictionary.common };
  const [q, setQ] = useState("");
  const [province, setProvince] = useState("");
  const [category, setCategory] = useState("");
  const [mode, setMode] = useState<Mode>("keyword");
  const [sort, setSort] = useState("date_desc");
  const [data, setData] = useState(initialRecords);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const query = useMemo(() => {
    const params = new URLSearchParams({ page_size: "20", search_mode: mode, sort });
    if (q) params.set("q", q);
    if (province) params.set("province", province);
    if (category) params.set("category", category);
    return `?${params.toString()}`;
  }, [category, mode, province, q, sort]);

  useEffect(() => {
    let alive = true;
    startTransition(async () => {
      setError(null);
      const next = await getRecords(query);
      if (!alive) return;
      setData(next);
      if (!next.items.length && initialRecords.total === 0) {
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
                onChange={(event) => setQ(event.target.value)}
                placeholder={text.keywordPlaceholder}
              />
            </span>
          </label>
          <label className="block text-sm font-medium">
            {text.province}
            <select className="mt-2 min-h-10 w-full rounded-md border border-border bg-background px-3 text-sm" value={province} onChange={(event) => setProvince(event.target.value)}>
              {provinces.map((item) => (
                <option key={item || "all"} value={item}>
                  {item || text.allProvinces}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm font-medium">
            {text.category}
            <select className="mt-2 min-h-10 w-full rounded-md border border-border bg-background px-3 text-sm" value={category} onChange={(event) => setCategory(event.target.value)}>
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
                  onClick={() => setMode(item)}
                  type="button"
                >
                  {text.modeLabels[item]}
                </button>
              ))}
            </div>
          </fieldset>
          <label className="block text-sm font-medium">
            {text.sort}
            <select className="mt-2 min-h-10 w-full rounded-md border border-border bg-background px-3 text-sm" value={sort} onChange={(event) => setSort(event.target.value)}>
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
          <RecordTable records={data.items as ProcurementRecord[]} labels={tableLabels} locale={normalizedLocale} />
        )}
      </section>
    </div>
  );
}
