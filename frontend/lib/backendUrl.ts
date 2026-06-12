/**
 * URL helpers for local dev vs hosted frontend + separate Python API.
 *
 * REST (browser): same-origin paths (/api/v2/...) proxied to NEXT_PUBLIC_BACKEND_URL.
 *
 * WebSocket (browser): must use NEXT_PUBLIC_BACKEND_WS_URL (wss://your-api-host).
 */

export function getBackendOrigin(): string {
  const env = process.env.NEXT_PUBLIC_BACKEND_URL?.replace(/\/$/, "");
  return env || "";
}

/** HTTP API path — browser uses relative URLs; server components hit the backend directly. */
export function apiUrl(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  if (typeof window !== "undefined") {
    return p;
  }
  const origin =
    getBackendOrigin() ||
    process.env.BACKEND_URL?.replace(/\/$/, "") ||
    "http://localhost:8000";
  return `${origin}${p}`;
}

export function wsUrl(path: string): string {
  const env = process.env.NEXT_PUBLIC_BACKEND_WS_URL?.replace(/\/$/, "");
  if (env) return `${env}${path.startsWith("/") ? path : `/${path}`}`;
  if (typeof window !== "undefined") {
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    return `${proto}://${window.location.hostname}:8000${path.startsWith("/") ? path : `/${path}`}`;
  }
  return "";
}

/** Reports/content assets — relative in browser (rewritten); absolute on server when configured. */
export function assetUrl(path: string): string {
  if (!path) return path;
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  if (typeof window !== "undefined") {
    return path.startsWith("/") ? path : `/${path}`;
  }
  return apiUrl(path);
}
