import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

/** Server-side backend URL — read at request time (not baked into rewrites at build). */
export function getServerBackendOrigin(): string {
  const url =
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    process.env.BACKEND_URL ||
    "http://localhost:8000";
  return url.replace(/\/$/, "");
}

export async function proxyToBackend(
  req: NextRequest,
  backendPath: string,
): Promise<NextResponse> {
  const origin = getServerBackendOrigin();
  const onCloud = Boolean(process.env.VERCEL || process.env.RENDER);
  if (onCloud && !process.env.NEXT_PUBLIC_BACKEND_URL && !process.env.BACKEND_URL) {
    return NextResponse.json(
      {
        error: "Backend not configured",
        hint: "Set NEXT_PUBLIC_BACKEND_URL to your Railway URL on Render (or Vercel), then redeploy.",
      },
      { status: 503 },
    );
  }

  const path = backendPath.startsWith("/") ? backendPath : `/${backendPath}`;
  const target = `${origin}${path}${req.nextUrl.search}`;

  const headers = new Headers();
  const contentType = req.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  const cookie = req.headers.get("cookie");
  if (cookie) headers.set("cookie", cookie);

  let body: BodyInit | undefined;
  if (req.method !== "GET" && req.method !== "HEAD") {
    body = contentType?.includes("multipart/form-data")
      ? await req.arrayBuffer()
      : await req.text();
  }

  try {
    const res = await fetch(target, {
      method: req.method,
      headers,
      body,
      cache: "no-store",
    });

    const outHeaders = new Headers();
    const resType = res.headers.get("content-type");
    if (resType) outHeaders.set("content-type", resType);

    return new NextResponse(res.body, { status: res.status, headers: outHeaders });
  } catch (e) {
    return NextResponse.json(
      {
        error: "Backend unreachable",
        backend: origin,
        detail: e instanceof Error ? e.message : String(e),
      },
      { status: 502 },
    );
  }
}
