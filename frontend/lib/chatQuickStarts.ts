export type QuickStartCategory = "seo" | "ads" | "content";

export type QuickStartOption = {
  id: QuickStartCategory;
  title: string;
  description: string;
  starterPrompt: string;
};

export const CHAT_QUICK_STARTS: QuickStartOption[] = [
  {
    id: "seo",
    title: "SEO & Website",
    description: "Audits, rankings, technical fixes, and page-level recommendations.",
    starterPrompt: `[intake-first: seo]
I want help with SEO and our website. Before running any audit or pulling data, ask me exactly 3 clarifying questions (scope, target markets, and goals). Do not call tools until I answer — unless I say "skip intake".`,
  },
  {
    id: "ads",
    title: "Ads",
    description: "Meta and Google Ads performance, waste, and optimization ideas.",
    starterPrompt: `[intake-first: ads]
I want help with our paid ads (Meta and/or Google). Before pulling ad data, ask me exactly 3 clarifying questions (platforms, date range, and primary KPI). Do not call tools until I answer — unless I say "skip intake".`,
  },
  {
    id: "content",
    title: "Content ideas",
    description: "Social posts, blogs, and calendars — questions first when context is thin.",
    starterPrompt: `[intake-first: content]
I want help with social media, blogs, or a content plan. Before generating anything, ask exactly 3 clarifying questions tailored to what I need: for social posts (result, topic, channels); for blogs (goal, audience/angle, constraints); for calendars (results, topics, formats). Skip questions if I already gave enough detail. Do not call tools until I answer — unless I say "skip intake".`,
  },
];

export const QUICK_START_TITLES: Record<QuickStartCategory, string> = {
  seo: "SEO & Website",
  ads: "Ads",
  content: "Content ideas",
};

const STOP_WORDS = new Set([
  "the", "a", "an", "and", "or", "for", "with", "from", "that", "this",
  "about", "please", "help", "need", "want", "make", "create", "write",
  "generate", "show", "give", "our", "your", "to", "on", "of", "in",
  "post", "posts", "idea", "ideas", "plan", "calendar", "content",
]);

function cleanPrompt(prompt: string): string {
  return prompt
    .replace(/\[intake-first:\s*\w+\]\s*/i, "")
    .replace(/\s+/g, " ")
    .trim();
}

function inferCategory(text: string): string {
  const t = text.toLowerCase();
  if (/linkedin|instagram|tiktok|social media|caption|reel/.test(t)) return "Social";
  if (/seo|keyword|organic|ranking|search console|ga4/.test(t)) return "SEO";
  if (/meta ads|google ads|roas|cpl|ad(s)?\b|campaign/.test(t)) return "Ads";
  if (/blog|landing page|brief|case study/.test(t)) return "Content";
  if (/report|audit|analysis|diagnostic/.test(t)) return "Analysis";
  return "Chat";
}

function pickFocus(text: string): string {
  const tokens = text
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, " ")
    .split(/\s+/)
    .filter(Boolean)
    .filter((w) => w.length > 2 && !STOP_WORDS.has(w));

  // Preserve first meaningful phrase-ish chunk (max 3 words)
  const focus = tokens.slice(0, 3).join(" ");
  if (!focus) return "General";
  return focus.replace(/\b\w/g, (c) => c.toUpperCase());
}

export function titleFromPrompt(prompt: string): string {
  const m = prompt.match(/\[intake-first:\s*(\w+)\]/i);
  if (m && m[1] in QUICK_START_TITLES) {
    const cleaned = cleanPrompt(prompt);
    const focus = pickFocus(cleaned);
    return `${QUICK_START_TITLES[m[1] as QuickStartCategory]} · ${focus}`.slice(0, 60);
  }

  const cleaned = cleanPrompt(prompt);
  if (!cleaned) return "New chat";
  const category = inferCategory(cleaned);
  const focus = pickFocus(cleaned);
  return `${category} · ${focus}`.slice(0, 60);
}
