"""Live test runner — creates tickets, sends queries via WebSocket, waits for completion."""
import asyncio
import json
import time
import httpx
import websockets

BASE = "http://localhost:8000"
WS_BASE = "ws://localhost:8000"

TESTS = [
    {"id": 1, "user": "Afrah", "query": "How many sessions did our website have this week?",
     "expect": "simple_answer", "timeout": 60},
    {"id": 2, "user": "Nadia", "query": "What are our top 10 organic keywords right now?",
     "expect": "keywords_table", "timeout": 90},
    {"id": 3, "user": "Nadia", "query": "Can you audit the SEO of sourcy.ai/about?",
     "expect": "analysis_text", "timeout": 480},
    {"id": 4, "user": "Afrah", "query": "Write a blog post about how to source eco-friendly packaging from Vietnam.",
     "expect": "html_artifact", "timeout": 600},
    {"id": 5, "user": "Nadia", "query": "Create a landing page for our Easy Sourcing service targeting US e-commerce brands.",
     "expect": "html_artifact", "timeout": 600},
    {"id": 6, "user": "Afrah", "query": "How's our website doing overall? I want keywords, traffic, and recommendations — around 100 keywords please.",
     "expect": "html_artifact", "timeout": 600},
    {"id": 7, "user": "Nadia", "query": "Rewrite our about page to target 'China sourcing service' better.",
     "expect": "pending_review", "timeout": 1200},
    {"id": 8, "user": "Afrah", "query": "Add FAQ schema to our main service pages — sourcing, easysourcing, products.",
     "expect": "pending_review", "timeout": 900},
    {"id": 9, "user": "Nadia", "query": "Improve SEO/GEO/AEO of our top 20 blogs — give me proposed changes to review.",
     "expect": "pending_review", "timeout": 1500},
    {"id": 10, "user": "Afrah", "query": "Let's do a full SEO/AEO/GEO overhaul of sourcy.ai — top 30 pages across all types. I want schemas, rewrites, llms.txt, and fix alt text on images too.",
     "expect": "pending_review", "timeout": 1500},
]

REGRESSIONS = [
    {"id": "R1", "user": "Afrah", "query": "How are our Meta Ads performing this week?",
     "must_not_contain": "website_overhaul", "timeout": 120},
    {"id": "R2", "user": "Nadia", "query": "Write a blog about AI sourcing tools.",
     "must_not_contain": "website_overhaul", "timeout": 300},
    {"id": "R3", "user": "Afrah", "query": "Can you audit sourcy.ai SEO? Just an audit, no changes.",
     "must_not_contain": "website_overhaul", "timeout": 180},
    {"id": "R4", "user": "Eugene", "query": "What is GEO and how does it differ from SEO?",
     "must_not_contain": "website_overhaul", "timeout": 60},
    {"id": "R5", "user": "Eugene", "query": "Generate a report of last month's performance.",
     "must_not_contain": "website_overhaul", "timeout": 300},
]


async def create_ticket(client, title, created_by):
    r = client.post(f"{BASE}/api/tickets", json={"title": title, "created_by": created_by})
    return r.json()["id"]


