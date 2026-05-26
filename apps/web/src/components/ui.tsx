import Link from "next/link";
import type { ProcurementRecord } from "@/types/api";
import { formatDate, formatMoney } from "@/lib/api";

export function Section({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <section className={`mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8 ${className}`}>{children}</section>;
}

export function PageHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description: string;
  actions?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-4 pb-6 lg:flex-row lg:items-end lg:justify-between">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight text-foreground">{title}</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">{description}</p>
      </div>
      {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
    </div>
  );
}

export function ButtonLink({ href, children, variant = "primary" }: { href: string; children: React.ReactNode; variant?: "primary" | "secondary" }) {
  return (
    <Link
      href={href}
      className={`focus-ring inline-flex min-h-10 items-center justify-center rounded-md px-4 text-sm font-medium transition ${
        variant === "primary"
          ? "bg-accent text-background hover:bg-accent-strong"
          : "border border-border bg-surface text-foreground hover:bg-surface-strong"
      }`}
    >
      {children}
    </Link>
  );
}

export function Stat({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <div className="text-xs font-medium uppercase tracking-wide text-muted">{label}</div>
      <div className="mt-2 text-2xl font-semibold tracking-tight">{value}</div>
      {note ? <div className="mt-1 text-xs text-muted">{note}</div> : null}
    </div>
  );
}

export function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-lg border border-dashed border-border bg-surface p-8 text-center">
      <h2 className="text-base font-semibold">{title}</h2>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-muted">{body}</p>
    </div>
  );
}

export function DemoNotice() {
  return (
    <div className="rounded-lg border border-warning/40 bg-warning/10 p-4 text-sm leading-6">
      This demo uses synthetic sample records with obvious sample agency and vendor names. It does not claim facts about real agencies.
    </div>
  );
}

export function BarList({ rows }: { rows: Array<{ label: string; count: number; total_budget?: string | number | null }> }) {
  const max = Math.max(1, ...rows.map((row) => row.count));
  return (
    <div className="space-y-3">
      {rows.map((row) => (
        <div key={row.label} className="grid grid-cols-[minmax(7rem,1fr)_3fr_auto] items-center gap-3 text-sm">
          <div className="truncate text-muted">{row.label}</div>
          <div className="h-2 rounded-full bg-surface-strong">
            <div className="h-2 rounded-full bg-accent" style={{ width: `${Math.max(6, (row.count / max) * 100)}%` }} />
          </div>
          <div className="font-mono text-xs">{row.count}</div>
        </div>
      ))}
    </div>
  );
}

export function RecordTable({ records }: { records: ProcurementRecord[] }) {
  if (!records.length) {
    return <EmptyState title="No records found" body="Run sample ingestion or adjust the search filters." />;
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-border bg-surface">
      <table className="min-w-full border-collapse text-left text-sm">
        <thead className="bg-surface-strong text-xs uppercase tracking-wide text-muted">
          <tr>
            <th className="px-4 py-3">Project</th>
            <th className="px-4 py-3">Agency</th>
            <th className="px-4 py-3">Province</th>
            <th className="px-4 py-3">Budget</th>
            <th className="px-4 py-3">Date</th>
          </tr>
        </thead>
        <tbody>
          {records.map((record) => (
            <tr key={record.id} className="border-t border-border align-top hover:bg-background">
              <td className="px-4 py-3">
                <Link href={`/records/${record.id}`} className="focus-ring rounded-sm font-medium text-accent-strong hover:underline">
                  {record.project_name}
                </Link>
                <div className="mt-1 text-xs text-muted">{record.procurement_category || "Uncategorized"}</div>
              </td>
              <td className="px-4 py-3 text-muted">{record.agency_name || "Not available"}</td>
              <td className="px-4 py-3">{record.province || "Not available"}</td>
              <td className="px-4 py-3 font-mono text-xs">{formatMoney(record.budget_amount)}</td>
              <td className="px-4 py-3 text-muted">{formatDate(record.announcement_date)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

