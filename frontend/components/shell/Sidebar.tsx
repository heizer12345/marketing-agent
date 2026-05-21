"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import { TourLaunchButton } from "@/components/onboarding/Tour";

type Item = { href: string; label: string; hint: string; icon: React.ReactNode };

// Inline SVG icons — kept minimal so we don't pull in a library
const I = {
  home: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="nav-icon">
      <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9,22 9,12 15,12 15,22"/>
    </svg>
  ),
  chat: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="nav-icon">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
    </svg>
  ),
  library: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="nav-icon">
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
    </svg>
  ),
  memory: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="nav-icon">
      <circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/>
    </svg>
  ),
  ticket: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-3.5 h-3.5">
      <path d="M2 9a3 3 0 0 1 3-3h14a3 3 0 0 1 3 3v2a2 2 0 0 0-2 2 2 2 0 0 0 2 2v2a3 3 0 0 1-3 3H5a3 3 0 0 1-3-3v-2a2 2 0 0 0 2-2 2 2 0 0 0-2-2z"/>
    </svg>
  ),
};

const items: Item[] = [
  { href: "/home",    label: "Home",    hint: "Live marketing dashboard", icon: I.home },
  { href: "/chat",    label: "Chat",    hint: "Ask anything · agents dispatch in parallel", icon: I.chat },
  { href: "/library", label: "Library", hint: "Generated blogs · ads · LPs · case studies", icon: I.library },
  { href: "/memory",  label: "Memory",  hint: "Brand voice · design system · logo", icon: I.memory },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="flex flex-col w-60 shrink-0 border-r" style={{ background: "var(--bg-rail)", borderColor: "var(--border)" }}>
      <div className="px-5 py-5 border-b" style={{ borderColor: "var(--border)" }}>
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-bold shadow-sm"
               style={{ background: "linear-gradient(135deg, #0F172A 0%, #1E293B 100%)" }}>
            S
          </div>
          <div>
            <div className="text-sm font-semibold text-ink leading-tight">Sourcy Marketing</div>
            <div className="text-[11px] text-muted leading-tight">AI co-pilot</div>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        {items.map((it) => {
          const active = pathname === it.href || pathname.startsWith(it.href + "/");
          return (
            <Link key={it.href} href={it.href} className={clsx("nav-item", active && "active")} title={it.hint}>
              <span className={clsx(!active && "text-muted-soft")}>{it.icon}</span>
              <div className="flex-1 min-w-0">
                <div className="leading-tight">{it.label}</div>
                <div className={clsx(
                  "text-[10.5px] leading-tight mt-0.5 truncate",
                  active ? "text-cyan-soft" : "text-muted-soft",
                )} style={active ? { color: "rgba(207,250,254,0.85)" } : undefined}>{it.hint}</div>
              </div>
            </Link>
          );
        })}
      </nav>

      <div className="border-t p-3 space-y-2" style={{ borderColor: "var(--border)" }}>
        <TourLaunchButton />
        <div className="text-[10px] text-muted-soft pt-1">v1.0 · Phase 3</div>
      </div>
    </aside>
  );
}
