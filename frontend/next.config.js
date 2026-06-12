/** @type {import('next').NextConfig} */
const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

module.exports = {
  // StrictMode double-mounts effects in dev, which breaks WebSocket lifetimes —
  // each mount opens a WS, the cleanup closes it, then the second mount opens a
  // new one. The second connection often dies before fully establishing because
  // of the close-during-handshake race. Disable it.
  reactStrictMode: false,
  async rewrites() {
    const base = BACKEND.replace(/\/$/, "");
    // API traffic uses app/api/** route handlers (backendProxy) — do NOT duplicate
    // /api/* here; Next rewrites return opaque 500s ("socket hang up") when the
    // backend is slow or restarting.
    return [
      { source: "/ws", destination: `${base}/ws` },
      { source: "/ws/:path*", destination: `${base}/ws/:path*` },
      { source: "/content/:path*", destination: `${base}/content/:path*` },
      { source: "/brand/:path*", destination: `${base}/brand/:path*` },
      { source: "/reviews/:path*", destination: `${base}/reviews/:path*` },
    ];
  },
};
