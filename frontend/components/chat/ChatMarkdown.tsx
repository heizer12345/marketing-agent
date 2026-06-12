"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  contentLinkLabel,
  contentPreviewHref,
  isContentPreviewPath,
  isReportPath,
  isSourcyContentAsset,
  linkifyArtifactPaths,
  publicAssetLabel,
  shouldAutoLinkExternalUrl,
  toPublicAssetUrl,
} from "@/lib/contentPaths";

function SourcyAssetLink({ href, children }: { href: string; children?: ReactNode }) {
  const full = toPublicAssetUrl(href);
  const label = publicAssetLabel(full);
  const isImage = /\.(png|jpe?g|webp|gif)$/i.test(full);

  const copy = () => {
    void navigator.clipboard?.writeText(label);
  };

  return (
    <span className="inline-flex flex-wrap items-center gap-2 my-1 align-baseline max-w-full">
      <a
        href={full}
        target="_blank"
        rel="noreferrer"
        className="inline-flex items-center gap-1 shrink-0 font-medium text-cyan-800 underline underline-offset-2 hover:text-cyan-950 text-[12px]"
      >
        {isImage ? "Open image" : "Open"} ↗
      </a>
      <button
        type="button"
        onClick={copy}
        className="shrink-0 text-[11px] font-medium text-muted hover:text-ink border rounded px-1.5 py-0.5"
        style={{ borderColor: "var(--border)" }}
        title={`Copy ${label}`}
      >
        Copy link
      </button>
      <code className="text-[11px] text-ink/80 break-all font-normal bg-bg-alt px-1 py-0.5 rounded">
        {typeof children === "string" && !children.includes("/content/") ? children : label}
      </code>
    </span>
  );
}

const mdLink = {
  a: ({ href, children }: { href?: string; children?: ReactNode }) => {
    // Markdown calendars/blogs → in-app preview (must run before isSourcyContentAsset).
    if (isContentPreviewPath(href)) {
      const label =
        typeof children === "string" && children.includes("/content/")
          ? contentLinkLabel(href!)
          : children;
      return (
        <Link
          href={contentPreviewHref(href!)}
          className="inline-flex items-center gap-1 font-medium text-cyan-800 underline underline-offset-2 hover:text-cyan-950"
        >
          {label}
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-3.5 h-3.5 shrink-0" aria-hidden>
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
            <polyline points="15,3 21,3 21,9" />
            <line x1="10" y1="14" x2="21" y2="3" />
          </svg>
        </Link>
      );
    }
    if (href && isSourcyContentAsset(href)) {
      return <SourcyAssetLink href={href}>{children}</SourcyAssetLink>;
    }
    if (href && !shouldAutoLinkExternalUrl(href)) {
      return (
        <a
          href={href}
          target="_blank"
          rel="noreferrer"
          className="break-all text-cyan-800 underline underline-offset-2 text-[12px]"
        >
          {children}
        </a>
      );
    }
    if (isReportPath(href)) {
      const full = href!.startsWith("http") ? href! : toPublicAssetUrl(href!);
      return (
        <a
          href={full}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1 font-medium text-cyan-800 underline underline-offset-2"
        >
          {children}
        </a>
      );
    }
    return (
      <a href={href} target="_blank" rel="noreferrer" className="text-cyan-700 underline">
        {children}
      </a>
    );
  },
};

type Props = {
  markdown: string;
  className?: string;
  /** Extra react-markdown component overrides (e.g. citation chips in artifacts). */
  components?: Record<string, React.ComponentType<any>>;
};

export function ChatMarkdown({ markdown, className, components }: Props) {
  const prepared = linkifyArtifactPaths(markdown);

  return (
    <div className={className}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={{ ...mdLink, ...components }}>
        {prepared}
      </ReactMarkdown>
    </div>
  );
}
