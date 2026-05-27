import { Database } from "lucide-react";
import { EmptyState, PageHeader, Section, Stat } from "@/components/ui";
import { formatDate, getAnalytics, getIngestionRuns } from "@/lib/api";
import { getDictionary, normalizeLocale } from "@/lib/i18n";

export default async function DataStatusPage({ searchParams }: { searchParams?: Promise<{ lang?: string | string[] }> }) {
  const params = await searchParams;
  const locale = normalizeLocale(params?.lang);
  const dictionary = getDictionary(locale);
  const [analytics, runs] = await Promise.all([getAnalytics(), getIngestionRuns()]);

  return (
    <Section>
      <PageHeader
        title={dictionary.dataStatus.title}
        description={dictionary.dataStatus.description}
      />
      <div className="grid gap-4 sm:grid-cols-3">
        <Stat label={dictionary.dataStatus.records} value={analytics.total_records.toLocaleString(locale === "th" ? "th-TH" : "en-US")} />
        <Stat label={dictionary.dataStatus.ingestionRuns} value={runs.length.toLocaleString(locale === "th" ? "th-TH" : "en-US")} />
        <Stat label={dictionary.dataStatus.latestStatus} value={runs[0]?.status || dictionary.dataStatus.noRun} />
      </div>

      <div className="mt-6 rounded-lg border border-border bg-surface p-5">
        <div className="mb-4 flex items-center gap-2">
          <Database size={18} className="text-accent-strong" />
          <h2 className="text-base font-semibold">{dictionary.dataStatus.recentRuns}</h2>
        </div>
        {runs.length ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-wide text-muted">
                <tr>
                  <th className="py-2 pr-4">{dictionary.dataStatus.source}</th>
                  <th className="py-2 pr-4">{dictionary.dataStatus.status}</th>
                  <th className="py-2 pr-4">{dictionary.dataStatus.rows}</th>
                  <th className="py-2 pr-4">{dictionary.dataStatus.inserted}</th>
                  <th className="py-2 pr-4">{dictionary.dataStatus.updated}</th>
                  <th className="py-2 pr-4">{dictionary.dataStatus.failed}</th>
                  <th className="py-2 pr-4">{dictionary.dataStatus.finished}</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((run) => (
                  <tr key={run.id} className="border-t border-border">
                    <td className="py-3 pr-4">{run.source_name}</td>
                    <td className="py-3 pr-4">{run.status}</td>
                    <td className="py-3 pr-4 font-mono text-xs">{run.total_rows}</td>
                    <td className="py-3 pr-4 font-mono text-xs">{run.inserted_rows}</td>
                    <td className="py-3 pr-4 font-mono text-xs">{run.updated_rows}</td>
                    <td className="py-3 pr-4 font-mono text-xs">{run.failed_rows}</td>
                    <td className="py-3 pr-4 text-muted">{formatDate(run.finished_at, locale)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState title={dictionary.dataStatus.emptyTitle} body={dictionary.dataStatus.emptyBody} />
        )}
      </div>
    </Section>
  );
}
