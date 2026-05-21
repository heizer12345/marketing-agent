"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { api } from "@/lib/api";

/** Redirects to /memory/setup on first launch if persona or design system are missing. */
export function OnboardingGate({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function check() {
      if (pathname.startsWith("/memory/setup")) {
        setReady(true);
        return;
      }
      try {
        const state = await api.memoryState();
        if (cancelled) return;
        if (!state.setup_complete) {
          router.replace("/memory/setup");
          return;
        }
      } catch {
        // If the API isn't reachable yet, render anyway; user will see error states.
      }
      if (!cancelled) setReady(true);
    }
    check();
    return () => { cancelled = true; };
  }, [pathname, router]);

  if (!ready) {
    return (
      <div className="flex-1 flex items-center justify-center text-muted text-sm">
        Loading workspace…
      </div>
    );
  }
  return <>{children}</>;
}
