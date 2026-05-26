import Link from "next/link";
import { notFound } from "next/navigation";
import { ExternalLink } from "lucide-react";
import { SummaryPanel } from "@/components/summary-panel";
import { PageHeader, RecordTable, Section, Stat } from "@/components/ui";
import { formatDate, formatMoney, getRecord, getSimilar } from "@/lib/api";

export default async function RecordDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [record, similar] = await Promise.all([getRecord(id), getSimilar(id)]);
  if (!record) notFound();

  return (
    <Section>
      <PageHeader
        title={record.project_name}
        description={`${record.agency_name || "Unknown agency"} · ${record.province || "Unknown province"} · ${record.procurement_category || "Uncategorized"}`}
        actions={
          record.source_url ? (
            <Link className="focus-ring inline-flex min-h-10 items-center gap-2 rounded-md border border-border bg-surface px-3 text-sm font-medium hover:bg-surface-strong" href={record.source_url}>
              Source
              <ExternalLink size={16} />
            </Link>
          ) : null
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Budget" value={formatMoney(record.budget_amount)} />
        <Stat label="Winning amount" value={formatMoney(record.winning_amount)} />
        <Stat label="Announcement" value={formatDate(record.announcement_date)} />
        <Stat label="Method" value={record.procurement_method || "Not available"} />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_24rem]">
        <div className="space-y-6">
          <SummaryPanel recordId={record.id} initialSummary={record.ai_summary} />
          <div className="rounded-lg border border-border bg-surface p-5">
            <h2 className="text-base font-semibold">Raw source text</h2>
            <p className="mt-3 whitespace-pre-line text-sm leading-6 text-muted">{record.raw_text || "No raw source text available."}</p>
          </div>
          <div>
            <h2 className="mb-3 text-base font-semibold">Similar records</h2>
            <RecordTable records={similar} />
          </div>
        </div>
        <aside className="rounded-lg border border-border bg-surface p-5">
          <h2 className="text-base font-semibold">Normalized fields</h2>
          <dl className="mt-4 space-y-3 text-sm">
            {[
              ["Record ID", record.source_record_id || record.id],
              ["Agency", record.agency_name],
              ["Province", record.province],
              ["Category", record.procurement_category],
              ["Winner", record.winner_name],
              ["Contract date", formatDate(record.contract_date)],
              ["Imported", formatDate(record.imported_at)],
              ["Updated", formatDate(record.updated_at)],
            ].map(([label, value]) => (
              <div key={label}>
                <dt className="text-xs uppercase tracking-wide text-muted">{label}</dt>
                <dd className="mt-1 break-words font-medium">{value || "Not available"}</dd>
              </div>
            ))}
          </dl>
        </aside>
      </div>
    </Section>
  );
}

