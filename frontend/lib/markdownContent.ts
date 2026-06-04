export type ContentFrontmatter = {
  title?: string;
  type?: string;
  date?: string;
  keywords?: string;
  summary?: string;
};

/** Remove leading `---` YAML block so previews show human-readable content only. */
export function stripYamlFrontmatter(markdown: string): string {
  return parseMarkdownDocument(markdown).body;
}

export function parseMarkdownDocument(markdown: string): {
  meta: ContentFrontmatter;
  body: string;
} {
  const trimmed = markdown.replace(/^\uFEFF/, "").trimStart();
  if (!trimmed.startsWith("---")) {
    return { meta: {}, body: markdown.trim() };
  }

  const end = trimmed.indexOf("\n---", 3);
  if (end === -1) {
    return { meta: {}, body: markdown.trim() };
  }

  const yamlBlock = trimmed.slice(3, end).trim();
  let body = trimmed.slice(end + 4).trimStart();
  const meta: ContentFrontmatter = {};

  for (const line of yamlBlock.split("\n")) {
    const m = line.match(/^([a-z_]+):\s*(.*)$/i);
    if (!m) continue;
    const key = m[1].toLowerCase() as keyof ContentFrontmatter;
    let val = m[2].trim();
    if (
      (val.startsWith('"') && val.endsWith('"')) ||
      (val.startsWith("'") && val.endsWith("'"))
    ) {
      val = val.slice(1, -1);
    }
    if (key === "title" || key === "type" || key === "date" || key === "keywords" || key === "summary") {
      meta[key] = val;
    }
  }

  // Drop a duplicate H1 immediately after frontmatter if it matches the title.
  if (meta.title && body.startsWith("#")) {
    const firstLine = body.split("\n")[0];
    const h1 = firstLine.replace(/^#+\s*/, "").trim().toLowerCase();
    const titleNorm = meta.title.trim().toLowerCase();
    if (h1 === titleNorm || titleNorm.includes(h1) || h1.includes(titleNorm)) {
      body = body.slice(firstLine.length).trimStart();
    }
  }

  return { meta, body };
}

export function displayTitleFromPath(path: string, meta?: ContentFrontmatter): string {
  if (meta?.title) return meta.title;
  const base = path.split("/").pop()?.replace(/\.md$/i, "") ?? "Document";
  return base.replace(/[-_]/g, " ").replace(/\s+/g, " ");
}
