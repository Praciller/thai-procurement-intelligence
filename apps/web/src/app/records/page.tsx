import { RecordsClient } from "@/components/records-client";
import { DemoNotice, PageHeader, Section } from "@/components/ui";
import { getDatasetStatusResult, getRecordFacetsResult, getRecordsResult } from "@/lib/api";
import { ApiUnavailable } from "@/components/api-unavailable";
import { getDictionary, normalizeLocale } from "@/lib/i18n";

export default async function RecordsPage({ searchParams }: { searchParams?: Promise<{ lang?: string | string[] }> }) {
  const params = await searchParams;
  const locale = normalizeLocale(params?.lang);
  const dictionary = getDictionary(locale);
  const [recordsResult, datasetResult, facetsResult] = await Promise.all([
    getRecordsResult("?page_size=20"),
    getDatasetStatusResult(),
    getRecordFacetsResult(),
  ]);
  if (!recordsResult.ok || !datasetResult.ok || !facetsResult.ok) {
    return <Section><PageHeader title={dictionary.recordsPage.title} description={dictionary.recordsPage.description} /><div className="mt-6"><ApiUnavailable locale={locale} /></div></Section>;
  }
  const records = recordsResult.data;
  const dataset = datasetResult.data;
  const facets = facetsResult.data;

  return (
    <Section>
      <PageHeader
        title={dictionary.recordsPage.title}
        description={dictionary.recordsPage.description}
      />
      <div className="mb-5">
        <DemoNotice>
          {dataset.dataset_mode === "official_snapshot"
            ? dictionary.common.officialDatasetNote
            : dictionary.common.demoNotice}
        </DemoNotice>
      </div>
      <RecordsClient initialRecords={records} facets={facets} locale={locale} />
    </Section>
  );
}
