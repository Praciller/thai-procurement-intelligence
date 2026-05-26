"use client";

import { useEffect, useMemo, useState, useTransition } from "react";
import { Download, Search } from "lucide-react";
import { API_BASE_URL, getRecords } from "@/lib/api";
import type { ProcurementRecord, RecordsResponse } from "@/types/api";
import { EmptyState, RecordTable } from "@/components/ui";

const provinces = ["", "Bangkok", "Chiang Mai", "Phuket", "Khon Kaen", "Chonburi", "Songkhla"];
const categories = ["", "IT", "Construction", "Medical Supplies", "Education", "Utilities", "Transport", "Office Equipment"];
const modes = ["keyword", "semantic", "hybrid"] as const;

type Mode = (typeof modes)[number];

export function RecordsClient({ initialRecords }: { initialRecords: RecordsResponse }) {
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
        setError("API returned no records. Run sample ingestion from the README command.");
      }
    });
    return () => {
      alive = false;
    };
  }, [initialRecords.total, query]);

  return (
    <div className="grid gap-5 lg:grid-cols-[18rem_1fr]">
      <aside className="rounded-lg border border-border bg-surface p-4">
        <div className="space-y-4">
          <label className="block text-sm font-medium">
            Keyword
            <span className="mt-2 flex items-center gap-2 rounded-md border border-border bg-background px-3">
              <Search size={16} className="text-muted" />
              <input
                className="min-h-10 w-full bg-transparent text-sm outline-none"
                value={q}
                onChange={(event) => setQ(event.target.value)}
                placeholder="IT, construction, hospital"
              />
            </span>
          </label>
          <label className="block text-sm font-medium">
            Province
            <select className="mt-2 min-h-10 w-full rounded-md border border-border bg-background px-3 text-sm" value={province} onChange={(event) => setProvince(event.target.value)}>
              {provinces.map((item) => (
                <option key={item || "all"} value={item}>
                  {item || "All provinces"}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm font-medium">
            Category
            <select className="mt-2 min-h-10 w-full rounded-md border border-border bg-background px-3 text-sm" value={category} onChange={(event) => setCategory(event.target.value)}>
              {categories.map((item) => (
                <option key={item || "all"} value={item}>
                  {item || "All categories"}
                </option>
              ))}
            </select>
          </label>
          <fieldset>
            <legend className="text-sm font-medium">Search mode</legend>
            <div className="mt-2 grid grid-cols-3 rounded-md border border-border bg-background p-1">
              {modes.map((item) => (
                <button
                  key={item}
                  className={`min-h-9 rounded px-2 text-xs font-medium capitalize ${mode === item ? "bg-accent text-background" : "text-muted hover:bg-surface"}`}
                  onClick={() => setMode(item)}
                  type="button"
                >
                  {item}
                </button>
              ))}
            </div>
          </fieldset>
          <label className="block text-sm font-medium">
            Sort
            <select className="mt-2 min-h-10 w-full rounded-md border border-border bg-background px-3 text-sm" value={sort} onChange={(event) => setSort(event.target.value)}>
              <option value="date_desc">Newest first</option>
              <option value="date_asc">Oldest first</option>
              <option value="budget_desc">Budget high to low</option>
              <option value="budget_asc">Budget low to high</option>
            </select>
          </label>
          <a
            className="focus-ring inline-flex min-h-10 w-full items-center justify-center gap-2 rounded-md border border-border bg-background px-3 text-sm font-medium hover:bg-surface-strong"
            href={`${API_BASE_URL}/export/records.csv`}
          >
            <Download size={16} />
            Export CSV
          </a>
        </div>
      </aside>

      <section aria-live="polite">
        <div className="mb-3 flex items-center justify-between text-sm text-muted">
          <span>{isPending ? "Updating results..." : `${data.total} records`}</span>
          <span className="capitalize">{mode} mode</span>
        </div>
        {error ? <EmptyState title="No API data yet" body={error} /> : <RecordTable records={data.items as ProcurementRecord[]} />}
      </section>
    </div>
  );
}

