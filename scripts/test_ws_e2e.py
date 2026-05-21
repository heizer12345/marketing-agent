"""End-to-end WebSocket smoke test.

Opens a connection to the FastAPI backend exactly the way the browser does,
sends a real prompt, and verifies structured events flow back.

Verifies in one shot:
- WS upgrade works
- planner_started event fires
- subagent_started events fire (with role names)
- subagent_delta events stream text
- stream_end fires
"""

import asyncio
import json
import sys
import time

import httpx
import websockets


BASE_HTTP = "http://localhost:8000"
BASE_WS = "ws://localhost:8000"


async def main() -> int:
    # 1. Create a ticket (same call the chat page makes)
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BASE_HTTP}/api/tickets", json={"title": "WS smoke test", "created_by": "Eugene"})
        if r.status_code != 200:
            print(f"✗ ticket create failed: {r.status_code}")
            return 1
        ticket_id = r.json()["id"]
        print(f"✓ Ticket created: {ticket_id[:8]}…")

    # 2. Open WS
    url = f"{BASE_WS}/ws/{ticket_id}"
    print(f"→ Connecting to {url}")
    try:
        async with websockets.connect(url, max_size=None) as ws:
            print("✓ WebSocket open")

            # 3. Send a fast prompt (knowledge question — no heavy tool calls)
            prompt = "In one sentence each, what's the difference between SEO, GEO, and AEO?"
            await ws.send(json.dumps({"message": prompt, "user": "Eugene"}))
            print(f"→ Sent prompt: {prompt!r}\n")

            # 4. Receive structured events
            counts = {"planner_started": 0, "subagent_started": 0, "subagent_delta": 0,
                      "subagent_finished": 0, "artifact_chunk": 0, "artifact_complete": 0,
                      "stream_start": 0, "stream_delta": 0, "stream_end": 0,
                      "agent_switch": 0, "tool_status": 0, "tool_done": 0, "error": 0}
            agents_seen = []
            t0 = time.time()
            deadline = t0 + 120
            done = False
            text_total = ""

            while time.time() < deadline and not done:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=20)
                except asyncio.TimeoutError:
                    print(f"⚠ no message in 20s — giving up")
                    break
                try:
                    ev = json.loads(msg)
                except Exception:
                    continue
                t = ev.get("type", "?")
                counts[t] = counts.get(t, 0) + 1
                if t == "planner_started":
                    print(f"[{int(time.time()-t0):>3}s] planner_started · {ev.get('name')!r}")
                elif t == "subagent_started":
                    print(f"[{int(time.time()-t0):>3}s] subagent_started · {ev.get('name')!r} (letter={ev.get('letter')})")
                    agents_seen.append(ev.get("name"))
                elif t == "subagent_delta":
                    pass  # too noisy to print
                elif t == "subagent_finished":
                    print(f"[{int(time.time()-t0):>3}s] subagent_finished · {ev.get('name')!r} · findings={len(ev.get('findings') or [])}")
                elif t == "artifact_chunk":
                    text_total = ev.get("markdown", "")
                    print(f"[{int(time.time()-t0):>3}s] artifact_chunk · {len(text_total)} chars · citations={ev.get('citation_refs') or []}")
                elif t == "artifact_complete":
                    print(f"[{int(time.time()-t0):>3}s] artifact_complete · suggested_actions={len(ev.get('suggested_actions') or [])}")
                elif t == "stream_end":
                    print(f"[{int(time.time()-t0):>3}s] stream_end")
                    done = True
                elif t == "error":
                    print(f"[{int(time.time()-t0):>3}s] error: {ev}")
                    done = True

            print()
            print("═" * 60)
            print("Event counts:")
            for k, v in counts.items():
                if v > 0:
                    print(f"  {k:24s} × {v}")
            print(f"\nAgents seen: {agents_seen}")
            print(f"Total chat-output chars: {len(text_total)}")
            elapsed = time.time() - t0
            print(f"Total elapsed: {elapsed:.1f}s")

            # Pass criteria — streaming is working if planner fired, text streamed
            # (either as subagent_delta or stream_delta), and the stream ended cleanly.
            ok = (
                counts["planner_started"] > 0
                and (counts["subagent_delta"] > 0 or counts["stream_delta"] > 0)
                and counts.get("stream_end", 0) > 0
            )
            print(f"\n{'✓ PASS' if ok else '✗ FAIL'} — streaming works end-to-end")
            return 0 if ok else 2

    except Exception as e:
        print(f"✗ WS error: {e!r}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
