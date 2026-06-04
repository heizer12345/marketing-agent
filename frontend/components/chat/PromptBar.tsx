"use client";

import { forwardRef, useCallback, useImperativeHandle, useLayoutEffect, useRef, useState } from "react";

export type PromptBarHandle = {
  focus: () => void;
  setValue: (text: string) => void;
};

const MIN_HEIGHT = 88;
const MAX_HEIGHT = 220;

function resizeTextarea(el: HTMLTextAreaElement | null) {
  if (!el) return;
  el.style.height = "auto";
  const next = Math.min(MAX_HEIGHT, Math.max(MIN_HEIGHT, el.scrollHeight));
  el.style.height = `${next}px`;
  el.style.overflowY = el.scrollHeight > MAX_HEIGHT ? "auto" : "hidden";
}

export const PromptBar = forwardRef<PromptBarHandle, {
  onSubmit: (prompt: string) => void;
  disabled?: boolean;
}>(function PromptBar({ onSubmit, disabled }, ref) {
  const [val, setVal] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const send = useCallback(() => {
    const text = val.trim();
    if (!text) return;
    onSubmit(text);
    setVal("");
  }, [val, onSubmit]);

  useImperativeHandle(ref, () => ({
    focus: () => {
      const el = textareaRef.current;
      el?.focus();
      if (el) {
        const len = el.value.length;
        el.setSelectionRange(len, len);
      }
    },
    setValue: (text: string) => {
      setVal(text);
      requestAnimationFrame(() => {
        const el = textareaRef.current;
        if (el) {
          resizeTextarea(el);
          el.focus();
          const len = text.length;
          el.setSelectionRange(len, len);
        }
      });
    },
  }));

  useLayoutEffect(() => {
    resizeTextarea(textareaRef.current);
  }, [val]);

  return (
    <div className="border-t" style={{ background: "white", borderColor: "var(--border)" }}>
      <div className="max-w-3xl mx-auto px-6 py-4">
        <div className="flex items-end gap-3">
          <div className="flex-1 min-w-0">
            <textarea
              ref={textareaRef}
              id="chat-prompt-input"
              value={val}
              onChange={(e) => setVal(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send();
                }
                if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                  e.preventDefault();
                  send();
                }
              }}
              placeholder="Ask anything — or pick a topic above to load a starter prompt"
              rows={3}
              className="input resize-none font-sans text-[13.5px] leading-relaxed w-full block"
              style={{ minHeight: MIN_HEIGHT, maxHeight: MAX_HEIGHT }}
            />
            <p className="text-[10.5px] text-muted mt-1.5 px-0.5">
              <span className="kbd text-[9px]">Enter</span> to send ·{" "}
              <span className="kbd text-[9px]">Shift</span>+<span className="kbd text-[9px]">Enter</span> for a new line
            </p>
          </div>
          <button
            type="button"
            className="btn-primary shrink-0 px-5 py-3 min-h-[88px] self-end"
            onClick={send}
            disabled={disabled || !val.trim()}
          >
            Send
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22,2 15,22 11,13 2,9" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
});
