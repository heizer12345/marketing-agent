// Typed mirror of the structured streaming events emitted by
// app/streaming_events.py. Keep these in sync.

export type Finding = {
  finding_id?: string;
  claim?: string;
  evidence?: string;
  confidence?: "High" | "Medium" | "Low" | string;
  [k: string]: any;
};

export type SuggestedAction = {
  label: string;
  action_id: string;
  finding_refs?: string[];
  agent_refs?: string[];
};

export type SubAgent = {
  id: string;
  letter: string; // "A", "B", ...
  name: string;
  parent_id?: string;
  text: string;
  findings: Finding[];
  status: "pending" | "running" | "finished";
};

export type Planner = {
  id: string;
  name: string;
  prompt: string;
  text: string;
  activity?: string;  // latest tool_status label — shown as a live activity hint
};

export type Artifact = {
  markdown: string;
  citation_refs: string[];
  suggested_actions: SuggestedAction[];
  elapsed_seconds?: number;
  complete: boolean;
};

export type ChatSession = {
  id: string;
  ticket_id?: string;
  title: string;
  created_at: number;
  planner?: Planner;
  subagents: SubAgent[];
  artifact: Artifact;
  status: "idle" | "running" | "complete" | "error";
  error?: string;
  pendingSeedPrompt?: string;  // auto-submitted when the WebSocket opens
};

// Raw event shapes from the backend WebSocket.
export type WSEvent =
  | { type: "stream_start"; agent: string }
  | { type: "stream_end" }
  | { type: "stream_delta"; data: string }
  | { type: "agent_switch"; agent: string }
  | { type: "tool_status"; label: string; tool?: string }
  | { type: "tool_done"; label: string }
  | { type: "planner_started"; id: string; name: string; prompt: string }
  | { type: "subagent_started"; id: string; letter: string; name: string; parent_id?: string }
  | { type: "subagent_delta"; id: string; delta: string; is_planner?: boolean }
  | { type: "subagent_finished"; id: string; letter: string; name: string; findings: Finding[] }
  | { type: "artifact_chunk"; markdown: string; citation_refs: string[] }
  | { type: "artifact_complete"; suggested_actions: SuggestedAction[]; citation_refs: string[]; elapsed_seconds?: number }
  | { type: "error"; error_type?: string; message?: string; data?: string }
  | { type: string; [k: string]: any };

export type Persona = Record<string, any>;
export type DesignSystem = Record<string, any>;
export type MemoryState = {
  setup_complete: boolean;
  persona: Persona;
  design_system: DesignSystem;
  principles: Array<{ slug: string; name: string; summary?: string; [k: string]: any }>;
  winners: { ads: any[]; blogs: any[]; landing_pages: any[]; case_studies: any[] };
  api_status: Record<string, boolean>;
};
