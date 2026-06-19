import { Cpu, Gauge } from "lucide-react";

export const MODEL_OPTIONS = [
  { value: "claude-opus-4-8", label: "Opus · deepest" },
  { value: "claude-sonnet-4-6", label: "Sonnet · faster" },
];

// "Thinking" maps to the effort parameter, and also scales the web-search/fetch
// budget on the backend — so it's the main speed-vs-depth lever.
export const EFFORT_OPTIONS = [
  { value: "high", label: "Deep" },
  { value: "medium", label: "Balanced" },
  { value: "low", label: "Quick" },
];

export const DEFAULT_SETTINGS = { model: "claude-opus-4-8", effort: "medium" };

export default function SettingsControls({ settings, onChange, compact = false, disabled }) {
  const set = (key) => (e) => onChange({ ...settings, [key]: e.target.value });

  const wrap = compact
    ? "flex items-center gap-1.5 rounded-lg bg-white px-2 py-1 ring-1 ring-slate-200"
    : "flex items-center gap-2 rounded-xl bg-white px-3 py-2 ring-1 ring-slate-200";
  const icon = compact ? "h-3.5 w-3.5 text-slate-400" : "h-4 w-4 text-slate-400";
  const sel =
    "cursor-pointer bg-transparent font-medium text-slate-600 outline-none disabled:cursor-not-allowed disabled:opacity-50 " +
    (compact ? "text-xs" : "text-sm");

  return (
    <div className={`flex items-center gap-2 ${compact ? "" : "justify-center"}`}>
      <div className={wrap}>
        <Cpu className={icon} />
        <select
          value={settings.model}
          onChange={set("model")}
          disabled={disabled}
          title="Research model"
          className={sel}
        >
          {MODEL_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </div>

      <div className={wrap}>
        <Gauge className={icon} />
        <select
          value={settings.effort}
          onChange={set("effort")}
          disabled={disabled}
          title="Thinking depth (also controls how much it searches)"
          className={sel}
        >
          {EFFORT_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
