const ticketId = process.argv[2];
const message = process.argv[3];

if (!ticketId || !message) {
  console.error("usage: node scripts/ws-probe.mjs <ticketId> <message>");
  process.exit(1);
}

const ws = new WebSocket(`ws://localhost:8000/ws/${ticketId}`);

const timeout = setTimeout(() => {
  console.log("TIMEOUT_WAITING_FOR_MESSAGE");
  try { ws.close(); } catch {}
  process.exit(2);
}, 30000);

ws.addEventListener("open", () => {
  ws.send(JSON.stringify({ message, user: "Codex" }));
});

ws.addEventListener("message", (event) => {
  const payload = String(event.data);
  console.log(payload);
  const lowered = payload.toLowerCase();
  if (
    lowered.includes("stream_end") ||
    lowered.includes("run_finished") ||
    lowered.includes('"type":"error"')
  ) {
    clearTimeout(timeout);
    try { ws.close(); } catch {}
    process.exit(0);
  }
});

ws.addEventListener("error", (event) => {
  clearTimeout(timeout);
  console.error("WS_ERROR", event?.message || "");
  process.exit(3);
});
