"""Structured streaming-event tracker for the new Chat UX.

Adds typed events on top of the existing flat stream — old `stream_delta` events
still flow for the legacy Kanban UI, while the new Next.js frontend reads:

- `planner_started`  — first agent begins, includes the user prompt
- `subagent_started` — orchestrator delegates to a Tier 2/3 agent
- `subagent_delta`   — text chunk from a sub-agent (tagged with sub-agent id)
- `subagent_finished`— sub-agent returned, includes its parsed findings (if any)
- `artifact_chunk`   — markdown block of the final artifact, may contain
                       citation refs like `[A]` (agent letter) or `[F3]` (finding id)
- `artifact_complete`— final artifact done; carries suggested_actions

The tracker is intentionally simple: it watches the AgentUpdatedStreamEvent
transitions, assigns each sub-agent a stable letter (A, B, C...), and routes
text deltas to the current sub-agent's bucket.

Finding extraction parses a structured JSON block from the agent output if
present (`<<<FINDINGS_JSON>>>...<<<END_FINDINGS_JSON>>>`); writers can opt
into this when they're ready.
"""

from __future__ import annotations

import json
import re
import string
import time
import uuid
from typing import Any, Awaitable, Callable


_FINDINGS_RE = re.compile(
    r"<<<FINDINGS_JSON>>>(.*?)<<<END_FINDINGS_JSON>>>", re.DOTALL
)
_SUGGESTED_RE = re.compile(
    r"<<<SUGGESTED_ACTIONS>>>(.*?)<<<END_SUGGESTED_ACTIONS>>>", re.DOTALL
)
_CITATION_RE = re.compile(r"\[([A-Z]|F\d+)\]")


class StreamTracker:
    """Track sub-agent boundaries and emit structured events.

    Pair one tracker with one `_run_agent_stream` call. It piggybacks on
    the existing `_ws_send` callback so it co-exists with the legacy
    events without rewriting the streaming loop.
    """

    def __init__(self, send: Callable[[dict], Awaitable[None]], user_prompt: str = ""):
        self._send = send
        self._user_prompt = user_prompt
        self._letters = iter(string.ascii_uppercase)
        self._by_name: dict[str, dict] = {}  # agent_name → {id, letter, text}
        self._current_id: str | None = None  # the active sub-agent id
        self._planner_emitted = False
        self._planner_id: str | None = None
        self._started_at = time.time()

    # ── public API ────────────────────────────────────────────────────

    async def planner_started(self, planner_name: str) -> None:
        """Emit once at the start of the stream — the planner reads the prompt."""
        if self._planner_emitted:
            return
        self._planner_emitted = True
        self._planner_id = self._new_id()
        await self._send({
            "type": "planner_started",
            "id": self._planner_id,
            "name": planner_name,
            "prompt": self._user_prompt,
        })

    async def on_agent_switch(self, new_agent_name: str) -> None:
        """Called when AgentUpdatedStreamEvent fires for a new agent."""
        # First-ever switch is the planner.
        if not self._planner_emitted:
            await self.planner_started(new_agent_name)
            self._current_id = self._planner_id
            return

        # Re-entering an agent we've seen → just switch the current_id back.
        existing = self._by_name.get(new_agent_name)
        if existing:
            self._current_id = existing["id"]
            return

        # New sub-agent.
        letter = next(self._letters, "?")
        sub_id = self._new_id()
        self._by_name[new_agent_name] = {
            "id": sub_id,
            "letter": letter,
            "name": new_agent_name,
            "text": "",
        }
        self._current_id = sub_id
        await self._send({
            "type": "subagent_started",
            "id": sub_id,
            "letter": letter,
            "name": new_agent_name,
            "parent_id": self._planner_id,
        })

    async def on_delta(self, delta: str) -> None:
        """Route a text delta to whichever agent is currently active."""
        if not self._current_id:
            return
        # Find the agent record by current id.
        agent = self._find_by_id(self._current_id)
        if agent is None:
            # Planner deltas — emit as planner_delta (frontend can show or ignore).
            await self._send({
                "type": "subagent_delta",
                "id": self._current_id,
                "delta": delta,
                "is_planner": True,
            })
            return
        agent["text"] += delta
        await self._send({
            "type": "subagent_delta",
            "id": self._current_id,
            "delta": delta,
        })

    async def finish_open_subagents(self) -> None:
        """At stream end, close every sub-agent we started. Parse findings if present."""
        for agent in self._by_name.values():
            findings = self._extract_findings(agent["text"])
            await self._send({
                "type": "subagent_finished",
                "id": agent["id"],
                "letter": agent["letter"],
                "name": agent["name"],
                "findings": findings,
            })

    async def emit_artifact(self, full_output: str) -> None:
        """Emit the artifact in one chunk + a `complete` envelope.

        Future work: split into incremental artifact_chunks during generation.
        For v1 we emit a single chunk after the run finishes — the frontend
        still gets typed events to render with citation chips.
        """
        citations = sorted(set(_CITATION_RE.findall(full_output)))
        suggested = self._extract_suggested_actions(full_output)

        await self._send({
            "type": "artifact_chunk",
            "markdown": full_output,
            "citation_refs": citations,
        })
        await self._send({
            "type": "artifact_complete",
            "suggested_actions": suggested,
            "citation_refs": citations,
            "elapsed_seconds": round(time.time() - self._started_at, 2),
        })

    # ── helpers ──────────────────────────────────────────────────────

    def _new_id(self) -> str:
        return uuid.uuid4().hex[:12]

    def _find_by_id(self, id_: str) -> dict | None:
        for a in self._by_name.values():
            if a["id"] == id_:
                return a
        return None

    @staticmethod
    def _extract_findings(text: str) -> list[dict]:
        match = _FINDINGS_RE.search(text)
        if not match:
            return []
        try:
            data = json.loads(match.group(1).strip())
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "findings" in data:
                return data["findings"]
        except json.JSONDecodeError:
            pass
        return []

    @staticmethod
    def _extract_suggested_actions(text: str) -> list[dict]:
        match = _SUGGESTED_RE.search(text)
        if not match:
            return []
        try:
            data = json.loads(match.group(1).strip())
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "actions" in data:
                return data["actions"]
        except json.JSONDecodeError:
            pass
        return []
