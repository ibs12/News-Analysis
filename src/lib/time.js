// "5m ago" / "2h ago" / "3d ago" from an epoch-seconds timestamp.
export function timeAgo(epochSeconds) {
  if (!epochSeconds) return "";
  const secs = Math.max(0, Date.now() / 1000 - epochSeconds);
  if (secs < 60) return "just now";
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}
