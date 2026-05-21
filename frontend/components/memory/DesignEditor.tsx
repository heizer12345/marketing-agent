"use client";

import { useState } from "react";
import { api } from "@/lib/api";

export function DesignEditor({
  design,
  onSaved,
}: {
  design: Record<string, any>;
  onSaved: () => void;
}) {
  const [draft, setDraft] = useState<string>(() => JSON.stringify(design, null, 2));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  let parsed: any = {};
  try { parsed = JSON.parse(draft); } catch { /* draft invalid */ }

  const updateNested = (path: string[], value: any) => {
    try {
      const obj = JSON.parse(draft);
      let cur = obj;
      for (let i = 0; i < path.length - 1; i++) {
        if (typeof cur[path[i]] !== "object" || cur[path[i]] === null) cur[path[i]] = {};
        cur = cur[path[i]];
      }
      cur[path[path.length - 1]] = value;
      setDraft(JSON.stringify(obj, null, 2));
      setError(null);
    } catch {
      setError("JSON invalid — fix the raw view first.");
    }
  };

  const save = async () => {
    setSaving(true); setError(null);
    try {
      const obj = JSON.parse(draft);
      await api.saveDesignSystem(obj);
      onSaved();
    } catch (e: any) {
      setError(e?.message || "Save failed");
    } finally { setSaving(false); }
  };

  const colors = parsed.colors || {};
  const imageStyle = parsed.image_style || {};
  const fonts = parsed.fonts || {};

  return (
    <div className="space-y-6">
      <section>
        <div className="label mb-3">Brand colors</div>
        <div className="grid grid-cols-2 gap-4">
          <ColorField label="Primary" value={colors.primary || "#0F172A"} onChange={(v) => updateNested(["colors", "primary"], v)} />
          <ColorField label="Accent" value={colors.accent || "#22D3EE"} onChange={(v) => updateNested(["colors", "accent"], v)} />
        </div>
      </section>

      <section>
        <div className="label mb-3">Fonts</div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-muted">Heading</label>
            <input className="input" value={fonts.heading || ""} onChange={(e) => updateNested(["fonts", "heading"], e.target.value)} />
          </div>
          <div>
            <label className="text-xs text-muted">Body</label>
            <input className="input" value={fonts.body || ""} onChange={(e) => updateNested(["fonts", "body"], e.target.value)} />
          </div>
        </div>
      </section>

      <section>
        <div className="label mb-1">Image style by job</div>
        <p className="text-xs text-muted mb-3">
          These descriptors are injected into every GPT Image 2 prompt. The more specific, the more on-brand the output.
        </p>
        <div className="space-y-3">
          {(["ad_style", "blog_image_style", "case_study_style", "lp_hero_style", "infographic_style"] as const).map((k) => (
            <div key={k}>
              <label className="text-xs font-medium text-ink">{k.replace(/_/g, " ")}</label>
              <textarea
                className="textarea mt-1"
                rows={2}
                value={imageStyle[k] || ""}
                onChange={(e) => updateNested(["image_style", k], e.target.value)}
              />
            </div>
          ))}
          <div>
            <label className="text-xs font-medium text-ink">Banned visuals</label>
            <textarea
              className="textarea mt-1"
              rows={3}
              value={(imageStyle.banned_visuals || []).join(", ")}
              onChange={(e) =>
                updateNested(["image_style", "banned_visuals"], e.target.value.split(",").map((s) => s.trim()).filter(Boolean))
              }
            />
          </div>
        </div>
      </section>

      <details className="card p-4">
        <summary className="cursor-pointer text-sm font-medium text-ink">Raw JSON (advanced)</summary>
        <textarea className="textarea mt-3" rows={20} value={draft} onChange={(e) => setDraft(e.target.value)} />
      </details>

      {error && <div className="text-sm text-red-600">{error}</div>}

      <div className="flex items-center justify-between pt-2">
        <p className="text-xs text-muted">Saving rebuilds the design system block used by image_gen and content writers.</p>
        <button className="btn-primary" disabled={saving} onClick={save}>
          {saving ? "Saving…" : "Save design system"}
        </button>
      </div>
    </div>
  );
}

function ColorField({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div>
      <label className="text-xs text-muted">{label}</label>
      <div className="mt-1 flex items-center gap-2">
        <input type="color" value={value} onChange={(e) => onChange(e.target.value)} className="w-12 h-9 rounded border border-border bg-white p-1" />
        <input className="input flex-1 font-mono text-xs" value={value} onChange={(e) => onChange(e.target.value)} />
      </div>
    </div>
  );
}
