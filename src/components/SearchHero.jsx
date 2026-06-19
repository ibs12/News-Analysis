import { useState } from "react";
import { Search, Sparkles } from "lucide-react";
import SettingsControls from "./SettingsControls.jsx";

const SUGGESTIONS = [
  "What's the latest on US–China tariff negotiations?",
  "How are sources covering the new AI executive order?",
  "Is inflation actually cooling? What do the numbers say?",
];

export default function SearchHero({ onSearch, busy, settings, onSettingsChange }) {
  const [value, setValue] = useState("");

  const submit = (e) => {
    e.preventDefault();
    const q = value.trim();
    if (q && !busy) onSearch(q);
  };

  return (
    <section className="mx-auto max-w-3xl px-5 pt-20 pb-10 text-center">
      <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-white px-3 py-1 text-xs font-medium text-slate-600 ring-1 ring-slate-200">
        <Sparkles className="h-3.5 w-3.5 text-brand" />
        Powered by Claude · live web research
      </div>

      <h1 className="font-serif text-5xl font-semibold leading-tight tracking-tight text-ink sm:text-6xl">
        Read the news,
        <br />
        <span className="text-brand">not the spin.</span>
      </h1>
      <p className="mx-auto mt-5 max-w-xl text-lg leading-relaxed text-slate-600">
        Ask about any story. An AI agent searches the live web across the
        political spectrum and writes you a balanced, sourced briefing.
      </p>

      <form onSubmit={submit} className="mx-auto mt-8 max-w-2xl">
        <div className="flex items-center gap-2 rounded-2xl bg-white p-2 shadow-sm ring-1 ring-slate-200 focus-within:ring-2 focus-within:ring-brand">
          <Search className="ml-2 h-5 w-5 shrink-0 text-slate-400" />
          <input
            autoFocus
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="Ask about a news topic…"
            className="w-full bg-transparent px-1 py-2.5 text-base outline-none placeholder:text-slate-400"
          />
          <button
            type="submit"
            disabled={busy || !value.trim()}
            className="shrink-0 rounded-xl bg-brand px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-brand/90 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Brief me
          </button>
        </div>
      </form>

      <div className="mt-4">
        <SettingsControls
          settings={settings}
          onChange={onSettingsChange}
          disabled={busy}
        />
      </div>

      <div className="mx-auto mt-6 flex max-w-2xl flex-wrap justify-center gap-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => !busy && onSearch(s)}
            className="rounded-full bg-white px-3.5 py-1.5 text-left text-xs text-slate-600 ring-1 ring-slate-200 transition hover:ring-brand hover:text-brand"
          >
            {s}
          </button>
        ))}
      </div>
    </section>
  );
}
