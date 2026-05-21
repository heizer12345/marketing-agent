"use client";

import { useRef, useState } from "react";
import { api } from "@/lib/api";

export function LogoUploader({
  design,
  onSaved,
}: {
  design: Record<string, any>;
  onSaved: () => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [lastUrl, setLastUrl] = useState<string | null>(design?.logo?.primary_url || null);
  const [error, setError] = useState<string | null>(null);

  const upload = async (file: File, asset_type = "logo") => {
    setUploading(true); setError(null);
    try {
      const res = await api.uploadAsset(file, asset_type);
      // Patch the design system to point logo.primary_url at the uploaded path.
      const next = JSON.parse(JSON.stringify(design));
      if (asset_type === "logo") {
        next.logo = { ...(next.logo || {}), primary_url: res.url };
      } else {
        next.brand_assets = [...(next.brand_assets || []), { type: asset_type, path: res.url, tags: [] }];
      }
      await api.saveDesignSystem(next);
      setLastUrl(res.url);
      onSaved();
    } catch (e: any) {
      setError(e?.message || "Upload failed");
    } finally { setUploading(false); }
  };

  return (
    <div className="space-y-6">
      <section>
        <div className="label mb-1">Logo</div>
        <p className="text-xs text-muted mb-3">SVG or PNG. Passed as a reference image to GPT Image 2 on every ad/case study image generation.</p>
        <div className="card p-6 flex items-center gap-6">
          <div className="w-24 h-24 rounded-md border border-border bg-bg-alt flex items-center justify-center overflow-hidden">
            {lastUrl ? (
              <img src={lastUrl} alt="Logo preview" className="max-w-full max-h-full object-contain" />
            ) : (
              <span className="text-xs text-muted">No logo</span>
            )}
          </div>
          <div className="flex-1">
            <input
              ref={inputRef}
              type="file"
              accept="image/svg+xml,image/png,image/jpeg"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) upload(f, "logo");
              }}
            />
            <button className="btn-primary" onClick={() => inputRef.current?.click()} disabled={uploading}>
              {uploading ? "Uploading…" : "Upload logo"}
            </button>
            {lastUrl && <div className="mt-2 text-xs text-muted">URL: <span className="font-mono">{lastUrl}</span></div>}
            {error && <div className="mt-2 text-xs text-red-600">{error}</div>}
          </div>
        </div>
      </section>

      <section>
        <div className="label mb-1">Brand assets (additional)</div>
        <p className="text-xs text-muted mb-3">Product photos, packaging shots, lifestyle imagery. Used as reference for generated images.</p>
        <BrandAssetGrid design={design} />
      </section>
    </div>
  );
}

function BrandAssetGrid({ design }: { design: Record<string, any> }) {
  const assets: Array<{ type: string; path: string; tags?: string[] }> = design?.brand_assets || [];
  if (!assets.length) return <div className="text-sm text-muted">No assets yet.</div>;
  return (
    <div className="grid grid-cols-4 gap-3">
      {assets.map((a, i) => (
        <div key={i} className="card p-2">
          <div className="aspect-square bg-bg-alt rounded overflow-hidden flex items-center justify-center">
            <img src={a.path} alt={a.type} className="max-w-full max-h-full object-contain" />
          </div>
          <div className="text-xs text-muted mt-1 truncate">{a.type}</div>
        </div>
      ))}
    </div>
  );
}
