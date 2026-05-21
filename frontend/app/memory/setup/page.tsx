"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { MemoryState } from "@/lib/types";

type Step = 1 | 2 | 3 | 4;

export default function SetupWizard() {
  const router = useRouter();
  const [step, setStep] = useState<Step>(1);
  const [state, setState] = useState<MemoryState | null>(null);
  const [persona, setPersona] = useState<Record<string, any>>({});
  const [design, setDesign] = useState<Record<string, any>>({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.memoryState().then((s) => {
      setState(s);
      setPersona(s.persona || {});
      setDesign(s.design_system || {});
    });
  }, []);

  if (!state) return <div className="p-8 text-muted">Loading setup…</div>;

  const next = () => setStep((s) => Math.min(4, (s + 1)) as Step);
  const back = () => setStep((s) => Math.max(1, (s - 1)) as Step);

  const savePersona = async () => {
    setSaving(true);
    try { await api.savePersona(persona); next(); } finally { setSaving(false); }
  };
  const saveDesign = async () => {
    setSaving(true);
    try { await api.saveDesignSystem(design); next(); } finally { setSaving(false); }
  };
  const finish = () => router.replace("/home");

  return (
    <div className="flex-1 overflow-y-auto bg-bg-alt">
      <div className="max-w-3xl mx-auto p-10">
        <div className="mb-8">
          <div className="text-xs text-muted">Step {step} of 4</div>
          <h1 className="text-2xl font-semibold text-ink mt-1">
            {step === 1 && "Welcome — confirm your persona"}
            {step === 2 && "Confirm your design system"}
            {step === 3 && "Upload your logo"}
            {step === 4 && "Review and finish"}
          </h1>
          <p className="text-sm text-muted mt-2">
            {step === 1 && "Sourcy has a starter persona pre-filled. Edit anything that's wrong, then continue."}
            {step === 2 && "Brand colors and image-style descriptors. Every generated image reads from this."}
            {step === 3 && "Logo is passed to GPT Image 2 as a reference on every ad / case study generation."}
            {step === 4 && "You can edit any of this later under Memory."}
          </p>
        </div>

        {step === 1 && (
          <div className="space-y-4">
            <Field label="One-liner" value={persona.one_liner || ""} onChange={(v) => setPersona({ ...persona, one_liner: v })} />
            <Field label="Positioning vs competitors" textarea value={persona.positioning_vs_competitors || ""} onChange={(v) => setPersona({ ...persona, positioning_vs_competitors: v })} />
            <Field label="Banned phrases (comma-separated)" textarea
              value={(persona.banned_phrases || []).join(", ")}
              onChange={(v) => setPersona({ ...persona, banned_phrases: v.split(",").map((s) => s.trim()).filter(Boolean) })}
            />
            <Buttons onBack={null} onNext={savePersona} nextDisabled={!persona.one_liner || saving} nextLabel={saving ? "Saving…" : "Save & continue"} />
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <ColorPicker label="Primary" value={design.colors?.primary || "#0F172A"}
                onChange={(v) => setDesign({ ...design, colors: { ...(design.colors || {}), primary: v } })} />
              <ColorPicker label="Accent" value={design.colors?.accent || "#22D3EE"}
                onChange={(v) => setDesign({ ...design, colors: { ...(design.colors || {}), accent: v } })} />
            </div>
            <Field label="Ad image style"
              textarea
              value={design.image_style?.ad_style || ""}
              onChange={(v) => setDesign({ ...design, image_style: { ...(design.image_style || {}), ad_style: v } })}
            />
            <Field label="Blog image style"
              textarea
              value={design.image_style?.blog_image_style || ""}
              onChange={(v) => setDesign({ ...design, image_style: { ...(design.image_style || {}), blog_image_style: v } })}
            />
            <Buttons onBack={back} onNext={saveDesign} nextDisabled={saving} nextLabel={saving ? "Saving…" : "Save & continue"} />
          </div>
        )}

        {step === 3 && <LogoStep design={design} onSaved={(d) => setDesign(d)} onNext={next} onBack={back} />}

        {step === 4 && (
          <div className="space-y-3">
            <div className="card p-4 space-y-2">
              <div className="text-sm"><span className="label">One-liner</span><div className="mt-1">{persona.one_liner}</div></div>
              <div className="text-sm"><span className="label">Positioning</span><div className="mt-1">{persona.positioning_vs_competitors}</div></div>
              <div className="text-sm flex items-center gap-3"><span className="label">Colors</span>
                <Swatch v={design.colors?.primary} /> <code className="text-xs">{design.colors?.primary}</code>
                <Swatch v={design.colors?.accent} /> <code className="text-xs">{design.colors?.accent}</code>
              </div>
              <div className="text-sm"><span className="label">Logo</span><div className="mt-1">
                {design.logo?.primary_url ? <img src={design.logo.primary_url} className="h-10" alt="logo" /> : "Skipped"}
              </div></div>
            </div>
            <Buttons onBack={back} onNext={finish} nextLabel="Open dashboard" />
          </div>
        )}
      </div>
    </div>
  );
}

