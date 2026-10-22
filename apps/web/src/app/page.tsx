import { ArrowRight, Database, Search } from "lucide-react";
import { getAnalyticsResult, getDatasetStatus, getRecords, formatMoney } from "@/lib/api";
import { BarList, ButtonLink, DemoNotice, PageHeader, RecordTable, Section, Stat } from "@/components/ui";
import { getDictionary, normalizeLocale, withLocale } from "@/lib/i18n";

export default async function Home({ searchParams }: { searchParams?: Promise<{ lang?: string | string[] }> }) {
  const params = await searchParams;
  const locale = normalizeLocale(params?.lang);
  const dictionary = getDictionary(locale);
  const [analyticsResult, recordsResult, datasetResult] = await Promise.all([
    getAnalyticsResult(),
    getRecords("?page_size=5&sort=budget_desc"),
    getDatasetStatus(),
  ]);
  const analytics = analyticsResult.ok ? analyticsResult.data : null;
  const records = recordsResult.ok ? recordsResult.data : null;
  const dataset = datasetResult.ok ? datasetResult.data : null;
  const tableLabels = { ...dictionary.table, ...dictionary.common };

  return (
    <>
      <Section className="py-10">
        <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
          <div>
            <PageHeader
              title={dictionary.home.title}
              description={dictionary.home.description}
              actions={
                <>
                  <ButtonLink href={withLocale("/records", locale)}>
                    <Search aria-hidden="true" className="mr-2" size={16} />
                    {dictionary.home.searchRecords}
                  </ButtonLink>
                  <ButtonLink href={withLocale("/assistant", locale)} variant="secondary">
                    {dictionary.home.askAssistant}
                    <ArrowRight aria-hidden="true" className="ml-2" size={16} />
                  </ButtonLink>
                </>
              }
            />
            <DemoNotice>
              {!dataset
                ? dictionary.common.notAvailable
                : dataset.dataset_mode === "official_snapshot"
                  ? dictionary.common.officialDatasetNote
                  : dictionary.common.demoNotice}
            </DemoNotice>
          </div>
          <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
            <Stat label={dictionary.home.stats.records} value={analytics ? analytics.total_records.toLocaleString(locale === "th" ? "th-TH" : "en-US") : dictionary.common.notAvailable} note={dictionary.home.stats.afterIngestion} />
            <Stat
              label={dictionary.home.stats.totalBudget}
              value={analytics ? formatMoney(analytics.total_budget, locale) : dictionary.common.notAvailable}
              note={dataset ? dataset.dataset_mode === "official_snapshot" ? dictionary.common.officialDataset : dictionary.home.stats.sampleDataOnly : dictionary.common.notAvailable}
            />
            <Stat label={dictionary.home.stats.averageBudget} value={analytics ? formatMoney(analytics.average_budget, locale) : dictionary.common.notAvailable} note={dictionary.home.stats.normalizedNumericField} />
          </div>
        </div>
      </Section>

      <Section className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="rounded-lg border border-border bg-surface p-5">
          <div className="mb-4 flex items-center gap-2">
            <Database size={18} className="text-accent-strong" />
            <h2 className="text-base font-semibold">{dictionary.home.recordsByProvince}</h2>
          </div>
          {analytics?.records_by_province.length ? (
            <BarList rows={analytics.records_by_province.slice(0, 8)} />
          ) : (
            <p className="py-10 text-sm leading-6 text-muted">{dictionary.home.noProvinceData}</p>
          )}
        </div>
        <div>
          <h2 className="mb-4 text-base font-semibold">{dictionary.home.topProjects}</h2>
          <RecordTable records={records?.items || []} labels={tableLabels} locale={locale} />
        </div>
      </Section>
    </>
  );
}
