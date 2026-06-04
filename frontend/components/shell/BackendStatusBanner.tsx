"use client";

import { useEffect, useState } from "react";
import { apiUrl, getBackendOrigin } from "@/lib/backendUrl";

type Status = "ok" | "missing_env" | "unreachable" | "unauthorized";

export function BackendStatusBanner() {
  const [status, setStatus] = useState<Status | null>(null);

  useEffect(() => {
    const onVercel =
      typeof window !== "undefined" &&
      (window.location.hostname.includes("vercel.app") ||
        window.location.hostname.includes("vercel.sh"));

    if (onVercel && !getBackendOrigin()) {
      setStatus("missing_env");
      return;
    }

    let cancelled = false;
    (async () => {
      try {
        const r = await fetch(apiUrl("/_health"), { credentials: "include" });
        if (cancelled) return;
        if (r.status === 401) setStatus("unauthorized");
        else if (!r.ok) setStatus("unreachable");
        else setStatus("ok");
      } catch {
        if (!cancelled) setStatus("unreachable");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (!status || status === "ok") return null;

  const copy: Record<Exclude<Status, "ok">, { title: string; body: string }> = {
    missing_env: {
      title: "Backend URL not configured",
      body:
        "In Vercel → Settings → Environment Variables, set NEXT_PUBLIC_BACKEND_URL and NEXT_PUBLIC_BACKEND_WS_URL to your API host (e.g. Railway), then redeploy. Chat and Home need the Python backend — the UI alone is not enough.",
    },
    unreachable: {
      title: "Cannot reach the marketing API",
      body:
        "Check that the backend is running, NEXT_PUBLIC_BACKEND_URL points to it, and CORS_ORIGINS on the backend includes this site URL. Redeploy both after changing env vars.",
    },
    unauthorized: {
      title: "API blocked by login",
      body:
        "On the backend host set DEV_MODE=1 or V2_PUBLIC_ACCESS=1 for prototype testing, or log in at your API /login before using this app.",
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
    </div>
  );
}
