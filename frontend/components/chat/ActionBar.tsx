"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useChatStore } from "@/lib/store";
import type { ChatSession, SuggestedAction, SubAgent } from "@/lib/types";

/** Bottom-of-artifact action bar.
 *
 * Three generation modes:
 * 1) Auto suggestions  — buttons emitted by synthesis
 * 2) Manual combine    — uses checkboxed sub-agents from the Steps rail
 * 3) Single-agent      — same combine flow but with one agent selected
 *
 * Each click POSTs to /api/v2/dispatch/{action_id} → seed_prompt →
 * spawn NEW chat session → autostream.
 */
export function ActionBar({ session }: { session: ChatSession }) {
  const selected = useChatStore((s) => s.selectedSubagentIds[session.id] || {});
  const clearSelected = useChatStore((s) => s.clearSelected);
  const newSession = useChatStore((s) => s.newSession);
  const selectedSubs = Object.entries(selected).filter(([, v]) => v).map(([id]) => id);
  const selectedAgents = session.subagents.filter((a) => selectedSubs.includes(a.id));

  const resolveFindings = (findingRefs: string[]): any[] => {
    if (!findingRefs.length) return [];
    const all: any[] = [];
    session.subagents.forEach((a) => a.findings.forEach((f) => all.push(f)));
    return all.filter((f) => findingRefs.includes(f.finding_id));
  };

  const [busy, setBusy] = useState<string | null>(null);

  const dispatch = async (
    action_id: string,
    findings: any[],
    agent_refs: string[],
    title: string,
    extra: Partial<{ channel: string; subject: string; customer_name: string }> = {},
  ) => {
    setBusy(action_id);
    try {
      const r = await api.dispatch(action_id, {
        selected_findings: findings,
        selected_agents: agent_refs,
        ticket_id: session.ticket_id,
        ...extra,
      });
      if (r.ok && r.seed_prompt) newSession(title, { seedPrompt: r.seed_prompt });
    } finally { setBusy(null); }
  };

  const dispatchAuto = (a: SuggestedAction) => dispatch(
    a.action_id,
    resolveFindings(a.finding_refs || []),
    a.agent_refs || [],
    a.label,
  );

  const dispatchCombine = (kind: string, label: string) => {
    const findings: any[] = [];
    selectedAgents.forEach((a) => a.findings.forEach((f) => findings.push(f)));
    dispatch(kind, findings, selectedAgents.map((a) => a.letter), label).then(() => clearSelected(session.id));
  };

  const showAuto = session.artifact.complete && session.artifact.suggested_actions.length > 0;
  const showCombine = selectedAgents.length > 0;

  if (!showAuto && !showCombine) return null;

  return (
    <div className="border-t" style={{ background: "white", borderColor: "var(--border)" }}>
      {showAuto && (
        <div className="px-6 py-3 border-b" style={{ borderColor: "var(--border)" }}>
          <div className="flex items-center gap-3 flex-wrap">
            <div>
              <div className="label">Next moves</div>
              <div className="text-[11px] text-muted mt-0.5">Suggested by what the agents just found</div>
            </div>
            <div className="flex flex-wrap gap-2">
              {session.artifact.suggested_actions.map((a) => (
                <button
                  key={a.action_id}
                  className="btn-accent text-[12.5px]"
                  onClick={() => dispatchAuto(a)}
                  disabled={busy === a.action_id}
                  title={`Sources: ${(a.agent_refs || []).join(", ") || "all agents"} · Findings: ${(a.finding_refs || []).join(", ") || "all"}`}
                >
                  {busy === a.action_id ? "Starting…" : a.label}
                  {(a.agent_refs || []).map((r) => <span key={r} className="chip text-[10px] py-0 ml-1" style={{background:"rgba(255,255,255,0.2)",color:"#fff",borderColor:"rgba(255,255,255,0.3)"}}>{r}</span>)}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
      {showCombine && (
        <div className="px-6 py-3" style={{ background: "linear-gradient(180deg, rgba(6,182,212,0.04), transparent)" }}>
          <div className="flex items-center gap-3 flex-wrap">
            <div>
              <div className="label">Generate from selected agents</div>
              <SelectedSummary agents={selectedAgents} />
            </div>
            <div className="ml-auto flex flex-wrap gap-2">
              <button className="btn-primary" disabled={!!busy} onClick={() => dispatchCombine("gen-ad", "Generate ad variants")}>
                Ad variants
              </button>
              <button className="btn-secondary" disabled={!!busy} onClick={() => dispatchCombine("gen-blog", "Generate blog post")}>
                Blog post
              </button>
              <button className="btn-secondary" disabled={!!busy} onClick={() => dispatchCombine("gen-landing-page", "Generate landing page")}>
                Landing page
              </button>
              <button className="btn-secondary" disabled={!!busy} onClick={() => dispatchCombine("gen-case-study", "Generate case study")}>
                Case study
              </button>
              <button className="btn-ghost" onClick={() => clearSelected(session.id)}>Clear</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function SelectedSummary({ agents }: { agents: SubAgent[] }) {
  if (!agents.length) return null;
  const findingCount = agents.reduce((acc, a) => acc + a.findings.length, 0);
  return (
    <div className="text-[11px] text-muted mt-0.5">
      Using {agents.length} agent{agents.length === 1 ? "" : "s"}
      {findingCount > 0 && ` · ${findingCount} finding${findingCount === 1 ? "" : "s"}`}
    </div>
  );
}
