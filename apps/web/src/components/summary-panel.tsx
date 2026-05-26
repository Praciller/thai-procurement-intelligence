"use client";

import { useState, useTransition } from "react";
import { Sparkles } from "lucide-react";
import { postSummary } from "@/lib/api";

export function SummaryPanel({ recordId, initialSummary }: { recordId: string; initialSummary?: string | null }) {
  const [summary, setSummary] = useState(initialSummary || "");
  const [status, setStatus] = useState(initialSummary ? "Cached summary" : "No summary generated");
  const [isPending, startTransition] = useTransition();

  function generate() {
    startTransition(async () => {
      try {
        setStatus("Generating summary...");
        const result = await postSummary(recordId);
        setSummary(result.summary_text);
        setStatus(result.cached ? "Returned cached summary" : `Generated with ${result.provider}/${result.model}`);
      } catch {
        setStatus("AI summary unavailable. Check ENABLE_LLM or use mock provider for local demo.");
      }
    });
  }

  return (
    <div className="rounded-lg border border-border bg-surface p-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold">AI Summary</h2>
          <p className="mt-1 text-xs text-muted">{status}</p>
        </div>
        <button
          className="focus-ring inline-flex min-h-10 items-center gap-2 rounded-md bg-accent px-3 text-sm font-medium text-background hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isPending}
          onClick={generate}
          type="button"
        >
          <Sparkles size={16} />
          {summary ? "Refresh" : "Generate"}
        </button>
      </div>
      <div className="mt-4 whitespace-pre-line rounded-md bg-background p-4 text-sm leading-6 text-foreground">
        {summary || "Generate a concise evidence-limited summary. If no LLM key is configured, the backend can use the deterministic mock provider for local testing."}
      </div>
    </div>
  );
}

