import { AssistantClient } from "@/components/assistant-client";
import { DemoNotice, PageHeader, Section } from "@/components/ui";
import { getDatasetStatus } from "@/lib/api";
import { getDictionary, normalizeLocale } from "@/lib/i18n";

export default async function AssistantPage({ searchParams }: { searchParams?: Promise<{ lang?: string | string[] }> }) {
  const params = await searchParams;
  const locale = normalizeLocale(params?.lang);
  const dictionary = getDictionary(locale);
  const dataset = await getDatasetStatus();

  return (
    <Section>
      <PageHeader
        title={dictionary.assistantPage.title}
        description={dictionary.assistantPage.description}
      />
      <div className="mb-5">
        <DemoNotice>
          {dataset.dataset_mode === "official_snapshot"
            ? dictionary.common.officialDatasetNote
            : dictionary.common.demoNotice}
        </DemoNotice>
      </div>
      <AssistantClient key={locale} locale={locale} />
    </Section>
  );
}
