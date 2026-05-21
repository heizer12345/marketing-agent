"use client";

import { useState } from "react";

const EXAMPLES = [
  "Audit our SEO across the top 10 organic pages and recommend fixes",
  "Write a blog post about how to source private-label products from Vietnam",
  "How are our Meta Ads performing this week?",
  "Generate 3 ad variants for our AI Sourcing Agent",
];

export function PromptBar({
  onSubmit,
  disabled,
  showExamples = false,
}: {
  onSubmit: (prompt: string) => void;
  disabled?: boolean;
  showExamples?: boolean;
}) {
  const [val, setVal] = useState("");

  const send = () => {
    if (!val.trim()) return;
    onSubmit(val);
    setVal("");
  };

  return (
    <div className="border-t" style={{ background: "white", borderColor: "var(--border)" }}>
      <div className="max-w-3xl mx-auto px-6 py-4">
        {showExamples && !val && (
          <div className="mb-3 flex flex-wrap gap-1.5">
            <span className="text-[11px] text-muted self-center mr-1">Try:</span>
            {EXAMPLES.map((ex) => (
              <button
                key={ex}
                onClick={() => setVal(ex)}
                className="chip hover:bg-white hover:border-[color:var(--border-strong)] transition-colors"
              >
                {ex.length > 50 ? ex.slice(0, 50) + "…" : ex}
              </button>
            ))}
          </div>
        )}
        <div className="flex items-end gap-2">
          <div className="flex-1 relative">
            <textarea
              value={val}
              onChange={(e) => setVal(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) { e.preventDefault(); send(); }
              }}
              placeholder="Ask anything — agents will dispatch and report back"
              rows={2}
              className="input resize-none font-sans text-[13.5px] leading-snug pr-20"
              style={{ minHeight: 56 }}
            />
            <div className="absolute right-3 bottom-2.5 flex items-center gap-1.5 text-[10px] text-muted">
              <span className="kbd">⌘</span><span className="kbd">↵</span>
            </div>
          </div>
          <button
            className="btn-primary h-[56px] px-5"
            onClick={send}
            disabled={disabled || !val.trim()}
          >
            Send
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
              <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22,2 15,22 11,13 2,9"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
