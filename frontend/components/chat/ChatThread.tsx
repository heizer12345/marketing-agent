"use client";

import type { ChatSession, ChatTurn } from "@/lib/types";
import { ArtifactCanvas } from "@/components/chat/ArtifactCanvas";
import { ChatMarkdown } from "@/components/chat/ChatMarkdown";

function UserBubble({ text }: { text: string }) {
  return (
    <div className="flex justify-end">
      <div
        className="max-w-[92%] rounded-2xl rounded-br-md px-4 py-3 text-[13px] leading-relaxed text-ink"
        style={{ background: "var(--cyan-soft)", border: "1px solid rgba(6, 182, 212, 0.25)" }}
      >
        <div className="whitespace-pre-wrap">{text}</div>
      </div>
    </div>
  );
}

function ThinkingCard({ name, activity }: { name: string; activity?: string }) {
  return (
    <div className="flex gap-3 items-start px-1">
      <div
        className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-white text-xs font-bold"
        style={{ background: "linear-gradient(135deg, #06B6D4 0%, #0891B2 100%)" }}
      >
        AI
      </div>
      <div className="rounded-2xl rounded-bl-md px-4 py-3 text-[13px] text-muted border"
           style={{ background: "white", borderColor: "var(--border)" }}>
        <span className="status-dot running inline-block mr-2 align-middle" />
        {activity || `Working${name ? ` — ${name}` : ""}…`}
      </div>
    </div>
  );
}

function PastTurn({ turn }: { turn: ChatTurn }) {
  return (
    <div className="space-y-4">
      <UserBubble text={turn.userPrompt} />
      {turn.assistantMarkdown && (
        <div className="flex gap-3 items-start">
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-white text-xs font-bold"
            style={{ background: "linear-gradient(135deg, #0F172A 0%, #1E293B 100%)" }}
          >
            AI
          </div>
          <div
            className="flex-1 min-w-0 rounded-2xl rounded-bl-md px-4 py-3 border prose-sourcy text-[13px]"
            style={{ background: "white", borderColor: "var(--border)" }}
          >
            <ChatMarkdown markdown={turn.assistantMarkdown} />
          </div>
        </div>
      )}
    </div>
  );
}

function CurrentTurn({ session }: { session: ChatSession }) {
  const prompt = session.planner?.prompt?.trim();
  const hasAnswer = !!session.artifact.markdown;
  const isRunning = session.status === "running";

  if (!prompt && !hasAnswer && !isRunning) return null;

  return (
    <div className="space-y-4">
      {prompt && <UserBubble text={prompt} />}

      {hasAnswer ? (
        <div className="flex gap-3 items-start">
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-white text-xs font-bold"
            style={{ background: "linear-gradient(135deg, #0F172A 0%, #1E293B 100%)" }}
          >
            AI
          </div>
          <div className="flex-1 min-w-0">
            <ArtifactCanvas
              artifact={session.artifact}
              subagents={session.subagents}
              agentName={session.planner?.name}
              activity={isRunning ? session.planner?.activity : undefined}
              embedded
            />
          </div>
        </div>
      ) : isRunning ? (
        <ThinkingCard name={session.planner?.name || "Assistant"} activity={session.planner?.activity} />
      ) : null}
    </div>
  );
}

export function ChatThread({ session }: { session: ChatSession }) {
  const turns = session.turns ?? [];

  return (
    <div className="space-y-6 max-w-3xl">
      {turns.map((turn) => (
        <PastTurn key={turn.id} turn={turn} />
      ))}
      <CurrentTurn session={session} />
    </div>
  );
}
