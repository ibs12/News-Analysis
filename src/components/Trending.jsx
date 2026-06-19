import { useEffect, useState } from "react";
import { TrendingUp, ArrowUpRight, FileText } from "lucide-react";
import { getTrending } from "../api.js";
import { timeAgo } from "../lib/time.js";

// Recent briefings, shown on the homepage. Opening one is free (served from the
// store, no new Opus call), which is what makes this section cheap.
export default function Trending({ onOpen }) {
  const [items, setItems] = useState(null);

  useEffect(() => {
    getTrending(9).then(setItems);
  }, []);

  if (!items || items.length === 0) return null;

  return (
    <section className="mx-auto max-w-4xl px-5 pb-24">
      <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
        <TrendingUp className="h-4 w-4 text-brand" />
        Recently briefed
      </h2>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((b) => (
          <button
            key={b.id}
            onClick={() => onOpen(b.id)}
            className="group flex flex-col gap-2 rounded-xl bg-white p-4 text-left ring-1 ring-slate-200 transition hover:ring-brand"
          >
            <div className="flex items-start justify-between gap-2">
              <span className="text-xs font-medium text-slate-400">{timeAgo(b.created_at)}</span>
              <ArrowUpRight className="h-4 w-4 text-slate-300 group-hover:text-brand" />
            </div>
            <h3 className="font-serif text-base font-semibold leading-snug text-ink group-hover:text-brand">
              {b.headline || b.query}
            </h3>
            <p className="line-clamp-1 text-xs text-slate-500">{b.query}</p>
            <span className="mt-auto flex items-center gap-1 pt-1 text-xs text-slate-400">
              <FileText className="h-3 w-3" />
              {b.source_count} sources
            </span>
          </button>
        ))}
      </div>
    </section>
  );
}
