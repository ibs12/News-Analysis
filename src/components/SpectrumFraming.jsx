import { spectrumCounts, SIDE_META } from "../lib/leans.js";

// A spectrum bar (share of sources by side) plus side-by-side framing cards
// showing how the left, center, and right each cover the story.
export default function SpectrumFraming({ sources, framing }) {
  const counts = spectrumCounts(sources);
  const total = Math.max(counts.left + counts.center + counts.right, 1);
  const pct = (n) => Math.round((n / total) * 100);

  const ordered = ["left", "center", "right"]
    .map((side) => framing.find((f) => f.side === side))
    .filter(Boolean);

  return (
    <section>
      <h2 className="mb-3 font-serif text-2xl font-semibold text-ink">
        How the sides are covering it
      </h2>

      {/* spectrum share bar */}
      <div className="mb-5">
        <div className="flex h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
          <div style={{ width: `${pct(counts.left)}%`, background: "#2563eb" }} />
          <div style={{ width: `${pct(counts.center)}%`, background: "#94a3b8" }} />
          <div style={{ width: `${pct(counts.right)}%`, background: "#dc2626" }} />
        </div>
        <div className="mt-1.5 flex justify-between text-xs text-slate-500">
          <span>Left · {pct(counts.left)}%</span>
          <span>Center · {pct(counts.center)}%</span>
          <span>Right · {pct(counts.right)}%</span>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        {ordered.map((f) => {
          const meta = SIDE_META[f.side];
          return (
            <article
              key={f.side}
              className={`rounded-xl p-4 ring-1 ${meta.ring} ${meta.bg}`}
            >
              <div className="mb-2 flex items-center gap-2">
                <span
                  className="h-2.5 w-2.5 rounded-full"
                  style={{ background: meta.accent }}
                />
                <h3 className="text-sm font-semibold text-ink">{meta.label}</h3>
              </div>
              <p className="text-sm font-medium leading-snug text-slate-800">
                {f.narrative}
              </p>
              {f.emphasis?.length > 0 && (
                <ul className="mt-2 space-y-1">
                  {f.emphasis.map((e, i) => (
                    <li key={i} className="flex gap-1.5 text-[13px] text-slate-600">
                      <span style={{ color: meta.accent }}>•</span>
                      <span>{e}</span>
                    </li>
                  ))}
                </ul>
              )}
              {f.omits && (
                <p className="mt-3 border-t border-black/5 pt-2 text-xs text-slate-500">
                  <span className="font-semibold text-slate-600">Downplays: </span>
                  {f.omits}
                </p>
              )}
            </article>
          );
        })}
      </div>
    </section>
  );
}
