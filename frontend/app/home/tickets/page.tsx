"use client";

import { useEffect, useRef } from "react";

/** Embeds the legacy kanban UI served by FastAPI at "/". */
export default function TicketsPage() {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    // Re-mount the iframe on tab switch so it loads fresh state.
  }, []);

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <header className="border-b border-border bg-white px-8 py-4">
        <h1 className="text-lg font-semibold text-ink">Tickets</h1>
        <p className="text-xs text-muted">Legacy kanban for ticket management.</p>
      </header>
      <iframe
        ref={iframeRef}
        src="/"
        className="flex-1 w-full border-0"
        title="Legacy kanban"
      />
    </div>
  );
}
