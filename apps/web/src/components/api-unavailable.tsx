import { getDictionary } from "@/lib/i18n";

export function ApiUnavailable({ locale }: { locale: "en" | "th" }) {
  const copy = getDictionary(locale).common;
  return (
    <div role="alert" className="rounded-lg border border-border bg-surface p-5">
      <h2 className="text-base font-semibold">{copy.apiUnavailableTitle}</h2>
      <p className="mt-2 text-sm leading-6 text-muted">{copy.apiUnavailableBody}</p>
    </div>
  );
}
