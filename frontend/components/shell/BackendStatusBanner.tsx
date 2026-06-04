"use client";

import { useEffect, useState } from "react";

type Status = "ok" | "missing_backend" | "unreachable" | "unauthorized";

export function BackendStatusBanner() {
  const [status, setStatus] = useState<Status | null>(null);
  const [detail, setDetail] = useState<string>("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await fetch("/api/v2/memory/state", { credentials: "include" });
        if (cancelled) return;
        if (r.status === 401) {
          setStatus("unauthorized");
          return;
        }
        if (!r.ok) {
          setStatus("unreachable");
          setDetail(`${r.status} ${r.statusText}`);
          return;
        }
        setStatus("ok");
      } catch (e) {
        if (cancelled) return;
        const onVercel =
          window.location.hostname.includes("vercel.app") ||
          window.location.hostname.includes("vercel.sh");
        setStatus(onVercel ? "missing_backend" : "unreachable");
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
      title: "Python API not connected",
      body:
        "This Vercel site is only the UI. Deploy the backend (Railway/Render: python main.py), then in Vercel → Settings → Environment Variables set NEXT_PUBLIC_BACKEND_URL=https://your-api-host (no trailing slash) and NEXT_PUBLIC_BACKEND_WS_URL=wss://your-api-host. On the backend set V2_PUBLIC_ACCESS=1. Redeploy Vercel after saving env vars.",
    },
    unreachable: {
      title: "Marketing API returned an error",
      body:
        "The UI reached a proxy but the backend failed. Confirm the API is running, NEXT_PUBLIC_BACKEND_URL is correct, and you redeployed Vercel after changing it. Backend env: V2_PUBLIC_ACCESS=1.",
    },
    unauthorized: {
      title: "API blocked by login",
      body:
        "On the backend host set V2_PUBLIC_ACCESS=1 (or DEV_MODE=1) for prototype testing, then restart the API.",
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
