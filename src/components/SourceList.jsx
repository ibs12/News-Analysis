import { ExternalLink } from "lucide-react";
import { leanMeta } from "../lib/leans.js";

export default function SourceList({ sources }) {
  return (
    <section>
      <h2 className="mb-3 font-serif text-2xl font-semibold text-ink">
        Sources <span className="text-base font-normal text-slate-400">({sources.length})</span>
      </h2>
      <ul className="space-y-2">
        {sources.map((s, i) => {
          const meta = leanMeta(s.lean);
          return (
            <li key={i}>
              <a
                href={s.url}
                target="_blank"
                rel="noreferrer"
                className="group flex gap-3 rounded-xl bg-white p-3.5 ring-1 ring-slate-200 transition hover:ring-brand"
              >
                <span
                  className="mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full"
                  style={{ background: meta.dot }}
                  title={meta.label}
                />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-slate-700">
                      {s.publisher}
                    </span>
                    <span
                      className={`rounded-full px-1.5 py-0.5 text-[10px] font-medium ring-1 ${meta.chip}`}
                    >
                      {meta.label}
                    </span>
                  </div>
                  <p className="mt-0.5 truncate text-sm font-medium text-ink group-hover:text-brand">
                    {s.title}
                  </p>
                  {s.takeaway && (
                    <p className="mt-0.5 line-clamp-2 text-xs text-slate-500">
                      {s.takeaway}
                    </p>
                  )}
                </div>
                <ExternalLink className="mt-1 h-3.5 w-3.5 shrink-0 text-slate-300 group-hover:text-brand" />
              </a>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
