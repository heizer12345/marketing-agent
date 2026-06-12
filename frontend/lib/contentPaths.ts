/** Public marketing site — use for copy-paste and open-in-new-tab links. */
export const PUBLIC_SITE_ORIGIN =
  (typeof process !== "undefined" && process.env.NEXT_PUBLIC_SITE_ORIGIN) ||
  "https://www.sourcy.ai";

export function toPublicAssetUrl(path: string): string {
  let p = path.trim().replace(/^`+|`+$/g, "");
  if (p.startsWith("www.")) return `https://${p}`;
  if (p.startsWith("http://") || p.startsWith("https://")) {
    try {
      const u = new URL(p);
      if (u.hostname.replace(/^www\./, "").endsWith("sourcy.ai")) {
        return `${PUBLIC_SITE_ORIGIN}${u.pathname}`;
      }
    } catch {
      /* keep */
    }
    return p;
  }
  if (!p.startsWith("/") && p.includes("/content/")) {
    const m = p.match(/\/content\/[^\s)\]"']+/i);
    if (m) p = m[0];
  }
  return `${PUBLIC_SITE_ORIGIN}${p.startsWith("/") ? p : `/${p}`}`;
}

/** Display form for copy: www.sourcy.ai/content/... */
export function publicAssetLabel(pathOrUrl: string): string {
  return toPublicAssetUrl(pathOrUrl).replace(/^https:\/\//i, "www.");
}

export function isSourcyContentAsset(href: string | undefined): boolean {
  if (!href) return false;
  // Saved markdown (calendars, blogs, …) opens in /preview/content — not the public site.
  if (/\.md$/i.test(href)) return false;
  if (/^https?:\/\/(www\.)?sourcy\.ai\/content\//i.test(href)) return true;
  return /^\/content\/(images|calendars|blogs|audits|briefs|landing-pages|ads|case-studies)\//i.test(
    href,
  );
}

/** `/content/calendars/foo.md` → in-app preview route */
export function normalizeContentPath(path: string): string {
  let p = path.trim().replace(/^`+|`+$/g, "");
  if (p.startsWith("http://") || p.startsWith("https://")) {
    try {
      const u = new URL(p);
      if (u.pathname.includes("/content/")) p = u.pathname;
    } catch {
      /* keep */
    }
  }
  if (p.startsWith("public/content/")) {
    p = "/" + p.slice("public/".length);
  }
  if (!p.startsWith("/") && p.includes("/content/")) {
    const m = p.match(/\/content\/[^\s)\]"']+\.md/i);
    if (m) p = m[0];
  }
  return p;
}

export function contentPreviewHref(path: string): string {
  const p = normalizeContentPath(path);
  const rel = p.startsWith("/content/") ? p.slice("/content/".length) : p.replace(/^\/+/, "");
  return `/preview/content/${rel}`;
}

const CONTENT_PATH_RE =
  /(?:public\/)?(\/content\/[a-zA-Z0-9_./-]+\.md)/gi;

const CONTENT_ASSET_RE =
  /(?:public\/)?(\/content\/(?:images|calendars|blogs|audits|briefs|landing-pages|ads|case-studies)\/[a-zA-Z0-9_./%-]+\.(?:png|jpe?g|webp|gif|html))/gi;

const REPORT_PATH_RE =
  /(?:public\/)?(\/reports\/[a-zA-Z0-9_./-]+\.html)/gi;

export function extractContentMdPaths(markdown: string): string[] {
  const found = new Set<string>();
  Array.from(markdown.matchAll(CONTENT_PATH_RE)).forEach((m) => {
    found.add(normalizeContentPath(m[1]));
  });
  return [...found];
}

/** Human-readable link text instead of a long filename. */
export function contentLinkLabel(path: string): string {
  const normalized = normalizeContentPath(path);
  const file = normalized.split("/").pop()?.replace(/\.md$/i, "") ?? "";
  if (file.startsWith("content-calendar")) return "Open content calendar";
  if (file.includes("calendar")) return "Open calendar";
  if (file.includes("blog")) return "Open blog draft";
  if (file.includes("landing")) return "Open landing page";
  if (file.includes("brief")) return "Open content brief";
  const cleaned = file
    .replace(/_\d{8}(_\d{6,8})?$/i, "")
    .replace(/-/g, " ")
    .trim();
  if (!cleaned) return "Open document";
  if (cleaned.length > 42) return `Open ${cleaned.slice(0, 40)}…`;
  return `Open ${cleaned}`;
}

export function reportLinkLabel(path: string): string {
  const file = path.split("/").pop()?.replace(/\.html$/i, "") ?? "";
  if (file.startsWith("report_")) return "Open report";
  return file ? `Open ${file.replace(/-/g, " ").slice(0, 40)}` : "Open report";
}

const BARE_URL_RE =
  /(?<!\]\()(https?:\/\/[^\s)\]"'<]+)/gi;

/** Turn bare `/content/...md`, `/reports/...html`, and https URLs into markdown links. */
export function linkifyArtifactPaths(markdown: string): string {
  let out = markdown;

  out = out.replace(CONTENT_PATH_RE, (full, path, offset) => {
    const norm = normalizeContentPath(path);
    if (isInsideMarkdownLink(out, offset)) return full;
    return `[${contentLinkLabel(norm)}](${norm})`;
  });

  out = out.replace(CONTENT_ASSET_RE, (full, path, offset) => {
    if (isInsideMarkdownLink(out, offset)) return full;
    const pub = toPublicAssetUrl(path);
    const label = publicAssetLabel(path);
    return `[${label}](${pub})`;
  });

  out = out.replace(REPORT_PATH_RE, (full, path, offset) => {
    const norm = path.startsWith("/") ? path : `/${path}`;
    if (isInsideMarkdownLink(out, offset)) return full;
    const pub = toPublicAssetUrl(norm);
    return `[${reportLinkLabel(norm)}](${pub})`;
  });

  out = out.replace(BARE_URL_RE, (url, offset) => {
    if (isInsideMarkdownLink(out, offset)) return url;
    const clean = url.replace(/[.,;]+$/, "");
    const suffix = url.slice(clean.length);
    // Social post URLs are often hallucinated or dead — keep as plain text to copy
    if (!shouldAutoLinkExternalUrl(clean)) {
      return clean + suffix;
    }
    const label = externalUrlLabel(clean);
    return `[${label}](${clean})${suffix}`;
  });

  return out;
}

/** Reddit, Trends, news, IG/TikTok — OK to hyperlink. LinkedIn posts — plain URL (often break). */
export function shouldAutoLinkExternalUrl(url: string): boolean {
  const u = url.toLowerCase();
  if (u.includes("linkedin.com") || u.includes("/embed/")) {
    return false;
  }
  return true;
}

function externalUrlLabel(url: string): string {
  const u = url.toLowerCase();
  if (u.includes("linkedin.com")) return "LinkedIn post";
  if (u.includes("instagram.com")) return "Instagram post";
  if (u.includes("tiktok.com")) return "TikTok post";
  if (u.includes("reddit.com")) return "Reddit thread";
  if (u.includes("trends.google")) return "Google Trends";
  if (u.includes("facebook.com/ads/library")) return "Meta Ad Library";
  if (u.includes("sourcy.ai")) return "Source";
  try {
    const host = new URL(url).hostname.replace(/^www\./, "");
    return host.length > 28 ? `${host.slice(0, 26)}…` : host;
  } catch {
    return "Link";
  }
}

function isInsideMarkdownLink(text: string, index: number): boolean {
  const before = text.slice(0, index);
  const open = before.lastIndexOf("[");
  const close = before.lastIndexOf("](");
  return open >= 0 && close > open;
}

export function isContentPreviewPath(href: string | undefined): boolean {
  if (!href) return false;
  const p = normalizeContentPath(href);
  return /^\/content\/.*\.md$/i.test(p);
}

export function isReportPath(href: string | undefined): boolean {
  if (!href) return false;
  return /^\/reports\/.*\.html$/i.test(href);
}
