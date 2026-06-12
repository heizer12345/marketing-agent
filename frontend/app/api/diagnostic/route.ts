import { NextResponse } from "next/server";
import {
  getServerBackendOrigin,
  isBackendConfigured,
  isHostedFrontend,
} from "@/lib/backendProxy";

/** Runtime health check — local dev defaults to localhost:8000 without env vars. */
export async function GET() {
  if (!isBackendConfigured()) {
    return NextResponse.json({
      ok: false,
      configured: false,
      hint: "Set NEXT_PUBLIC_BACKEND_URL to your API host.",
    });
  }

  const backend = getServerBackendOrigin();
  const mode = isHostedFrontend() ? "hosted" : "local";

  try {
    const r = await fetch(`${backend}/_health`, { cache: "no-store" });
    const text = await r.text();
    return NextResponse.json({
      ok: r.ok,
      configured: true,
      mode,
      backend_host: new URL(backend).host,
      health_status: r.status,
      health_body: text.slice(0, 200),
    });
  } catch (e) {
    const hint =
      mode === "local"
        ? "Start the backend: python main.py (port 8000)."
        : "Check NEXT_PUBLIC_BACKEND_URL and that the API is running.";
    return NextResponse.json({
      ok: false,
      configured: true,
      mode,
      backend_host: new URL(backend).host,
      error: e instanceof Error ? e.message : String(e),
      hint,
    });
  }
}
