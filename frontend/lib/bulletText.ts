/** Split agent prose into bullet lines for UI display. */
export function textToBullets(text: string): string[] {
  const raw = (text || "").trim();
  if (!raw) return [];

  const lines = raw.split(/\n/).map((l) => l.replace(/^[-•*]\s*/, "").trim()).filter(Boolean);
  if (lines.length > 1) return lines;

  const inline = raw.split(/(?<=\.)\s+(?=-\s)/).map((l) => l.replace(/^[-•*]\s*/, "").trim()).filter(Boolean);
  if (inline.length > 1) return inline;

  const sentences = raw.split(/(?<=\.)\s+(?=\S)/).map((s) => s.trim()).filter((s) => s.length > 8);
  return sentences.length > 1 ? sentences : [raw];
}
