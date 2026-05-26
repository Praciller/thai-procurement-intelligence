"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, Bot, Database, FileSearch, Info, Landmark } from "lucide-react";

const navItems = [
  { href: "/", label: "Home", icon: Landmark },
  { href: "/records", label: "Search", icon: FileSearch },
  { href: "/dashboard", label: "Dashboard", icon: BarChart3 },
  { href: "/assistant", label: "Assistant", icon: Bot },
  { href: "/data-status", label: "Data Status", icon: Database },
  { href: "/about", label: "About", icon: Info },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-20 border-b border-border bg-background/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
          <Link href="/" className="flex items-center gap-3 focus-ring rounded-md">
            <span className="flex h-9 w-9 items-center justify-center rounded-md bg-accent text-sm font-semibold text-background">
              TP
            </span>
            <span>
              <span className="block text-sm font-semibold tracking-tight">Thai Procurement Intelligence</span>
              <span className="block text-xs text-muted">Sample public-data AI platform</span>
            </span>
          </Link>
          <nav className="flex gap-1 overflow-x-auto" aria-label="Primary">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
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
        </div>
      </header>
      <main>{children}</main>
    </div>
  );
}

