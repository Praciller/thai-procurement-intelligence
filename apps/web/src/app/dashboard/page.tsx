import { BarList, PageHeader, RecordTable, Section, Stat } from "@/components/ui";
import { formatMoney, getAnalytics } from "@/lib/api";

export default async function DashboardPage() {
  const analytics = await getAnalytics();

  return (
    <Section>
      <PageHeader
        title="Analytics Dashboard"
        description="Overview metrics from normalized procurement records: budget totals, province distribution, categories, agencies, monthly volume, and high-budget projects."
      />
      <div className="grid gap-4 sm:grid-cols-3">
        <Stat label="Total records" value={analytics.total_records.toLocaleString()} />
        <Stat label="Total budget" value={formatMoney(analytics.total_budget)} />
        <Stat label="Average budget" value={formatMoney(analytics.average_budget)} />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border border-border bg-surface p-5">
          <h2 className="mb-4 text-base font-semibold">Province distribution</h2>
          <BarList rows={analytics.records_by_province} />
        </div>
        <div className="rounded-lg border border-border bg-surface p-5">
          <h2 className="mb-4 text-base font-semibold">Category distribution</h2>
          <BarList rows={analytics.records_by_category} />
        </div>
        <div className="rounded-lg border border-border bg-surface p-5">
          <h2 className="mb-4 text-base font-semibold">Monthly volume</h2>
          <BarList rows={analytics.records_by_month.slice(-12)} />
        </div>
        <div className="rounded-lg border border-border bg-surface p-5">
          <h2 className="mb-4 text-base font-semibold">Top agencies</h2>
          <BarList rows={analytics.top_agencies} />
        </div>
      </div>

      <div className="mt-6">
        <h2 className="mb-3 text-base font-semibold">Top budget projects</h2>
        <RecordTable records={analytics.top_projects} />
      </div>
    </Section>
  );
}

