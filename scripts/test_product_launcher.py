"""Intensive product-launch generation test.

Scenario: Sourcy is launching "Sourcy Launcher" — an AI dedicated agent that
fires off specialist sub-agents to source verified suppliers, gather real
quotes for product comparison, and run a first round of price negotiation.
The use case is brand aggregators launching HUNDREDS of products at once.

This script creates one chat ticket per content piece and submits a prompt
over the production WebSocket — exactly like a real user. The result:
every output appears as a chat session in the UI (left rail), with its
artifact + image linkage live in the SessionArtifacts panel.

Pieces generated (in parallel):
  1. Blog post — how AI agents launch 100 products
  2. Landing page — Sourcy Launcher product page
  3. Ad variants (Meta) — 3 ad creatives
  4. Ad variants (Instagram Story) — 3 vertical creatives
  5. Case study — brand aggregator who launched 47 SKUs
"""

import asyncio
import json
import re
import sys
import time
from pathlib import Path

import httpx
import websockets

sys.path.insert(0, str(Path(__file__).parent.parent))

BASE = "http://localhost:8000"
WS = "ws://localhost:8000"


PIECES = [
    {
        "title": "Blog: AI agents launching 100 products",
        "prompt": """Write a 600-word blog post for sourcy.ai about how brand aggregators can launch 100+ new products in a quarter using Sourcy Launcher — an AI dedicated agent that dispatches specialist sub-agents to source verified suppliers, return real quotes for side-by-side comparison, and negotiate the first round of pricing. Audience: PE-backed brand aggregator operators ($30M+ portfolio revenue). State the marketing principle used in the metadata.""",
    },
    {
        "title": "Landing page: Sourcy Launcher",
        "prompt": """Write a landing page for sourcy.ai/launcher — our new product "Sourcy Launcher". One-line value prop: an AI dedicated agent that launches dozens of products at once by dispatching sourcing sub-agents to fetch real supplier quotes (so you can compare side-by-side) and run a first round of negotiation. Target audience: brand aggregators with 5+ portfolio brands. Use the Hormozi value-stack principle. Name the LP blocks (from design system) you chose.""",
    },
    {
        "title": "Ad variants (Meta): Sourcy Launcher",
        "prompt": """Generate 3 Meta ad variants for Sourcy Launcher (subject: AI agent that launches 100 products by dispatching sub-agents to fetch supplier quotes and negotiate).

Selected findings:
[
  {"finding_id":"F1","claim":"73% of brand aggregators say sourcing rebuild is their #1 launch bottleneck across portfolio brands","evidence":"Sourcy customer interviews 2026 Q1","confidence":"High","tags":["pain_point","brand_aggregator"]},
  {"finding_id":"F2","claim":"Sourcy Launcher returns verified-supplier quotes in 3 hours per product, and a side-by-side comparison + negotiated first-round price in 24 hours","evidence":"Internal benchmark vs Alibaba 14-day RFQ cycle","confidence":"High","tags":["winning_angle","speed"]}
]

Channel: meta.""",
    },
    {
        "title": "Ad variants (IG Story): Sourcy Launcher",
        "prompt": """Generate 3 Instagram Story ad variants for Sourcy Launcher (portrait aspect), same product as above. Target: brand operators 28-45 scrolling between meetings.

Selected findings:
[
  {"finding_id":"F1","claim":"Sourcy Launcher = autopilot for 100+ SKU launches: dispatch agents, get quotes, negotiate","evidence":"Product description","confidence":"High","tags":["winning_angle","autopilot"]},
  {"finding_id":"F2","claim":"Brand aggregators using Sourcy save 60% of procurement time per SKU","evidence":"Internal Q1 metric","confidence":"Medium","tags":["winning_angle","time_savings"]}
]

Channel: instagram_story.""",
    },
    {
        "title": "Case study: 47 SKUs in one quarter",
        "prompt": """Write a case study using Before / What we did / After structure. Customer: confidential US brand aggregator (anonymous, mid-market), 12 portfolio brands. Launched 47 new SKUs in Q1 using Sourcy Launcher AI dispatcher.

Selected findings:
[
  {"finding_id":"F1","claim":"Aggregator cut per-SKU sourcing cycle from 21 days to 4 days using Sourcy Launcher's AI dispatcher","evidence":"Customer share","confidence":"High","tags":["customer_outcome","speed"]},
  {"finding_id":"F2","claim":"Negotiated first-round prices averaged 12% lower than initial supplier quotes thanks to side-by-side comparison","evidence":"Customer Q1 PO data","confidence":"Medium","tags":["customer_outcome","savings"]}
]

Generate one landscape hero image.""",
    },
]


