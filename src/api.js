// Minimal SSE-over-fetch client. EventSource doesn't support POST bodies, so we
// read the response stream and parse `event:`/`data:` frames ourselves.

function parseFrame(raw) {
  let event = "message";
  let data = "";
  for (const line of raw.split("\n")) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) data += line.slice(5).trim();
  }
  if (!data) return null;
  try {
    return { event, data: JSON.parse(data) };
  } catch {
    return { event, data };
  }
}

async function streamSSE(url, body, onEvent, signal) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok || !res.body) {
    throw new Error(`Request failed (${res.status})`);
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx;
    while ((idx = buffer.indexOf("\n\n")) !== -1) {
      const frame = parseFrame(buffer.slice(0, idx));
      buffer = buffer.slice(idx + 2);
      if (frame) onEvent(frame);
    }
  }
}

export function streamBriefing(query, options, onEvent, signal) {
  // options: { model, effort } — research-stage overrides
  return streamSSE("/api/briefing", { query, ...options }, onEvent, signal);
}

export function streamChat(payload, onEvent, signal) {
  return streamSSE("/api/chat", payload, onEvent, signal);
}

export async function getBriefing(id) {
  const res = await fetch(`/api/briefing/${encodeURIComponent(id)}`);
  if (!res.ok) throw new Error(`Briefing not found (${res.status})`);
  return res.json();
}

export async function getTrending(limit = 12) {
  try {
    const res = await fetch(`/api/trending?limit=${limit}`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.briefings || [];
  } catch {
    return [];
  }
}
