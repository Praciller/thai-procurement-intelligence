import Link from "next/link";
import { notFound } from "next/navigation";
import { ExternalLink } from "lucide-react";
import { SummaryPanel } from "@/components/summary-panel";
import { PageHeader, RecordTable, Section, Stat } from "@/components/ui";
import { formatDate, formatMoney, getRecord, getSimilar } from "@/lib/api";
import { getDictionary, normalizeLocale } from "@/lib/i18n";

export default async function RecordDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams?: Promise<{ lang?: string | string[] }>;
}) {
  const { id } = await params;
  const query = await searchParams;
  const locale = normalizeLocale(query?.lang);
  const dictionary = getDictionary(locale);
  const tableLabels = { ...dictionary.table, ...dictionary.common };
  const [record, similar] = await Promise.all([getRecord(id), getSimilar(id)]);
  if (!record) notFound();

  return (
    <Section>
      <PageHeader
        title={record.project_name}
        description={`${record.agency_name || dictionary.common.unknownAgency} · ${record.province || dictionary.common.unknownProvince} · ${record.procurement_category || dictionary.common.uncategorized}`}
        actions={
          record.source_url ? (
            <Link className="focus-ring inline-flex min-h-10 items-center gap-2 rounded-md border border-border bg-surface px-3 text-sm font-medium hover:bg-surface-strong" href={record.source_url}>
              {dictionary.common.source}
              <ExternalLink size={16} />
            </Link>
          ) : null
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label={dictionary.detail.budget} value={formatMoney(record.budget_amount, locale)} />
        <Stat label={dictionary.detail.winningAmount} value={formatMoney(record.winning_amount, locale)} />
        <Stat label={dictionary.detail.announcement} value={formatDate(record.announcement_date, locale)} />
        <Stat label={dictionary.detail.method} value={record.procurement_method || dictionary.common.notAvailable} />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_24rem]">
        <div className="space-y-6">
          <SummaryPanel recordId={record.id} initialSummary={record.ai_summary} locale={locale} />
          <div className="rounded-lg border border-border bg-surface p-5">
            <h2 className="text-base font-semibold">{dictionary.detail.rawSourceText}</h2>
            <p className="mt-3 whitespace-pre-line text-sm leading-6 text-muted">{record.raw_text || dictionary.detail.noRawSourceText}</p>
          </div>
          <div>
            <h2 className="mb-3 text-base font-semibold">{dictionary.detail.similarRecords}</h2>
            <RecordTable records={similar} labels={tableLabels} locale={locale} />
          </div>
        </div>
        <aside className="rounded-lg border border-border bg-surface p-5">
          <div className="mb-5 rounded-md border border-border bg-background p-3 text-sm">
            <div className="font-semibold">
              {record.is_synthetic ? dictionary.common.syntheticDataset : dictionary.common.officialDataset}
            </div>
            <div className="mt-1 text-xs text-muted">
              {record.is_synthetic ? dictionary.common.syntheticDatasetNote : dictionary.common.officialDatasetNote}
            </div>
          </div>
          <h2 className="text-base font-semibold">{dictionary.detail.normalizedFields}</h2>
          <dl className="mt-4 space-y-3 text-sm">
            {[
              [dictionary.detail.recordId, record.source_record_id || record.id],
              [dictionary.detail.agency, record.agency_name],
              [dictionary.detail.province, record.province],
              [dictionary.detail.category, record.procurement_category],
              [dictionary.detail.winner, record.winner_name],
              [dictionary.detail.contractDate, formatDate(record.contract_date, locale)],
              [dictionary.detail.imported, formatDate(record.imported_at, locale)],
              [dictionary.detail.updated, formatDate(record.updated_at, locale)],
              [dictionary.detail.sourceName, record.source_name],
              [dictionary.detail.sourceRecordId, record.source_record_id],
              [dictionary.detail.snapshotId, record.source_snapshot_id],
              [dictionary.detail.retrieved, formatDate(record.source_retrieved_at, locale)],
              [dictionary.detail.published, formatDate(record.source_published_at, locale)],
              [dictionary.detail.license, record.source_license],
              [dictionary.detail.mappingVersion, record.mapping_version],
            ].map(([label, value]) => (
              <div key={label}>
                <dt className="text-xs uppercase tracking-wide text-muted">{label}</dt>
                <dd className="mt-1 break-words font-medium">{value || dictionary.common.notAvailable}</dd>
              </div>
            ))}
          </dl>
        </aside>
      </div>
    </Section>
  );
}
