"use client";

import { useState } from "react";
import { api } from "@/lib/api";

export function PersonaEditor({
  persona,
  onSaved,
}: {
  persona: Record<string, any>;
  onSaved: () => void;
}) {
  const [draft, setDraft] = useState<string>(() => JSON.stringify(persona, null, 2));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = (k: string, v: any) => {
    try {
      const obj = JSON.parse(draft);
      obj[k] = v;
      setDraft(JSON.stringify(obj, null, 2));
      setError(null);
    } catch {
      setError("JSON is invalid — fix the raw view first.");
    }
  };

  const save = async () => {
    setSaving(true); setError(null);
    try {
      const obj = JSON.parse(draft);
      await api.savePersona(obj);
      onSaved();
    } catch (e: any) {
      setError(e?.message || "Save failed");
    } finally {
      setSaving(false);
    }
  };

  let parsed: any = {};
  try { parsed = JSON.parse(draft); } catch { /* draft has errors */ }

  return (
    <div className="space-y-6">
      <Section title="One-liner" hint="The single sentence that captures Sourcy.">
        <input
          className="input"
          value={parsed.one_liner ?? ""}
          onChange={(e) => set("one_liner", e.target.value)}
        />
      </Section>

      <Section title="Elevator pitch" hint="One short paragraph. Used in generation contexts that need a fuller positioning.">
        <textarea
          className="textarea"
          rows={3}
          value={parsed.elevator_pitch ?? ""}
          onChange={(e) => set("elevator_pitch", e.target.value)}
        />
      </Section>

      <Section title="Positioning vs competitors" hint="The single most differentiating sentence. Goes into most generated copy.">
        <textarea
          className="textarea"
          rows={3}
          value={parsed.positioning_vs_competitors ?? ""}
          onChange={(e) => set("positioning_vs_competitors", e.target.value)}
        />
      </Section>

      <Section title="Banned phrases" hint="Comma-separated. Every generation skill grep-checks against this.">
        <textarea
          className="textarea"
          rows={3}
          value={(parsed.banned_phrases || []).join(", ")}
          onChange={(e) => set("banned_phrases", e.target.value.split(",").map((s: string) => s.trim()).filter(Boolean))}
        />
      </Section>

      <Section title="Preferred lexicon" hint="Terms generation skills should prefer when on-topic.">
        <textarea
          className="textarea"
          rows={2}
          value={((parsed.lexicon && parsed.lexicon.preferred) || []).join(", ")}
          onChange={(e) => {
            const obj = JSON.parse(draft);
            obj.lexicon = { ...(obj.lexicon || {}), preferred: e.target.value.split(",").map((s: string) => s.trim()).filter(Boolean) };
            setDraft(JSON.stringify(obj, null, 2));
          }}
        />
      </Section>

      <details className="card p-4">
        <summary className="cursor-pointer text-sm font-medium text-ink">Raw JSON (advanced)</summary>
        <textarea
          className="textarea mt-3"
          rows={20}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
        />
      </details>

      {error && <div className="text-sm text-red-600">{error}</div>}

      <div className="flex items-center justify-between pt-2">
        <p className="text-xs text-muted">Saving reloads the persona block injected into every generation skill.</p>
        <button className="btn-primary" disabled={saving} onClick={save}>
          {saving ? "Saving…" : "Save persona"}
        </button>
      </div>
    </div>
  );
}

function Section({ title, hint, children }: { title: string; hint?: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="label mb-1">{title}</div>
      {hint && <div className="text-xs text-muted mb-2">{hint}</div>}
      {children}
    </div>
  );
}
