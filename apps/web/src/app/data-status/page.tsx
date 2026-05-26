import { Database } from "lucide-react";
import { EmptyState, PageHeader, Section, Stat } from "@/components/ui";
import { formatDate, getAnalytics, getIngestionRuns } from "@/lib/api";

export default async function DataStatusPage() {
  const [analytics, runs] = await Promise.all([getAnalytics(), getIngestionRuns()]);

  return (
    <Section>
      <PageHeader
        title="Data Status"
        description="Read-only operational view for ingestion runs, record counts, sample source status, and demo readiness."
      />
      <div className="grid gap-4 sm:grid-cols-3">
        <Stat label="Records" value={analytics.total_records.toLocaleString()} />
        <Stat label="Ingestion runs" value={runs.length.toLocaleString()} />
        <Stat label="Latest status" value={runs[0]?.status || "No run"} />
      </div>

      <div className="mt-6 rounded-lg border border-border bg-surface p-5">
        <div className="mb-4 flex items-center gap-2">
          <Database size={18} className="text-accent-strong" />
          <h2 className="text-base font-semibold">Recent ingestion runs</h2>
        </div>
        {runs.length ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-wide text-muted">
                <tr>
                  <th className="py-2 pr-4">Source</th>
                  <th className="py-2 pr-4">Status</th>
                  <th className="py-2 pr-4">Rows</th>
                  <th className="py-2 pr-4">Inserted</th>
                  <th className="py-2 pr-4">Updated</th>
                  <th className="py-2 pr-4">Failed</th>
                  <th className="py-2 pr-4">Finished</th>
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
                    <td className="py-3 pr-4 text-muted">{formatDate(run.finished_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState title="No ingestion runs yet" body="Run the sample import command to populate the database and display import counters." />
        )}
      </div>
    </Section>
  );
}

