import { useEffect, useRef, useState } from "react";
import { Globe, Brain, ChevronDown, Loader2 } from "lucide-react";

// Live view of the agent working: current status, streamed research prose,
// summarized reasoning, and sources as they're discovered. Collapses to a
// summary line once the briefing is ready.
export default function ResearchConsole({
  status,
  notes,
  thinking,
  sources,
  active,
  done,
}) {
  const [open, setOpen] = useState(true);
  const feedRef = useRef(null);

  // Collapse automatically once research finishes.
  useEffect(() => {
    if (done) setOpen(false);
  }, [done]);

  // Keep the streaming feed pinned to the bottom while active.
  useEffect(() => {
    if (open && active && feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
    }
  }, [notes, thinking, open, active]);

  return (
    <div className="overflow-hidden rounded-2xl bg-white ring-1 ring-slate-200">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-3 px-4 py-3 text-left"
      >
        {active ? (
          <Loader2 className="h-4 w-4 shrink-0 animate-spin text-brand" />
        ) : (
          <Globe className="h-4 w-4 shrink-0 text-slate-400" />
        )}
        <span className="flex-1 text-sm font-medium text-slate-700">
          {active ? status || "Researching…" : `Research trail · ${sources.length} sources`}
        </span>
        <ChevronDown
          className={`h-4 w-4 text-slate-400 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open && (
        <div className="border-t border-slate-100 px-4 pb-4 pt-3">
          {sources.length > 0 && (
            <div className="mb-3 flex flex-wrap gap-1.5">
              {sources.map((s) => (
                <a
                  key={s.url}
                  href={s.url}
                  target="_blank"
                  rel="noreferrer"
                  title={s.title}
                  className="max-w-[220px] truncate rounded-full bg-slate-50 px-2.5 py-1 text-xs text-slate-600 ring-1 ring-slate-200 hover:text-brand hover:ring-brand"
                >
                  {hostname(s.url)}
                </a>
              ))}
            </div>
          )}

          <div
            ref={feedRef}
            className="scroll-slim max-h-72 overflow-y-auto whitespace-pre-wrap text-sm leading-relaxed text-slate-600"
          >
            {thinking && (
              <p className="mb-3 flex gap-2 rounded-lg bg-slate-50 p-3 text-[13px] italic text-slate-500">
                <Brain className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                <span>{thinking}</span>
              </p>
            )}
            {notes || (
              <span className="text-slate-400">
                {active ? "Gathering coverage…" : "No notes."}
              </span>
            )}
            {active && <span className="pulse-dot">▍</span>}
          </div>
        </div>
      )}
    </div>
  );
}

function hostname(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}
