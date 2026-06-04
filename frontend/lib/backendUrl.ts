/**
 * API / WebSocket base URLs for local dev vs Vercel + separate backend.
 *
 * - Local: leave NEXT_PUBLIC_BACKEND_URL unset → same-origin + Next rewrites to :8000
 * - Vercel: set NEXT_PUBLIC_BACKEND_URL + NEXT_PUBLIC_BACKEND_WS_URL to your Railway/host URL
 */

export function getBackendOrigin(): string {
  const env = process.env.NEXT_PUBLIC_BACKEND_URL?.replace(/\/$/, "");
  return env || "";
}

export function apiUrl(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  const origin = getBackendOrigin();
  return origin ? `${origin}${p}` : p;
}

export function wsUrl(path: string): string {
  const env = process.env.NEXT_PUBLIC_BACKEND_WS_URL?.replace(/\/$/, "");
  if (env) return `${env}${path.startsWith("/") ? path : `/${path}`}`;
  if (typeof window === "undefined") return "";
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${window.location.hostname}:8000${path.startsWith("/") ? path : `/${path}`}`;
}

/** Turn /reports/foo.html into a full URL when UI is on Vercel and assets live on the API host. */
export function assetUrl(path: string): string {
  if (!path) return path;
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  return apiUrl(path);
}
