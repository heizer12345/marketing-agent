import Link from "next/link";
import { notFound } from "next/navigation";
import { ContentPreviewPage } from "@/components/content/ContentPreviewPage";
import { displayTitleFromPath, parseMarkdownDocument } from "@/lib/markdownContent";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

async function loadMarkdown(segments: string[]): Promise<string | null> {
  const rel = segments.join("/");
  try {
    const r = await fetch(`${BACKEND}/content/${rel}`, { cache: "no-store" });
    if (!r.ok) return null;
    return r.text();
  } catch {
    return null;
  }
}

export default async function PreviewContentPage({
  params,
}: {
  params: { path?: string[] };
}) {
  const segments = params.path ?? [];
  if (!segments.length) notFound();

  const markdown = await loadMarkdown(segments);
  if (!markdown) notFound();

  const { meta } = parseMarkdownDocument(markdown);
  const title = displayTitleFromPath(segments.join("/"), meta);

  return (
    <div
      className="flex-1 min-h-0 h-full overflow-y-auto thin-scroll"
      style={{ background: "var(--bg-alt)" }}
    >
      <header
        className="sticky top-0 z-10 border-b px-6 py-3 flex items-center gap-4"
        style={{ background: "white", borderColor: "var(--border)" }}
      >
        <Link href="/chat" className="btn-ghost text-[12px]">
          ← Back to chat
        </Link>
        <div className="flex-1 min-w-0">
          <div className="text-[10px] font-semibold uppercase tracking-wide text-muted">Content preview</div>
          <h1 className="text-base font-semibold text-ink truncate capitalize">{title}</h1>
        </div>
      </header>
      <main className="max-w-3xl mx-auto px-6 py-8 pb-24">
        <ContentPreviewPage markdown={markdown} />
      </main>
    </div>
  );
}
