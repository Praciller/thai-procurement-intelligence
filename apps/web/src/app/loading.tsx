import { Section } from "@/components/ui";

function SkeletonBlock({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-md bg-surface-strong ${className}`} />;
}

export default function Loading() {
  return (
    <main aria-label="Loading page">
      <Section className="py-10">
        <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
          <div className="space-y-4">
            <SkeletonBlock className="h-9 w-full max-w-xl" />
            <SkeletonBlock className="h-5 w-full max-w-2xl" />
            <SkeletonBlock className="h-5 w-4/5 max-w-xl" />
            <div className="flex gap-2 pt-1">
              <SkeletonBlock className="h-10 w-36" />
              <SkeletonBlock className="h-10 w-32" />
            </div>
            <SkeletonBlock className="h-20 w-full max-w-3xl" />
          </div>
          <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
            <SkeletonBlock className="h-28" />
            <SkeletonBlock className="h-28" />
            <SkeletonBlock className="h-28" />
          </div>
        </div>
      </Section>

      <Section className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <SkeletonBlock className="h-48" />
        <div className="space-y-3">
          <SkeletonBlock className="h-6 w-64" />
          <SkeletonBlock className="h-12" />
          <SkeletonBlock className="h-12" />
          <SkeletonBlock className="h-12" />
          <SkeletonBlock className="h-12" />
        </div>
      </Section>
    </main>
  );
}
