import { AssistantClient } from "@/components/assistant-client";
import { DemoNotice, PageHeader, Section } from "@/components/ui";

export default function AssistantPage() {
  return (
    <Section>
      <PageHeader
        title="AI Assistant"
        description="Ask natural-language questions. The backend retrieves procurement records first, then uses the configured LLM provider only when enabled."
      />
      <div className="mb-5">
        <DemoNotice />
      </div>
      <AssistantClient />
    </Section>
  );
}

