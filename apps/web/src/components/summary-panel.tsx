"use client";

import { useState, useTransition } from "react";
import { Sparkles } from "lucide-react";
import { postSummary } from "@/lib/api";
import { getDictionary, normalizeLocale } from "@/lib/i18n";

export function SummaryPanel({ recordId, initialSummary, locale = "en" }: { recordId: string; initialSummary?: string | null; locale?: string }) {
  const normalizedLocale = normalizeLocale(locale);
  const text = getDictionary(normalizedLocale).summary;
  const [summary, setSummary] = useState(initialSummary || "");
  const [status, setStatus] = useState(initialSummary ? text.cachedSummary : text.noSummary);
  const [isPending, startTransition] = useTransition();

  function generate() {
    startTransition(async () => {
      try {
        setStatus(text.generating);
        const result = await postSummary(recordId);
        setSummary(result.summary_text);
        setStatus(result.cached ? text.returnedCached : `${text.generatedWith} ${result.provider}/${result.model}`);
      } catch {
        setStatus(text.unavailable);
      }
    });
  }

  return (
    <div className="rounded-lg border border-border bg-surface p-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold">{text.title}</h2>
          <p className="mt-1 text-xs text-muted">{status}</p>
        </div>
        <button
          className="focus-ring inline-flex min-h-10 items-center gap-2 rounded-md bg-accent px-3 text-sm font-medium text-background hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isPending}
          onClick={generate}
          type="button"
        >
          <Sparkles size={16} />
          {summary ? text.refresh : text.generate}
        </button>
      </div>
      <div className="mt-4 whitespace-pre-line rounded-md bg-background p-4 text-sm leading-6 text-foreground">
        {summary || text.placeholder}
      </div>
    </div>
  );
}
