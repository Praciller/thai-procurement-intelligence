import { RecordsClient } from "@/components/records-client";
import { DemoNotice, PageHeader, Section } from "@/components/ui";
import { getRecords } from "@/lib/api";

export default async function RecordsPage() {
  const records = await getRecords("?page_size=20");

  return (
    <Section>
      <PageHeader
        title="Procurement Search"
        description="Search sample procurement records by keyword, province, category, budget order, and search mode. Semantic and hybrid modes degrade to deterministic local retrieval when vector infrastructure is not configured."
      />
      <div className="mb-5">
        <DemoNotice />
      </div>
      <RecordsClient initialRecords={records} />
    </Section>
  );
}

