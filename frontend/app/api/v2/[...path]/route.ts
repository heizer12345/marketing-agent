import type { NextRequest } from "next/server";
import { proxyToBackend } from "@/lib/backendProxy";

export const dynamic = "force-dynamic";
export const maxDuration = 120;

type Ctx = { params: { path: string[] } };

async function handle(req: NextRequest, ctx: Ctx) {
  const segments = ctx.params.path ?? [];
  return proxyToBackend(req, `/api/v2/${segments.join("/")}`);
}

export const GET = handle;
export const POST = handle;
export const PUT = handle;
export const PATCH = handle;
export const DELETE = handle;
