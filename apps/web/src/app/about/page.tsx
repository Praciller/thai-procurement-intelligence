import { PageHeader, Section } from "@/components/ui";
import { getDictionary, normalizeLocale } from "@/lib/i18n";

export default async function AboutPage({ searchParams }: { searchParams?: Promise<{ lang?: string | string[] }> }) {
  const params = await searchParams;
  const locale = normalizeLocale(params?.lang);
  const dictionary = getDictionary(locale);

  return (
    <Section>
      <PageHeader
        title={dictionary.about.title}
        description={dictionary.about.description}
      />
      <div className="grid gap-4 lg:grid-cols-2">
        {dictionary.about.items.map((item: { title: string; body: string }) => (
          <section key={item.title} className="rounded-lg border border-border bg-surface p-5">
            <h2 className="text-base font-semibold">{item.title}</h2>
            <p className="mt-2 text-sm leading-6 text-muted">{item.body}</p>
          </section>
        ))}
      </div>
    </Section>
  );
}
