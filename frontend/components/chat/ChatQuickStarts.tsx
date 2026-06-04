"use client";

import type { QuickStartCategory } from "@/lib/chatQuickStarts";
import { CHAT_QUICK_STARTS } from "@/lib/chatQuickStarts";

function CategoryIcon({ kind }: { kind: QuickStartCategory }) {
  const cls = "w-5 h-5";
  if (kind === "seo") {
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={cls}>
        <circle cx="11" cy="11" r="8" />
        <path d="m21 21-4.3-4.3" />
      </svg>
    );
  }
  if (kind === "ads") {
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={cls}>
        <path d="M3 3v18h18" />
        <path d="M7 16l4-8 4 5 5-7" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={cls}>
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" />
    </svg>
  );
}

type Props = {
  onSelectCategory: (id: QuickStartCategory) => void;
};

export function ChatQuickStarts({ onSelectCategory }: Props) {
  return (
    <div className="flex flex-col items-center justify-center py-6 px-4 min-h-[min(420px,50vh)]">
      <h2 className="text-lg font-semibold text-ink text-center" style={{ letterSpacing: "-0.02em" }}>
        What do you want to work on?
      </h2>
      <p className="text-[13px] text-muted text-center mt-2 max-w-md leading-relaxed">
        Pick a topic to load a guided starter in the box below — I&apos;ll ask a few questions before
        pulling data. Or type your own question anytime.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 w-full max-w-3xl mt-8">
        {CHAT_QUICK_STARTS.map((opt) => (
          <button
            key={opt.id}
            type="button"
            onClick={() => onSelectCategory(opt.id)}
            className="card p-5 text-left transition-all hover:shadow-md hover:border-[color:var(--border-strong)] focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500/40 group"
          >
            <div
              className="w-10 h-10 rounded-lg flex items-center justify-center mb-3 text-white"
              style={{ background: "linear-gradient(135deg, #06B6D4 0%, #0891B2 100%)" }}
            >
              <CategoryIcon kind={opt.id} />
            </div>
            <div className="text-sm font-semibold text-ink group-hover:text-cyan-800">{opt.title}</div>
            <p className="text-[12px] text-muted mt-1.5 leading-snug">{opt.description}</p>
            <div className="text-[11px] font-medium text-cyan-700 mt-3 group-hover:underline">
              Use starter prompt →
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