async def run_via_websocket(ticket_id, query, timeout_s):
    """Send query over WS and collect all events until done/error/timeout."""
    full_text = []
    artifacts = []
    final_status = "unknown"
    start = time.time()

    uri = f"{WS_BASE}/ws/{ticket_id}"
    try:
        async with websockets.connect(uri, ping_interval=30, ping_timeout=60) as ws:
            # Send user message (server expects {"message": "..."})
            await ws.send(json.dumps({"message": query}))

            while True:
                elapsed = time.time() - start
                if elapsed > timeout_s:
                    final_status = "timeout"
                    break

                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=30)
                except asyncio.TimeoutError:
                    elapsed = time.time() - start
                    print(f"  ... still waiting ({elapsed:.0f}s elapsed)", flush=True)
                    continue

                evt = json.loads(raw)
                etype = evt.get("type", "")

                if etype == "token":
                    full_text.append(evt.get("data", ""))
                elif etype == "message":
                    d = evt.get("data", {})
                    if isinstance(d, dict):
                        full_text.append(d.get("content", ""))
                    elif isinstance(d, str):
                        full_text.append(d)
                elif etype == "artifact":
                    artifacts.append(evt.get("data", {}))
                    print(f"  [artifact] {evt.get('data', {}).get('file_path', str(evt.get('data', {})))[:80]}", flush=True)
                elif etype == "status":
                    s = evt.get("data", {})
                    st = s if isinstance(s, str) else s.get("status", "")
                    print(f"  [status] {st}", flush=True)
                    if st in ("completed", "pending_review", "error"):
                        final_status = st
                        break
                elif etype in ("done", "stream_end"):
                    # stream_end = normal completion; done = legacy
                    final_status = "completed"
                    for url in (evt.get("artifact_urls") or []):
                        artifacts.append({"file_path": url})
                    break
                elif etype == "error":
                    final_status = "error"
                    full_text.append(f"[ERROR] {evt.get('data', '')}")
                    break

    except Exception as e:
        final_status = f"ws_error: {e}"

    return {
        "final_status": final_status,
        "elapsed_s": round(time.time() - start, 1),
        "response_preview": "".join(full_text)[:500],
        "artifact_count": len(artifacts),
        "artifacts": [a.get("file_path", str(a))[:80] for a in artifacts],
    }


async def check_ticket_status(client, ticket_id):
    try:
        r = client.get(f"{BASE}/api/tickets/{ticket_id}", timeout=10)
        if r.status_code != 200 or not r.text.strip():
            return {"status": "error", "msg_count": 0, "artifact_count": 0, "last_msg": f"HTTP {r.status_code}"}
        d = r.json()
    except Exception as e:
        return {"status": "error", "msg_count": 0, "artifact_count": 0, "last_msg": str(e)[:100]}
    return {
        "status": d.get("status"),
        "msg_count": len(d.get("messages", [])),
        "artifact_count": len(d.get("artifacts", [])),
        "last_msg": (d.get("messages") or [{}])[-1].get("content", "")[:300],
    }


def grade(test, result, db_info):
    expect = test.get("expect", "")
    status = db_info["status"]
    passed = False
    notes = []

    if expect == "simple_answer":
        passed = status == "completed" and db_info["msg_count"] >= 2
    elif expect in ("html_artifact", "md_artifact"):
        passed = status == "completed" and db_info["artifact_count"] >= 1
    elif expect == "keywords_table":
        passed = status == "completed" and db_info["msg_count"] >= 2
    elif expect == "analysis_text":
        # Audit/analysis that produces structured text (no artifact required)
        passed = status == "completed" and db_info["msg_count"] >= 2 and "timed out" not in db_info["last_msg"].lower()
    elif expect == "pending_review":
        passed = status == "pending_review"

    notes.append(f"db_status={status}")
    notes.append(f"msgs={db_info['msg_count']}")
    notes.append(f"artifacts={db_info['artifact_count']}")
    notes.append(f"elapsed={result['elapsed_s']}s")
    return "PASS" if passed else "FAIL", " | ".join(notes)


