/** @type {import('next').NextConfig} */
const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

module.exports = {
  // StrictMode double-mounts effects in dev, which breaks WebSocket lifetimes —
  // each mount opens a WS, the cleanup closes it, then the second mount opens a
  // new one. The second connection often dies before fully establishing because
  // of the close-during-handshake race. Disable it.
  reactStrictMode: false,
  async rewrites() {
    return [
      { source: "/api/v2/:path*", destination: `${BACKEND}/api/v2/:path*` },
      { source: "/api/:path*", destination: `${BACKEND}/api/:path*` },
      { source: "/ws", destination: `${BACKEND}/ws` },
      { source: "/ws/:path*", destination: `${BACKEND}/ws/:path*` },
      { source: "/reports/:path*", destination: `${BACKEND}/reports/:path*` },
      { source: "/content/:path*", destination: `${BACKEND}/content/:path*` },
      { source: "/brand/:path*", destination: `${BACKEND}/brand/:path*` },
      { source: "/reviews/:path*", destination: `${BACKEND}/reviews/:path*` },
    ];
  },
};