function Field({ label, value, onChange, textarea }: { label: string; value: string; onChange: (v: string) => void; textarea?: boolean }) {
  return (
    <div>
      <div className="label mb-1">{label}</div>
      {textarea
        ? <textarea className="textarea" rows={3} value={value} onChange={(e) => onChange(e.target.value)} />
        : <input className="input" value={value} onChange={(e) => onChange(e.target.value)} />}
    </div>
  );
}

function ColorPicker({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div>
      <div className="label mb-1">{label}</div>
      <div className="flex items-center gap-2">
        <input type="color" value={value} onChange={(e) => onChange(e.target.value)} className="w-12 h-9 rounded border border-border bg-white p-1" />
        <input className="input flex-1 font-mono text-xs" value={value} onChange={(e) => onChange(e.target.value)} />
      </div>
    </div>
  );
}

function LogoStep({ design, onSaved, onNext, onBack }: { design: Record<string, any>; onSaved: (d: Record<string, any>) => void; onNext: () => void; onBack: () => void }) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const url = design.logo?.primary_url;

  const upload = async (f: File) => {
    setUploading(true); setError(null);
    try {
      const r = await api.uploadAsset(f, "logo");
      const next = { ...design, logo: { ...(design.logo || {}), primary_url: r.url } };
      await api.saveDesignSystem(next);
      onSaved(next);
    } catch (e: any) {
      setError(e?.message || "Upload failed");
    } finally { setUploading(false); }
  };

  return (
    <div className="space-y-4">
      <div className="card p-6 flex items-center gap-6">
        <div className="w-24 h-24 rounded-md border border-border bg-bg-alt flex items-center justify-center overflow-hidden">
          {url ? <img src={url} alt="logo" className="max-w-full max-h-full object-contain" /> : <span className="text-xs text-muted">No logo</span>}
        </div>
        <div className="flex-1">
          <input type="file" accept="image/*" onChange={(e) => { const f = e.target.files?.[0]; if (f) upload(f); }} />
          {uploading && <div className="text-xs text-muted mt-2">Uploading…</div>}
          {error && <div className="text-xs text-red-600 mt-2">{error}</div>}
        </div>
      </div>
      <Buttons onBack={onBack} onNext={onNext} nextLabel="Skip / Continue" />
    </div>
  );
}

function Buttons({ onBack, onNext, nextLabel = "Continue", nextDisabled }: { onBack: (() => void) | null; onNext: () => void; nextLabel?: string; nextDisabled?: boolean }) {
  return (
    <div className="flex items-center justify-between pt-4">
      <div>{onBack && <button className="btn-ghost" onClick={onBack}>← Back</button>}</div>
      <button className="btn-primary" disabled={nextDisabled} onClick={onNext}>{nextLabel}</button>
    </div>
  );
}

function Swatch({ v }: { v?: string }) {
  return <span className="inline-block w-5 h-5 rounded border border-border" style={{ background: v || "#fff" }} />;
}
