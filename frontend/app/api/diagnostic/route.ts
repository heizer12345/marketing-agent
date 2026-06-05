import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";
import { getServerBackendOrigin } from "@/lib/backendProxy";

/** Runtime health + wiring check (does not require Railway CORS). */
export async function GET() {
  const backend = getServerBackendOrigin();
  const configured = Boolean(
    process.env.NEXT_PUBLIC_BACKEND_URL || process.env.BACKEND_URL,
  );

  if (!configured) {
    return NextResponse.json({
      ok: false,
      configured: false,
      hint: "Set NEXT_PUBLIC_BACKEND_URL on Vercel to your Railway public URL.",
    });
  }

  try {
    const r = await fetch(`${backend}/_health`, { cache: "no-store" });
    const text = await r.text();
    return NextResponse.json({
      ok: r.ok,
      configured: true,
      backend_host: new URL(backend).host,
      health_status: r.status,
      health_body: text.slice(0, 200),
    });
  } catch (e) {
    return NextResponse.json({
      ok: false,
      configured: true,
      backend_host: new URL(backend).host,
      error: e instanceof Error ? e.message : String(e),
    });
  }
}
