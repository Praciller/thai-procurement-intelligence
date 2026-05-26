"use client";

import { useState, useTransition } from "react";
import { Bot, Send } from "lucide-react";
import { askAssistant } from "@/lib/api";
import type { AssistantResponse } from "@/types/api";
import { EmptyState, RecordTable } from "@/components/ui";

const exampleQuestions = [
  "What are the highest-budget IT procurement projects?",
  "Which agencies have many construction projects?",
  "Summarize procurement records in Bangkok.",
];

export function AssistantClient() {
  const [question, setQuestion] = useState(exampleQuestions[0]);
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
        setError("Assistant request failed. Confirm API is running and sample data has been ingested.");
      }
    });
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_24rem]">
      <section className="space-y-4">
        <form onSubmit={submit} className="rounded-lg border border-border bg-surface p-4">
          <label className="block text-sm font-medium" htmlFor="question">
            Question
          </label>
          <textarea
            id="question"
            className="mt-2 min-h-28 w-full resize-y rounded-md border border-border bg-background p-3 text-sm leading-6 outline-none focus:border-accent"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
          />
          <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
            <p className="text-xs text-muted">Answers are constrained to retrieved procurement records and citations.</p>
            <button
              className="focus-ring inline-flex min-h-10 items-center gap-2 rounded-md bg-accent px-4 text-sm font-medium text-background hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isPending || !question.trim()}
              type="submit"
            >
              <Send size={16} />
              {isPending ? "Asking..." : "Ask"}
            </button>
          </div>
        </form>

        {error ? <EmptyState title="Assistant unavailable" body={error} /> : null}
        {result ? (
          <div className="rounded-lg border border-border bg-surface p-5">
            <div className="mb-3 flex items-center gap-2">
              <Bot size={18} className="text-accent-strong" />
              <h2 className="text-base font-semibold">Answer</h2>
            </div>
            {!result.ai_enabled ? <p className="mb-3 text-xs text-warning">LLM generation is disabled; retrieved evidence is still shown.</p> : null}
            <p className="whitespace-pre-line text-sm leading-6">{result.answer}</p>
          </div>
        ) : null}

        {result ? (
          <div>
            <h2 className="mb-3 text-base font-semibold">Retrieved evidence</h2>
            <RecordTable records={result.retrieved_records} />
          </div>
        ) : null}
      </section>

      <aside className="rounded-lg border border-border bg-surface p-4">
        <h2 className="text-base font-semibold">Example questions</h2>
        <div className="mt-3 space-y-2">
          {exampleQuestions.map((item) => (
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

