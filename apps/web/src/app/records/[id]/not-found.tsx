import { EmptyState, Section } from "@/components/ui";

export default function RecordNotFound() {
  return (
    <Section>
      <EmptyState title="Record not found" body="The API did not return this procurement record. It may not be ingested yet." />
    </Section>
  );
}

