"use client";

import { useState, useTransition } from "react";
import { Bot, Send } from "lucide-react";
import { askAssistant } from "@/lib/api";
import { getDictionary, normalizeLocale } from "@/lib/i18n";
import type { AssistantResponse } from "@/types/api";
import { EmptyState, RecordTable } from "@/components/ui";

export function AssistantClient({ locale = "en" }: { locale?: string }) {
  const normalizedLocale = normalizeLocale(locale);
  const dictionary = getDictionary(normalizedLocale);
  const text = dictionary.assistantClient;
  const tableLabels = { ...dictionary.table, ...dictionary.common };
  const [question, setQuestion] = useState(text.examples[0]);
  const [result, setResult] = useState<AssistantResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function submit(event: React.FormEvent) {
    event.preventDefault();
    startTransition(async () => {
      setError(null);
      try {
        setResult(await askAssistant(question));
      } catch {
        setError(text.unavailableBody);
      }
    });
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_24rem]">
      <section className="space-y-4">
        <form onSubmit={submit} className="rounded-lg border border-border bg-surface p-4">
          <label className="block text-sm font-medium" htmlFor="question">
            {text.question}
          </label>
          <textarea
            id="question"
            className="mt-2 min-h-28 w-full resize-y rounded-md border border-border bg-background p-3 text-sm leading-6 outline-none focus:border-accent"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
          />
          <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
            <p className="text-xs text-muted">{text.guardrail}</p>
            <button
              className="focus-ring inline-flex min-h-10 items-center gap-2 rounded-md bg-accent px-4 text-sm font-medium text-background hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isPending || !question.trim()}
              type="submit"
            >
              <Send size={16} />
              {isPending ? text.asking : text.ask}
            </button>
          </div>
        </form>

        {error ? <EmptyState title={text.unavailableTitle} body={error} /> : null}
        {result ? (
          <div className="rounded-lg border border-border bg-surface p-5">
            <div className="mb-3 flex items-center gap-2">
              <Bot size={18} className="text-accent-strong" />
              <h2 className="text-base font-semibold">{text.answer}</h2>
            </div>
            {!result.ai_enabled ? <p className="mb-3 text-xs text-warning">{text.disabled}</p> : null}
            <p className="whitespace-pre-line text-sm leading-6">{result.answer}</p>
          </div>
        ) : null}

        {result ? (
          <div>
            <h2 className="mb-3 text-base font-semibold">{text.retrievedEvidence}</h2>
            <RecordTable records={result.retrieved_records} labels={tableLabels} locale={normalizedLocale} />
          </div>
        ) : null}
      </section>

      <aside className="rounded-lg border border-border bg-surface p-4">
        <h2 className="text-base font-semibold">{text.exampleQuestions}</h2>
        <div className="mt-3 space-y-2">
          {text.examples.map((item: string) => (
            <button
              key={item}
              className="focus-ring w-full rounded-md border border-border bg-background p-3 text-left text-sm leading-5 hover:bg-surface-strong"
              onClick={() => setQuestion(item)}
              type="button"
            >
              {item}
            </button>
          ))}
        </div>
      </aside>
    </div>
  );
}
