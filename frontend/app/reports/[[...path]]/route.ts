import type { NextRequest } from "next/server";
import { proxyToBackend } from "@/lib/backendProxy";

type Ctx = { params: { path?: string[] } };

async function handle(req: NextRequest, ctx: Ctx) {
  const segments = ctx.params.path ?? [];
  const suffix = segments.length ? `/${segments.join("/")}` : "";
  return proxyToBackend(req, `/reports${suffix}`);
}

export const GET = handle;
export const HEAD = handle;