async def run_all():
    results = []

    with httpx.Client(timeout=30) as client:
        for test in TESTS:
            tid = test["id"]
            print(f"\n{'='*60}", flush=True)
            print(f"TEST {tid} — {test['user']}: {test['query'][:70]}", flush=True)
            print(f"{'='*60}", flush=True)

            ticket_id = await create_ticket(client, f"[TEST{tid}] {test['query'][:60]}", test["user"])
            print(f"  Ticket: {ticket_id}", flush=True)

            result = await run_via_websocket(ticket_id, test["query"], test["timeout"])
            print(f"  WS done: {result['final_status']} in {result['elapsed_s']}s", flush=True)
            if result["response_preview"]:
                print(f"  Preview: {result['response_preview'][:250]}", flush=True)

            # Always poll until ticket is done — avoid grading while agent is still running.
            # Agent keeps running in background even after WS disconnect/timeout.
            # Max wait: 600s for complex tasks, 15s for simple.
            is_simple = test.get("expect") == "simple_answer"
            # Scale polling budget to test complexity: simple=10s, pending_review=1200s, others=600s
            if is_simple:
                max_polls = 1
            elif test.get("expect") == "pending_review":
                max_polls = 120  # 120 × 10s = 1200s
            else:
                max_polls = 60   # 60 × 10s = 600s
            await asyncio.sleep(3)
            db_info = await check_ticket_status(client, ticket_id)
            if db_info["status"] == "in_progress":
                label = "WS timeout" if result["final_status"] == "timeout" else "still running"
                print(f"  Agent still running ({label}). Polling up to {max_polls * 10}s...", flush=True)
                for _wait in range(max_polls):
                    await asyncio.sleep(10)
                    db_info = await check_ticket_status(client, ticket_id)
                    print(f"  ... {(_wait+1)*10}s: status={db_info['status']} msgs={db_info['msg_count']} artifacts={db_info['artifact_count']}", flush=True)
                    if db_info["status"] in ("completed", "pending_review", "error"):
                        break

            verdict, notes = grade(test, result, db_info)
            print(f"  [{verdict}] {notes}", flush=True)
            if db_info["last_msg"]:
                print(f"  Last msg: {db_info['last_msg'][:200]}", flush=True)

            results.append({
                "test": tid,
                "user": test["user"],
                "query": test["query"][:70],
                "ticket_id": ticket_id,
                "verdict": verdict,
                "notes": notes,
                "ws_status": result["final_status"],
                "db_status": db_info["status"],
                "elapsed_s": result["elapsed_s"],
                "msg_count": db_info["msg_count"],
                "artifact_count": db_info["artifact_count"],
            })

        # Regression tests
        print(f"\n{'='*60}", flush=True)
        print("REGRESSION TESTS (must NOT route to website_overhaul)", flush=True)
        print(f"{'='*60}", flush=True)
        reg_results = []
        for reg in REGRESSIONS:
            rid = reg["id"]
            print(f"\n  REG {rid} — {reg['user']}: {reg['query'][:60]}", flush=True)
            ticket_id = await create_ticket(client, f"[{rid}] {reg['query'][:50]}", reg["user"])
            result = await run_via_websocket(ticket_id, reg["query"], reg["timeout"])
            await asyncio.sleep(2)
            db_info = await check_ticket_status(client, ticket_id)
            # Pass if completed (not pending_review, not error)
            passed = db_info["status"] == "completed"
            verdict = "PASS" if passed else "FAIL"
            print(f"  [{verdict}] status={db_info['status']} elapsed={result['elapsed_s']}s", flush=True)
            reg_results.append({"id": rid, "verdict": verdict, "status": db_info["status"],
                                 "elapsed_s": result["elapsed_s"]})

    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    passed_main = sum(1 for r in results if r["verdict"] == "PASS")
    passed_reg = sum(1 for r in reg_results if r["verdict"] == "PASS")
    print(f"Main tests:       {passed_main}/{len(results)} PASS")
    print(f"Regression tests: {passed_reg}/{len(reg_results)} PASS")
    print()
    for r in results:
        icon = "✓" if r["verdict"] == "PASS" else "✗"
        print(f"  {icon} Test {r['test']:2d} [{r['user']:6s}] {r['verdict']} — {r['notes']}")
    print()
    for r in reg_results:
        icon = "✓" if r["verdict"] == "PASS" else "✗"
        print(f"  {icon} {r['id']} {r['verdict']} — status={r['status']} elapsed={r['elapsed_s']}s")

    all_results = {"main": results, "regressions": reg_results}
    with open("test_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved to test_results.json")
    return all_results


if __name__ == "__main__":
    asyncio.run(run_all())