async def run_piece(piece: dict, idx: int) -> dict:
    title = piece["title"]
    prompt = piece["prompt"]
    started = time.time()

    # 1. Create ticket
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BASE}/api/tickets", json={"title": title, "created_by": "Eugene"})
        ticket_id = r.json()["id"]
    short = ticket_id[:8]
    print(f"  [{idx+1}] {short} · {title[:55]} · ticket created")

    # 2. WebSocket
    url = f"{WS}/ws/{ticket_id}"
    sub_agents_seen = []
    stream_chars = 0
    artifact_chars = 0
    artifacts: list[str] = []
    error: str | None = None
    last_status: str = "queued"

    try:
        async with websockets.connect(url, max_size=None) as ws:
            await ws.send(json.dumps({"message": prompt, "user": "Eugene"}))
            print(f"  [{idx+1}] {short} · prompt sent ({len(prompt)} chars)")

            deadline = time.time() + 900  # 15 min cap per piece
            while time.time() < deadline:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=60)
                except asyncio.TimeoutError:
                    print(f"  [{idx+1}] {short} · ⚠ idle 60s, continuing")
                    continue
                try:
                    ev = json.loads(msg)
                except Exception:
                    continue
                t = ev.get("type", "?")
                if t == "subagent_started":
                    sub_agents_seen.append(ev.get("name"))
                    last_status = f"agent: {ev.get('name')}"
                elif t == "stream_delta":
                    stream_chars += len(ev.get("data", ""))
                elif t == "tool_status":
                    last_status = ev.get("label", "")[:50]
                elif t == "artifact_chunk":
                    artifact_chars = len(ev.get("markdown", ""))
                elif t == "stream_end":
                    last_status = "complete"
                    break
                elif t == "error":
                    error = ev.get("message") or ev.get("data") or "unknown"
                    last_status = f"error: {error[:60]}"
                    break
    except Exception as e:
        error = str(e)[:200]

    # 3. Fetch the linked artifacts from the new endpoint
    async with httpx.AsyncClient() as c:
        try:
            r = await c.get(f"{BASE}/api/v2/sessions/{ticket_id}/artifacts")
            data = r.json()
            artifacts = [a["url"] for a in data.get("artifacts", [])]
        except Exception:
            pass

    elapsed = time.time() - started
    print(f"  [{idx+1}] {short} · {last_status} · {elapsed:.0f}s · {len(artifacts)} artifacts")
    return {
        "idx": idx, "ticket_id": ticket_id, "title": title,
        "elapsed_s": round(elapsed, 1),
        "sub_agents": sub_agents_seen,
        "stream_chars": stream_chars,
        "artifact_chars": artifact_chars,
        "artifacts": artifacts,
        "error": error,
    }


async def main() -> int:
    print("┌" + "─" * 76 + "┐")
    print("│  PRODUCT LAUNCHER INTENSIVE TEST                                             │")
    print("│  Sourcy Launcher: AI dedicated agent for 100-SKU brand-aggregator launches   │")
    print("│  Generating 5 content pieces in parallel — watch them in /chat               │")
    print("└" + "─" * 76 + "┘\n")

    print(f"Pieces ({len(PIECES)}):")
    for i, p in enumerate(PIECES):
        print(f"  {i+1}. {p['title']}")
    print()
    print("→ Spinning up all sessions concurrently. Open http://localhost:3000/chat")
    print("  to watch them stream live. Each gets its own chat session in the left rail.\n")

    started = time.time()
    results = await asyncio.gather(*(run_piece(p, i) for i, p in enumerate(PIECES)))
    total = time.time() - started

    print()
    print("═" * 78)
    print(f"  SUMMARY — total wall time {total:.0f}s ({total/60:.1f} min)")
    print("═" * 78)
    for r in results:
        mark = "✓" if not r["error"] else "✗"
        print(f"\n{mark} [{r['ticket_id'][:8]}] {r['title']}")
        print(f"    elapsed:      {r['elapsed_s']}s")
        print(f"    agents seen:  {len(r['sub_agents'])}  {r['sub_agents'][:5]}")
        print(f"    stream chars: {r['stream_chars']:,}")
        print(f"    artifact:     {r['artifact_chars']:,} chars")
        print(f"    saved files:  {len(r['artifacts'])}")
        for a in r["artifacts"]:
            print(f"      · {a}")
        if r["error"]:
            print(f"    error:        {r['error']}")

    passed = sum(1 for r in results if not r["error"])
    print(f"\n  {passed}/{len(results)} pieces completed cleanly.\n")
    print("  Open http://localhost:3000/chat — your sessions are in the left rail.")
    print("  Open http://localhost:3000/library — every artifact tagged with its source chat.")
    return 0 if passed == len(results) else 2


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
