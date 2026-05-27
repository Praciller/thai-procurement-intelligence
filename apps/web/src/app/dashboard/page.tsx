import { BarList, PageHeader, RecordTable, Section, Stat } from "@/components/ui";
import { formatMoney, getAnalytics } from "@/lib/api";
import { getDictionary, normalizeLocale } from "@/lib/i18n";

export default async function DashboardPage({ searchParams }: { searchParams?: Promise<{ lang?: string | string[] }> }) {
  const params = await searchParams;
  const locale = normalizeLocale(params?.lang);
  const dictionary = getDictionary(locale);
  const tableLabels = { ...dictionary.table, ...dictionary.common };
  const analytics = await getAnalytics();

  return (
    <Section>
      <PageHeader
        title={dictionary.dashboard.title}
        description={dictionary.dashboard.description}
      />
      <div className="grid gap-4 sm:grid-cols-3">
        <Stat label={dictionary.dashboard.totalRecords} value={analytics.total_records.toLocaleString(locale === "th" ? "th-TH" : "en-US")} />
        <Stat label={dictionary.dashboard.totalBudget} value={formatMoney(analytics.total_budget, locale)} />
        <Stat label={dictionary.dashboard.averageBudget} value={formatMoney(analytics.average_budget, locale)} />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border border-border bg-surface p-5">
          <h2 className="mb-4 text-base font-semibold">{dictionary.dashboard.provinceDistribution}</h2>
          <BarList rows={analytics.records_by_province} />
        </div>
        <div className="rounded-lg border border-border bg-surface p-5">
          <h2 className="mb-4 text-base font-semibold">{dictionary.dashboard.categoryDistribution}</h2>
          <BarList rows={analytics.records_by_category} />
        </div>
        <div className="rounded-lg border border-border bg-surface p-5">
          <h2 className="mb-4 text-base font-semibold">{dictionary.dashboard.monthlyVolume}</h2>
          <BarList rows={analytics.records_by_month.slice(-12)} />
        </div>
        <div className="rounded-lg border border-border bg-surface p-5">
          <h2 className="mb-4 text-base font-semibold">{dictionary.dashboard.topAgencies}</h2>
          <BarList rows={analytics.top_agencies} />
        </div>
      </div>

      <div className="mt-6">
        <h2 className="mb-3 text-base font-semibold">{dictionary.dashboard.topBudgetProjects}</h2>
        <RecordTable records={analytics.top_projects} labels={tableLabels} locale={locale} />
      </div>
    </Section>
  );
}
