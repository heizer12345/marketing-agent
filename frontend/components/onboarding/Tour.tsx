"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const TOUR_KEY = "sourcy-tour-completed-v1";
const AUTO_OPEN_DELAY_MS = 1500;
const STEP_AUTOPLAY_MS = 8000;

type Step = {
  title: string;
  body: string;
  href?: string;          // optional navigation when entering this step
  illustration?: string;  // emoji marker — keeps the modal lightweight
};

const STEPS: Step[] = [
  {
    title: "Welcome to Sourcy Marketing",
    body: "An AI co-pilot for Sourcy's marketing team. It pulls from every data source you have (GA4, Search Console, Meta Ads, Google Ads, Sourcy DB) and produces analysis, blogs, ads, landing pages, and case studies — on-brand and citation-backed. Take this 60-second tour.",
    illustration: "👋",
  },
  {
    title: "Home — your morning briefing",
    body: "Auto-pilot pulls every connected data source and writes a structured briefing: KPIs, alerts, what changed this week, top movers, recommended next moves. Click Refresh to re-run anytime.",
    href: "/home",
    illustration: "📊",
  },
  {
    title: "Chat — ask anything, watch agents work",
    body: "Type a prompt. A planner reads it and dispatches specialist agents (SEO, Traffic, Competitor, etc.) in parallel. Every claim in the answer has a citation chip that jumps to the agent that produced it.",
    href: "/chat",
    illustration: "💬",
  },
  {
    title: "Library — every generated piece",
    body: "Blogs, landing pages, ads (3-variant grids), case studies, and images. Every artifact is tagged with the chat session that created it — one click takes you back to its conversation.",
    href: "/library",
    illustration: "📚",
  },
  {
    title: "Memory — Sourcy's brand brain",
    body: "Persona (voice, ICP, banned phrases), design system (navy + cyan, Inter font, image style descriptors), and uploaded logo. Every generation skill reads from here — edit once, applies everywhere.",
    href: "/memory",
    illustration: "🧠",
  },
  {
    title: "You're ready",
    body: "Try a prompt in Chat or hit Refresh on Home. You can re-open this tour any time from the sidebar.",
    illustration: "🎉",
  },
];

function useTourState() {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState(0);
  const [paused, setPaused] = useState(false);

  // First-visit auto-open
  useEffect(() => {
    if (typeof window === "undefined") return;
    const done = window.localStorage.getItem(TOUR_KEY);
    if (done) return;
    const t = setTimeout(() => setOpen(true), AUTO_OPEN_DELAY_MS);
    return () => clearTimeout(t);
  }, []);

  return { open, setOpen, step, setStep, paused, setPaused };
}

export function TourLaunchButton() {
  const router = useRouter();
  const { open, setOpen, step, setStep, paused, setPaused } = useTourState();

  return (
    <>
      <button
        className="flex items-center gap-2 w-full text-left text-xs text-muted hover:text-ink transition-colors"
        onClick={() => { setStep(0); setOpen(true); }}
        title="Take the 60-second tour"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-3.5 h-3.5">
          <circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
        Take the tour
      </button>
      {open && <TourModal step={step} setStep={setStep} paused={paused} setPaused={setPaused}
        onClose={() => {
          setOpen(false);
          if (typeof window !== "undefined") window.localStorage.setItem(TOUR_KEY, "1");
        }}
        onNavigate={(href) => router.push(href)}
      />}
    </>
  );
}

function TourModal({ step, setStep, paused, setPaused, onClose, onNavigate }: {
  step: number;
  setStep: (s: number) => void;
  paused: boolean;
  setPaused: (b: boolean) => void;
  onClose: () => void;
  onNavigate: (href: string) => void;
}) {
  const current = STEPS[step];
  const isLast = step === STEPS.length - 1;
  const [tick, setTick] = useState(0);

  // Autoplay countdown — advances every STEP_AUTOPLAY_MS unless paused.
  useEffect(() => {
    if (paused || isLast) return;
    const start = Date.now();
    const interval = setInterval(() => {
      const elapsed = Date.now() - start;
      setTick(elapsed);
      if (elapsed >= STEP_AUTOPLAY_MS) {
        clearInterval(interval);
        setStep(step + 1);
      }
    }, 100);
    return () => clearInterval(interval);
  }, [step, paused, isLast, setStep]);

  // Navigate when entering a step that has a target route.
  useEffect(() => {
    if (current.href) onNavigate(current.href);
  }, [step]); // eslint-disable-line

  const progress = isLast ? 1 : Math.min(1, tick / STEP_AUTOPLAY_MS);

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-end p-6 pointer-events-none">
      <div className="absolute inset-0 bg-black/10 backdrop-blur-[2px] pointer-events-auto" onClick={onClose} />
      <div className="relative card pointer-events-auto p-5 w-[420px] shadow-2xl" style={{ boxShadow: "0 24px 48px -12px rgba(15,23,42,0.25)" }}>
        {/* Progress bar */}
        <div className="absolute top-0 left-0 right-0 h-1 rounded-t-xl overflow-hidden bg-bg-alt">
          <div className="h-full transition-[width] duration-100 ease-linear"
               style={{ width: `${progress * 100}%`, background: "var(--cyan)" }} />
        </div>

        <div className="flex items-start gap-3 mb-3">
          <div className="text-3xl shrink-0">{current.illustration}</div>
          <div className="flex-1 min-w-0">
            <div className="text-[10px] uppercase tracking-wider text-muted font-semibold">Step {step + 1} of {STEPS.length}</div>
            <h2 className="text-base font-semibold text-ink mt-0.5" style={{ letterSpacing: "-0.01em" }}>{current.title}</h2>
          </div>
          <button onClick={onClose} className="text-muted hover:text-ink text-lg leading-none" title="Skip tour">×</button>
        </div>

        <p className="text-[13px] text-ink leading-relaxed mb-4">{current.body}</p>

        <div className="flex items-center justify-between gap-2">
          <button
            className="text-[11px] text-muted hover:text-ink"
            onClick={() => setPaused(!paused)}
          >
            {paused ? "▶︎ Resume autoplay" : "⏸ Pause autoplay"}
          </button>

          <div className="flex items-center gap-2">
            {step > 0 && (
              <button className="btn-ghost text-[12px]" onClick={() => setStep(step - 1)}>← Back</button>
            )}
            {isLast ? (
              <button className="btn-primary text-[12px]" onClick={onClose}>Get started</button>
            ) : (
              <button className="btn-primary text-[12px]" onClick={() => setStep(step + 1)}>Next →</button>
            )}
          </div>
        </div>

        <div className="mt-3 flex items-center justify-center gap-1">
          {STEPS.map((_, i) => (
            <span key={i} className={`h-1 w-6 rounded-full transition-colors ${i <= step ? "bg-ink" : "bg-bg-alt"}`} />
          ))}
        </div>
      </div>
    </div>
  );
}
