// Visual language for political lean. Blue (left) → slate (center) → red (right)
// is the conventional US spectrum coloring; keep it intuitive.

export const LEAN_META = {
  left: { label: "Left", dot: "#2563eb", chip: "bg-blue-50 text-blue-700 ring-blue-200" },
  "center-left": {
    label: "Center-left",
    dot: "#60a5fa",
    chip: "bg-sky-50 text-sky-700 ring-sky-200",
  },
  center: {
    label: "Center",
    dot: "#64748b",
    chip: "bg-slate-100 text-slate-700 ring-slate-300",
  },
  "center-right": {
    label: "Center-right",
    dot: "#f87171",
    chip: "bg-orange-50 text-orange-700 ring-orange-200",
  },
  right: { label: "Right", dot: "#dc2626", chip: "bg-red-50 text-red-700 ring-red-200" },
  unknown: {
    label: "Unverified lean",
    dot: "#9ca3af",
    chip: "bg-gray-100 text-gray-600 ring-gray-300",
  },
};

export function leanMeta(lean) {
  return LEAN_META[lean] || LEAN_META.unknown;
}

// Group sources into left / center / right buckets for the spectrum bar.
export function spectrumCounts(sources = []) {
  const counts = { left: 0, center: 0, right: 0 };
  for (const s of sources) {
    if (s.lean === "left" || s.lean === "center-left") counts.left += 1;
    else if (s.lean === "right" || s.lean === "center-right") counts.right += 1;
    else if (s.lean === "center") counts.center += 1;
  }
  return counts;
}

export const SIDE_META = {
  left: { label: "The Left", accent: "#2563eb", ring: "ring-blue-200", bg: "bg-blue-50/60" },
  center: {
    label: "The Center",
    accent: "#475569",
    ring: "ring-slate-200",
    bg: "bg-slate-50",
  },
  right: { label: "The Right", accent: "#dc2626", ring: "ring-red-200", bg: "bg-red-50/60" },
};
