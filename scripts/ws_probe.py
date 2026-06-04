import asyncio
import json
import sys

import websockets


async def main(ticket_id: str, message: str) -> int:
    uri = f"ws://localhost:8000/ws/{ticket_id}"
    async with websockets.connect(uri, open_timeout=10, close_timeout=5) as ws:
        await ws.send(json.dumps({"message": message, "user": "Codex"}))
        for _ in range(30):
            try:
                payload = await asyncio.wait_for(ws.recv(), timeout=5)
            except asyncio.TimeoutError:
                print("TIMEOUT_WAITING_FOR_MESSAGE")
                return 2
            print(payload)
            lowered = payload.lower()
            if "stream_end" in lowered or "run_finished" in lowered or '"type":"error"' in lowered:
                return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(sys.argv[1], sys.argv[2])))
