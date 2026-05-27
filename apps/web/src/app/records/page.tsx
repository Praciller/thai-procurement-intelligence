import { RecordsClient } from "@/components/records-client";
import { DemoNotice, PageHeader, Section } from "@/components/ui";
import { getRecords } from "@/lib/api";
import { getDictionary, normalizeLocale } from "@/lib/i18n";

export default async function RecordsPage({ searchParams }: { searchParams?: Promise<{ lang?: string | string[] }> }) {
  const params = await searchParams;
  const locale = normalizeLocale(params?.lang);
  const dictionary = getDictionary(locale);
  const records = await getRecords("?page_size=20");

  return (
    <Section>
      <PageHeader
        title={dictionary.recordsPage.title}
        description={dictionary.recordsPage.description}
      />
      <div className="mb-5">
        <DemoNotice>{dictionary.common.demoNotice}</DemoNotice>
      </div>
      <RecordsClient initialRecords={records} locale={locale} />
    </Section>
  );
}
