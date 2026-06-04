"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useChatStore } from "./store";
import type { WSEvent } from "./types";

import { wsUrl as backendWsUrl } from "./backendUrl";

/**
 * Module-level WebSocket cache, keyed by ticketId.
 *
 * React StrictMode (dev) double-mounts effects, which previously caused us to
 * open a WS, immediately close it via cleanup, and reopen — the second
 * connection often died before establishing, swallowing the user's prompt.
 *
 * By keeping the WS at module level we survive remounts: the second mount
 * picks up the existing WS instead of opening a new one. We close it only
 * when the LAST consumer unmounts AND no new mount has subscribed within a
 * short grace window.
 */
type Subscription = {
  ws: WebSocket;
  consumers: number;
  closeTimer: number | null;
};
const wsCache: Map<string, Subscription> = (globalThis as any).__sourcyWsCache
  ?? ((globalThis as any).__sourcyWsCache = new Map());

function acquire(ticketId: string, onEvent: (ev: WSEvent) => void, onState: (connected: boolean) => void): () => void {
  let entry = wsCache.get(ticketId);
  if (entry && entry.closeTimer != null) {
    clearTimeout(entry.closeTimer);
    entry.closeTimer = null;
  }
  if (!entry) {
    const ws = new WebSocket(backendWsUrl(`/ws/${ticketId}`));
    // eslint-disable-next-line no-console
    console.info(`[ws] opening ${ticketId.slice(0, 8)}`);
    entry = { ws, consumers: 0, closeTimer: null };
    wsCache.set(ticketId, entry);
  }

  const e = entry;
  e.consumers += 1;

  const onOpen = () => onState(true);
  const onClose = () => onState(false);
  const onError = () => onState(false);
  const onMessage = (ev: MessageEvent) => {
    try { onEvent(JSON.parse(ev.data)); } catch { /* ignore parse errors */ }
  };

  // If the WS is already open we may have missed the open event; reflect state.
  if (e.ws.readyState === WebSocket.OPEN) onState(true);

  e.ws.addEventListener("open", onOpen);
  e.ws.addEventListener("close", onClose);
  e.ws.addEventListener("error", onError);
  e.ws.addEventListener("message", onMessage);

  return () => {
    e.ws.removeEventListener("open", onOpen);
    e.ws.removeEventListener("close", onClose);
    e.ws.removeEventListener("error", onError);
    e.ws.removeEventListener("message", onMessage);
    e.consumers -= 1;
    if (e.consumers <= 0) {
      // Grace period — give a remount (StrictMode) time to re-subscribe before
      // we actually close.
      e.closeTimer = window.setTimeout(() => {
        if (e.consumers <= 0) {
          // eslint-disable-next-line no-console
          console.info(`[ws] closing ${ticketId.slice(0, 8)} (no consumers)`);
          try { e.ws.close(); } catch {}
          wsCache.delete(ticketId);
        }
      }, 500);
    }
  };
}

export function useAgentStream(sessionId: string, ticketId: string | null) {
  const [connected, setConnected] = useState(false);
  // Hold the active WS reference so sendPrompt can hit it directly without
  // depending on React state.
  const wsRef = useRef<WebSocket | null>(null);

  // Latest handleEvent — read via store.getState() inside the listener so the
  // handler stays stable across renders.
  useEffect(() => {
    if (!ticketId) { setConnected(false); wsRef.current = null; return; }
    // Track the WS reference for sendPrompt.
    const updateRef = () => {
      const entry = wsCache.get(ticketId);
      wsRef.current = entry ? entry.ws : null;
    };

    const onEvent = (ev: WSEvent) => {
      useChatStore.getState().handleEvent(sessionId, ev);
    };
    const onState = (c: boolean) => {
      updateRef();
      setConnected(c);
    };

    const release = acquire(ticketId, onEvent, onState);
    updateRef();

    return release;
  }, [ticketId, sessionId]);

  const sendPrompt = useCallback((prompt: string, user = "Eugene") => {
    const ws = wsRef.current ?? wsCache.get(ticketId || "")?.ws ?? null;
    if (!ws) return false;
    if (ws.readyState === WebSocket.CONNECTING) {
      // Queue once it's open.
      const handler = () => { ws.removeEventListener("open", handler); try { ws.send(JSON.stringify({ message: prompt, user })); } catch {} };
      ws.addEventListener("open", handler);
      return true;
    }
    if (ws.readyState !== WebSocket.OPEN) return false;
    try { ws.send(JSON.stringify({ message: prompt, user })); return true; } catch { return false; }
  }, [ticketId]);

  return { connected, sendPrompt };
}
