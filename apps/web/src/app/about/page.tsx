import { PageHeader, Section } from "@/components/ui";

const items = [
  {
    title: "Data source strategy",
    body: "The MVP ships with synthetic but realistic sample procurement records and a CSV ingestion interface. Public CSV, Excel, and API adapters are isolated behind data-source interfaces so real open data can replace the sample source.",
  },
  {
    title: "AI design",
    body: "LLM calls are optional, provider-based, and evidence limited. Gemini and OpenRouter providers sit behind the same interface as the deterministic mock provider, and summaries are cached in the database.",
  },
  {
    title: "Cost control",
    body: "The demo works without private API keys. Embeddings use a local deterministic fallback, summary generation is cached, and deployment targets free-tier Vercel, hosted FastAPI, and Supabase PostgreSQL.",
  },
  {
    title: "Privacy boundary",
    body: "Only public or sample procurement records are designed to be sent to AI providers. No employer, company, or confidential data is required or included.",
  },
];

export default function AboutPage() {
  return (
    <Section>
      <PageHeader
        title="Methodology"
        description="Architecture and operating constraints for a personal portfolio project focused on AI engineering and data engineering."
      />
      <div className="grid gap-4 lg:grid-cols-2">
        {items.map((item) => (
          <section key={item.title} className="rounded-lg border border-border bg-surface p-5">
            <h2 className="text-base font-semibold">{item.title}</h2>
            <p className="mt-2 text-sm leading-6 text-muted">{item.body}</p>
          </section>
        ))}
      </div>
    </Section>
  );
}

