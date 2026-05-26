import { ArrowRight, Database, Search } from "lucide-react";
import { getAnalytics, getRecords, formatMoney } from "@/lib/api";
import { BarList, ButtonLink, DemoNotice, PageHeader, RecordTable, Section, Stat } from "@/components/ui";

export default async function Home() {
  const [analytics, records] = await Promise.all([getAnalytics(), getRecords("?page_size=5&sort=budget_desc")]);

  return (
    <>
      <Section className="py-10">
        <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
          <div>
            <PageHeader
              title="AI-powered search for Thai public procurement data"
              description="A portfolio-grade data product that ingests public or sample procurement records, normalizes them, supports search and analytics, and answers questions with cited evidence."
              actions={
                <>
                  <ButtonLink href="/records">
                    <Search aria-hidden="true" className="mr-2" size={16} />
                    Search records
                  </ButtonLink>
                  <ButtonLink href="/assistant" variant="secondary">
                    Ask assistant
                    <ArrowRight aria-hidden="true" className="ml-2" size={16} />
                  </ButtonLink>
                </>
              }
            />
            <DemoNotice />
          </div>
          <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
            <Stat label="Records" value={analytics.total_records.toLocaleString()} note="After ingestion" />
            <Stat label="Total budget" value={formatMoney(analytics.total_budget)} note="Sample data only" />
            <Stat label="Average budget" value={formatMoney(analytics.average_budget)} note="Normalized numeric field" />
          </div>
        </div>
      </Section>

      <Section className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="rounded-lg border border-border bg-surface p-5">
          <div className="mb-4 flex items-center gap-2">
            <Database size={18} className="text-accent-strong" />
            <h2 className="text-base font-semibold">Records by province</h2>
          </div>
          <BarList rows={analytics.records_by_province.slice(0, 8)} />
        </div>
        <div>
          <h2 className="mb-4 text-base font-semibold">Highest budget sample projects</h2>
          <RecordTable records={records.items} />
        </div>
      </Section>
    </>
  );
}

