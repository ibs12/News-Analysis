import { CheckCircle2, AlertTriangle, EyeOff } from "lucide-react";
import SpectrumFraming from "./SpectrumFraming.jsx";
import SourceList from "./SourceList.jsx";
import Chat from "./Chat.jsx";

const STATUS_STYLE = {
  disputed: "bg-amber-50 text-amber-700 ring-amber-200",
  unverified: "bg-slate-100 text-slate-600 ring-slate-300",
  misleading: "bg-red-50 text-red-700 ring-red-200",
  evolving: "bg-sky-50 text-sky-700 ring-sky-200",
};

export default function BriefingView({ query, briefing, researchNotes }) {
  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
      {/* main column */}
      <div className="space-y-8">
        <header>
          <h1 className="font-serif text-3xl font-semibold leading-tight tracking-tight text-ink sm:text-4xl">
            {briefing.headline}
          </h1>
          <p className="mt-3 text-lg leading-relaxed text-slate-700">
            {briefing.summary}
          </p>
        </header>

        {briefing.framing_by_side?.length > 0 && (
          <SpectrumFraming sources={briefing.sources} framing={briefing.framing_by_side} />
        )}

        <div className="grid gap-4 md:grid-cols-2">
          {briefing.key_facts?.length > 0 && (
            <Panel title="What's established" icon={CheckCircle2} accent="text-emerald-600">
              <ul className="space-y-2">
                {briefing.key_facts.map((f, i) => (
                  <li key={i} className="flex gap-2 text-sm text-slate-700">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
            </Panel>
          )}

          {briefing.contested_claims?.length > 0 && (
            <Panel title="What's contested" icon={AlertTriangle} accent="text-amber-600">
              <ul className="space-y-3">
                {briefing.contested_claims.map((c, i) => (
                  <li key={i} className="text-sm">
                    <div className="flex items-start justify-between gap-2">
                      <span className="font-medium text-slate-800">{c.claim}</span>
                      <span
                        className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide ring-1 ${
                          STATUS_STYLE[c.status] || STATUS_STYLE.unverified
                        }`}
                      >
                        {c.status}
                      </span>
                    </div>
                    <p className="mt-0.5 text-xs text-slate-500">{c.detail}</p>
                  </li>
                ))}
              </ul>
            </Panel>
          )}
        </div>

        {briefing.blind_spots?.length > 0 && (
          <Panel title="Blind spots" icon={EyeOff} accent="text-violet-600">
            <ul className="grid gap-2 sm:grid-cols-2">
              {briefing.blind_spots.map((b, i) => (
                <li key={i} className="flex gap-2 text-sm text-slate-700">
                  <EyeOff className="mt-0.5 h-4 w-4 shrink-0 text-violet-400" />
                  <span>{b}</span>
                </li>
              ))}
            </ul>
          </Panel>
        )}

        <Chat
          query={query}
          briefing={briefing}
          researchNotes={researchNotes}
          followUps={briefing.follow_up_questions}
        />
      </div>

      {/* sources rail */}
      <aside className="lg:sticky lg:top-6 lg:self-start">
        {briefing.sources?.length > 0 && <SourceList sources={briefing.sources} />}
      </aside>
    </div>
  );
}

function Panel({ title, icon: Icon, accent, children }) {
  return (
    <section className="rounded-2xl bg-white p-5 ring-1 ring-slate-200">
      <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
        <Icon className={`h-4 w-4 ${accent}`} />
        {title}
      </h2>
      {children}
    </section>
  );
}
