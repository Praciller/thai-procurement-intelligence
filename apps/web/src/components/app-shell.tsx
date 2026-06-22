"use client";

import Link from "next/link";
import { useEffect } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import { BarChart3, Bot, Database, FileSearch, Info, Landmark } from "lucide-react";
import { getDictionary, languages, normalizeLocale, withLocale } from "@/lib/i18n";
import type { DatasetStatus } from "@/types/api";

export function AppShell({ children, dataset }: { children: React.ReactNode; dataset: DatasetStatus }) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const locale = normalizeLocale(searchParams.get("lang"));
  const dictionary = getDictionary(locale);
  const currentQuery = searchParams.toString();
  const currentHref = `${pathname || "/"}${currentQuery ? `?${currentQuery}` : ""}`;
  const navItems = [
    { href: "/", label: dictionary.shell.nav.home, icon: Landmark },
    { href: "/records", label: dictionary.shell.nav.search, icon: FileSearch },
    { href: "/dashboard", label: dictionary.shell.nav.dashboard, icon: BarChart3 },
    { href: "/assistant", label: dictionary.shell.nav.assistant, icon: Bot },
    { href: "/data-status", label: dictionary.shell.nav.dataStatus, icon: Database },
    { href: "/about", label: dictionary.shell.nav.about, icon: Info },
  ];

  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-20 border-b border-border bg-background/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
          <Link href="/" className="flex items-center gap-3 focus-ring rounded-md">
            <span className="flex h-9 w-9 items-center justify-center rounded-md bg-accent text-sm font-semibold text-background">
              TP
            </span>
            <span>
              <span className="block text-sm font-semibold tracking-tight">{dictionary.shell.product}</span>
              <span className="block text-xs text-muted">{dictionary.shell.subtitle}</span>
            </span>
          </Link>
          <div className="flex flex-col gap-2 lg:flex-row lg:items-center">
            <nav className="flex gap-1 overflow-x-auto" aria-label="Primary">
              {navItems.map((item) => {
                const Icon = item.icon;
                const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
                return (
                  <Link
                    key={item.href}
                    href={withLocale(item.href, locale)}
                    className={`focus-ring flex min-h-10 items-center gap-2 rounded-md px-3 text-sm transition ${
                      active ? "bg-surface-strong text-foreground" : "text-muted hover:bg-surface"
                    }`}
                  >
                    <Icon aria-hidden="true" size={16} />
                    {item.label}
                  </Link>
                );
              })}
            </nav>
            <nav className="flex w-max rounded-md border border-border bg-surface p-1" aria-label={dictionary.shell.languageLabel}>
              {languages.map((language) => {
                const active = locale === language.id;
                return (
                <Link
                  key={language.id}
                  href={withLocale(currentHref, language.id)}
                  className={`focus-ring flex min-h-8 min-w-10 items-center justify-center rounded px-2 text-xs font-semibold transition ${
                    active ? "bg-accent text-background" : "text-muted hover:bg-background"
                  }`}
                  lang={language.id}
                >
                  {language.shortLabel}
                </Link>
                );
              })}
            </nav>
          </div>
        </div>
      </header>
      <div className="border-b border-border bg-surface">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-3 gap-y-1 px-4 py-2 text-xs sm:px-6 lg:px-8">
          <span className="font-semibold">
            {dataset.dataset_mode === "official_snapshot"
              ? dictionary.common.officialDataset
              : dictionary.common.syntheticDataset}
          </span>
          <span className="text-muted">
            {dataset.dataset_mode === "official_snapshot"
              ? dictionary.common.officialDatasetNote
              : dictionary.common.syntheticDatasetNote}
          </span>
        </div>
      </div>
      <main>{children}</main>
    </div>
  );
}
