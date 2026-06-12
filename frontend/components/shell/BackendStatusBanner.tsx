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
          setDetail(data.hint || data.error || `health ${data.health_status}`);
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
      title: "Backend URL not configured",
      body:
        "Run python main.py in the project root (port 8000), or set NEXT_PUBLIC_BACKEND_URL and NEXT_PUBLIC_BACKEND_WS_URL to your API host.",
    },
    unreachable: {
      title: "Cannot reach the backend",
      body:
        "Confirm the API is running and opens /_health in your browser. For local dev, start the backend with python main.py.",
    },
    unauthorized: {
      title: "API blocked by login",
      body: "Set DEV_MODE=1 in .env for local dev, or log in via the backend /login page.",
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
