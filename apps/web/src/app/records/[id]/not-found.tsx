import { EmptyState, Section } from "@/components/ui";
import { getDictionary } from "@/lib/i18n";

export default function RecordNotFound() {
  const dictionary = getDictionary("en");

  return (
    <Section>
      <EmptyState title={dictionary.detail.notFoundTitle} body={dictionary.detail.notFoundBody} />
    </Section>
  );
}
