import { useCallback, useEffect, useRef, useState } from "react";
import { Newspaper, Search, AlertCircle, Link2, Check, Loader2 } from "lucide-react";
import { streamBriefing, getBriefing } from "./api.js";
import SearchHero from "./components/SearchHero.jsx";
import Trending from "./components/Trending.jsx";
import ResearchConsole from "./components/ResearchConsole.jsx";
import BriefingView from "./components/BriefingView.jsx";

const EMPTY = {
  statusLabel: "",
  notes: "",
  thinking: "",
  sources: [],
  briefing: null,
  researchNotes: "",
  error: "",
};

function parsePath() {
  const m = window.location.pathname.match(/^\/b\/([^/]+)/);
  return m ? { name: "briefing", id: m[1] } : { name: "home" };
}

export default function App() {
  const [phase, setPhase] = useState("idle"); // idle | researching | loading | ready | error
  const [query, setQuery] = useState("");
  const [state, setState] = useState(EMPTY);
  const [briefingId, setBriefingId] = useState(null);
  const abortRef = useRef(null);

  const resetHome = useCallback(() => {
    abortRef.current?.abort();
    setPhase("idle");
    setState(EMPTY);
    setQuery("");
    setBriefingId(null);
  }, []);

  // Load a saved briefing by id (deep link, trending click, or back/forward).
  const loadBriefing = useCallback(async (id) => {
    abortRef.current?.abort();
    setBriefingId(id);
    setQuery("");
    setState(EMPTY);
    setPhase("loading");
    try {
      const data = await getBriefing(id);
      setQuery(data.query);
      setState({ ...EMPTY, briefing: data.briefing, researchNotes: data.research_notes });
      setPhase("ready");
    } catch (e) {
      setState({ ...EMPTY, error: e.message });
      setPhase("error");
    }
  }, []);

  // Resolve the current URL → state. Used on mount and on back/forward.
  const applyFromUrl = useCallback(() => {
    const route = parsePath();
    if (route.name === "briefing") loadBriefing(route.id);
    else resetHome();
  }, [loadBriefing, resetHome]);

  useEffect(() => {
    window.addEventListener("popstate", applyFromUrl);
    applyFromUrl();
    return () => window.removeEventListener("popstate", applyFromUrl);
  }, [applyFromUrl]);

  // Trending click / programmatic open: push URL, then load.
  const openBriefing = useCallback(
    (id) => {
      window.history.pushState({}, "", `/b/${id}`);
      loadBriefing(id);
    },
    [loadBriefing]
  );

  const goHome = useCallback(() => {
    window.history.pushState({}, "", "/");
    resetHome();
  }, [resetHome]);

  async function runBriefing(q) {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setQuery(q);
    setState(EMPTY);
    setBriefingId(null);
    setPhase("researching");

    try {
      await streamBriefing(
        q,
        ({ event, data }) => {
          setState((s) => {
            switch (event) {
              case "status":
                return { ...s, statusLabel: data.label };
              case "thinking":
                return { ...s, thinking: s.thinking + data.text };
              case "notes":
                return { ...s, notes: s.notes + data.text };
              case "source":
                return s.sources.some((x) => x.url === data.url)
                  ? s
                  : { ...s, sources: [...s.sources, data] };
              case "briefing":
                return {
                  ...s,
                  briefing: data.briefing,
                  researchNotes: data.research_notes,
                };
              case "error":
                return { ...s, error: data.message };
              default:
                return s;
            }
          });
          if (event === "briefing") setPhase("ready");
          if (event === "error") setPhase("error");
          // A persisted briefing came back with a shareable id — reflect it in
          // the URL so the page can be bookmarked/shared.
          if (event === "saved") {
            setBriefingId(data.id);
            window.history.pushState({}, "", `/b/${data.id}`);
          }
        },
        controller.signal
      );
    } catch (e) {
      if (e.name !== "AbortError") {
        setState((s) => ({ ...s, error: e.message }));
        setPhase("error");
      }
    }
  }

  const busy = phase === "researching";

  // Home: hero + trending
  if (phase === "idle") {
    return (
      <div className="min-h-full">
        <SearchHero onSearch={runBriefing} busy={busy} />
        <Trending onOpen={openBriefing} />
      </div>
    );
  }

  // Briefing screen (researching | loading | ready | error)
  return (
    <div className="min-h-full">
      <TopBar busy={busy} onSearch={runBriefing} onHome={goHome} briefingId={briefingId} />

      <main className="mx-auto max-w-5xl space-y-6 px-5 pb-24 pt-6">
        {query && (
          <p className="text-sm text-slate-500">
            Briefing on <span className="font-medium text-slate-700">“{query}”</span>
          </p>
        )}

        {phase === "loading" && (
          <div className="flex items-center gap-3 rounded-2xl bg-white p-6 text-sm text-slate-500 ring-1 ring-slate-200">
            <Loader2 className="h-4 w-4 animate-spin text-brand" />
            Loading briefing…
          </div>
        )}

        {(busy || state.sources.length > 0) && (
          <ResearchConsole
            status={state.statusLabel}
            notes={state.notes}
            thinking={state.thinking}
            sources={state.sources}
            active={busy}
            done={phase === "ready"}
          />
        )}

        {state.error && (
          <div className="flex items-start gap-3 rounded-2xl bg-red-50 p-4 text-sm text-red-700 ring-1 ring-red-200">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <div>
              <p className="font-semibold">Something went wrong</p>
              <p className="mt-0.5 text-red-600">{state.error}</p>
              <p className="mt-1 text-xs text-red-500">
                Tip: make sure the backend is running and ANTHROPIC_API_KEY is set.
              </p>
            </div>
          </div>
        )}

        {state.briefing && (
          <BriefingView
            query={query}
            briefing={state.briefing}
            researchNotes={state.researchNotes}
          />
        )}
      </main>
    </div>
  );
}

function TopBar({ busy, onSearch, onHome, briefingId }) {
  const [value, setValue] = useState("");
  const [copied, setCopied] = useState(false);

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      /* clipboard blocked — no-op */
    }
  };

  return (
    <header className="sticky top-0 z-10 border-b border-slate-200 bg-[#f8f7f4]/85 backdrop-blur">
      <div className="mx-auto flex max-w-5xl items-center gap-3 px-5 py-3">
        <button
          onClick={onHome}
          className="flex shrink-0 items-center gap-2 font-serif text-lg font-semibold text-brand"
        >
          <Newspaper className="h-5 w-5" />
          Lumen
        </button>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (value.trim() && !busy) onSearch(value.trim());
          }}
          className="ml-auto flex w-full max-w-md items-center gap-2 rounded-xl bg-white px-3 py-1.5 ring-1 ring-slate-200 focus-within:ring-brand"
        >
          <Search className="h-4 w-4 shrink-0 text-slate-400" />
          <input
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="New briefing…"
            className="w-full bg-transparent py-1 text-sm outline-none placeholder:text-slate-400"
          />
        </form>

        {briefingId && (
          <button
            onClick={copyLink}
            className="flex shrink-0 items-center gap-1.5 rounded-xl bg-white px-3 py-2 text-sm font-medium text-slate-600 ring-1 ring-slate-200 transition hover:text-brand hover:ring-brand"
            title="Copy shareable link"
          >
            {copied ? (
              <>
                <Check className="h-4 w-4 text-emerald-500" /> Copied
              </>
            ) : (
              <>
                <Link2 className="h-4 w-4" /> Share
              </>
            )}
          </button>
        )}
      </div>
    </header>
  );
}
