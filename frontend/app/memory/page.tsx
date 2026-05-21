"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { MemoryState } from "@/lib/types";
import { PersonaEditor } from "@/components/memory/PersonaEditor";
import { DesignEditor } from "@/components/memory/DesignEditor";
import { LogoUploader } from "@/components/memory/LogoUploader";
import { KnowledgePanel } from "@/components/memory/KnowledgePanel";
import { ApiStatus } from "@/components/memory/ApiStatus";

type Section = "persona" | "design" | "logo" | "knowledge" | "api";

export default function MemoryPage() {
  const [state, setState] = useState<MemoryState | null>(null);
  const [section, setSection] = useState<Section>("persona");
  const [savedAt, setSavedAt] = useState<number | null>(null);

  useEffect(() => {
    api.memoryState().then(setState).catch(() => {});
  }, []);

  const reload = () => api.memoryState().then(setState);

  if (!state) return <div className="p-8 text-muted">Loading memory…</div>;

  const SECTIONS: Array<[Section, string, string, string]> = [
    ["persona",   "Persona",        "🗣️", "Voice, tone, ICP, banned phrases"],
    ["design",    "Design system",  "🎨", "Colors, fonts, image style by job"],
    ["logo",      "Logo + assets",  "🖼️", "Uploaded refs passed to GPT Image 2"],
    ["knowledge", "Knowledge",      "📚", "Principle library + winners"],
    ["api",       "Connected APIs", "🔌", "GA4, Meta Ads, SEMrush, etc."],
  ];

  return (
    <div className="flex h-full overflow-hidden">
      <nav className="w-60 shrink-0 border-r p-3 space-y-1 text-sm thin-scroll overflow-y-auto" style={{ background: "var(--bg-rail)", borderColor: "var(--border)" }}>
        <div className="px-2 mb-2 mt-1">
          <div className="label">Brand brain</div>
          <p className="text-[11px] text-muted mt-1 leading-snug">Every generation skill reads from here. Edit once — applies everywhere.</p>
        </div>
        {SECTIONS.map(([k, label, emoji, desc]) => (
          <button
            key={k}
            onClick={() => setSection(k)}
            className={
              "flex items-start gap-2.5 w-full text-left rounded-lg px-3 py-2.5 transition-all duration-150 " +
              (section === k ? "bg-ink text-white shadow-sm" : "text-ink hover:bg-white")
            }
          >
            <span className="text-base shrink-0">{emoji}</span>
            <div className="min-w-0">
              <div className="leading-tight font-medium">{label}</div>
              <div className={"text-[10.5px] leading-tight mt-0.5 truncate " + (section === k ? "opacity-80" : "text-muted")}>{desc}</div>
            </div>
          </button>
        ))}
      </nav>
      <div className="flex-1 overflow-y-auto thin-scroll">
        <header className="border-b bg-white px-8 py-5 flex items-center justify-between sticky top-0 z-10" style={{ borderColor: "var(--border)" }}>
          <div>
            <h1 className="text-xl font-semibold text-ink" style={{ letterSpacing: "-0.02em" }}>Memory</h1>
            <p className="text-[13px] text-muted mt-0.5">Sourcy's brand brain. Every generation skill — blogs, ads, LPs, case studies — reads from here.</p>
          </div>
          {savedAt && <div className="chip chip-emerald text-[10.5px]">Saved · {new Date(savedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</div>}
        </header>
        <div className="p-8 max-w-4xl">
          {section === "persona" && <PersonaEditor persona={state.persona} onSaved={() => { setSavedAt(Date.now()); reload(); }} />}
          {section === "design" && <DesignEditor design={state.design_system} onSaved={() => { setSavedAt(Date.now()); reload(); }} />}
          {section === "logo" && <LogoUploader design={state.design_system} onSaved={() => { setSavedAt(Date.now()); reload(); }} />}
          {section === "knowledge" && <KnowledgePanel principles={state.principles} winners={state.winners} />}
          {section === "api" && <ApiStatus status={state.api_status} />}
        </div>
      </div>
    </div>
  );
}
