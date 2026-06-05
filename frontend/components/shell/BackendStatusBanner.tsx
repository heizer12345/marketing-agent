"use client";

import { useEffect, useState } from "react";

type Diagnostic = {
  ok?: boolean;
  configured?: boolean;
  backend_host?: string;
  health_status?: number;
  error?: string;
  hint?: string;
};

type Status = "ok" | "missing_backend" | "unreachable" | "unauthorized" | "vercel_sso";

export function BackendStatusBanner() {
  const [status, setStatus] = useState<Status | null>(null);
  const [detail, setDetail] = useState<string>("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await fetch("/api/diagnostic", { credentials: "include" });
        if (cancelled) return;
        if (r.status === 401) {
          setStatus("vercel_sso");
          return;
        }
        const data = (await r.json()) as Diagnostic;
        if (!data.configured) {
          setStatus("missing_backend");
          setDetail(data.hint || "");
          return;
        }
        if (!data.ok) {
          setStatus("unreachable");
          setDetail(data.error || `health ${data.health_status}`);
          return;
        }
        setStatus("ok");
      } catch (e) {
        if (cancelled) return;
        setStatus("unreachable");
        setDetail(e instanceof Error ? e.message : "network error");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (!status || status === "ok") return null;

  const copy: Record<Exclude<Status, "ok">, { title: string; body: string }> = {
    missing_backend: {
      title: "Railway URL not set on the frontend host",
      body:
        "On Render (or Vercel) → Environment: set NEXT_PUBLIC_BACKEND_URL and NEXT_PUBLIC_BACKEND_WS_URL to your Railway domain (https://… and wss://…). Redeploy. Railway must have V2_PUBLIC_ACCESS=1.",
    },
    unreachable: {
      title: "Frontend cannot reach Railway",
      body:
        "Open your Railway /_health and /api/v2/memory/state in the browser. Confirm NEXT_PUBLIC_BACKEND_URL matches exactly (no trailing slash), then redeploy the frontend.",
    },
    unauthorized: {
      title: "Railway API blocked by login",
      body: "On Railway set V2_PUBLIC_ACCESS=1 and restart the service.",
    },
    vercel_sso: {
      title: "Vercel Deployment Protection is blocking this site",
      body:
        "Vercel → Project → Settings → Deployment Protection → disable for Preview (or add testers to your team). Preview URLs require Vercel login otherwise Home/Chat API calls fail with 401.",
    },
  };

  const msg = copy[status];

  return (
    <div
      className="shrink-0 px-4 py-2.5 text-[12.5px] border-b"
      style={{ background: "#FEF2F2", borderColor: "rgba(239,68,68,0.35)", color: "#7F1D1D" }}
      role="alert"
    >
      <span className="font-semibold">{msg.title}. </span>
      {msg.body}
      {detail ? <span className="block mt-1 opacity-80">({detail})</span> : null}
    </div>
  );
}
