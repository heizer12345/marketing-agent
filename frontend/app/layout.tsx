import "./globals.css";
import type { Metadata } from "next";
import { Sidebar } from "@/components/shell/Sidebar";
import { OnboardingGate } from "@/components/onboarding/OnboardingGate";

export const metadata: Metadata = {
  title: "Sourcy Marketing",
  description: "AI-powered marketing analyst + content engine for Sourcy",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-sans">
        <div className="flex h-screen w-screen overflow-hidden">
          <Sidebar />
          <main className="flex-1 overflow-hidden flex flex-col">
            <OnboardingGate>{children}</OnboardingGate>
          </main>
        </div>
      </body>
    </html>
  );
}
