# Sourcy Marketing — Frontend

Next.js 14 (App Router) frontend for the Marketing agent. Talks to the FastAPI
backend over REST (`/api/v2/*`) and WebSocket (`/ws/{ticket_id}`).

## Local dev

```bash
# 1. Backend (in repo root)
DEV_MODE=1 .venv/bin/python main.py    # listens on :8000

# 2. Frontend (this directory)
npm install
npm run dev                            # listens on :3000
```

Open <http://localhost:3000>. The Next dev server rewrites `/api/v2/*` and `/ws/*`
to `http://localhost:8000`, so cookies and websocket session auth flow through.

If `personas/sourcy.json` or `design-systems/sourcy.json` are missing, the
landing path is `/memory/setup` (4-step wizard).

## Tabs

- `/home` — Sourcy dashboard. "Refresh dashboard" opens a new chat session
  pre-seeded with the all-API analysis prompt.
- `/chat` — Sessions list, planner card, sub-agent steps rail, artifact canvas
  with citation chips, ActionBar with 3 generation modes (auto / single / combine).
- `/library` — All generated content. Tabs for blogs / LPs / ads / case studies /
  images, filterable by name.
- `/memory` — Persona editor, design system editor, logo upload, knowledge view,
  API connection status.
- `/home/tickets` — Embedded legacy kanban for ticket management.

## Architecture notes

- `lib/store.ts` — Zustand store keyed by `sessionId`. Handles structured streaming
  events from `app/streaming_events.py` (planner_started, subagent_*, artifact_*).
- `lib/useAgentStream.ts` — WebSocket client per session.
- Citations: artifact markdown contains `[A]` / `[F3]` tokens. The
  `ArtifactCanvas` rewrites them into clickable chips that scroll the Steps
  rail to the matching sub-agent.
