import { useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { Send, MessagesSquare } from "lucide-react";
import { streamChat } from "../api.js";

// Grounded follow-up chat. Each turn is sent with the briefing + research notes
// as context so answers stay anchored to the same sources (and can search the
// web for anything new).
export default function Chat({ query, briefing, researchNotes, followUps }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [status, setStatus] = useState("");
  const bottomRef = useRef(null);

  const scrollDown = () =>
    requestAnimationFrame(() =>
      bottomRef.current?.scrollIntoView({ behavior: "smooth" })
    );

  async function ask(text) {
    const message = text.trim();
    if (!message || streaming) return;

    const history = messages.map((m) => ({ role: m.role, content: m.content }));
    setMessages((m) => [...m, { role: "user", content: message }, { role: "assistant", content: "" }]);
    setInput("");
    setStreaming(true);
    setStatus("");
    scrollDown();

    try {
      await streamChat(
        { query, briefing, research_notes: researchNotes, history, message },
        ({ event, data }) => {
          if (event === "status") setStatus(data.label);
          else if (event === "token") {
            setStatus("");
            setMessages((m) => {
              const next = [...m];
              next[next.length - 1] = {
                role: "assistant",
                content: next[next.length - 1].content + data.text,
              };
              return next;
            });
            scrollDown();
          } else if (event === "error") {
            setMessages((m) => {
              const next = [...m];
              next[next.length - 1] = {
                role: "assistant",
                content: `⚠️ ${data.message}`,
              };
              return next;
            });
          }
        }
      );
    } catch (e) {
      setMessages((m) => {
        const next = [...m];
        next[next.length - 1] = { role: "assistant", content: `⚠️ ${e.message}` };
        return next;
      });
    } finally {
      setStreaming(false);
    }
  }

  return (
    <section className="rounded-2xl bg-white ring-1 ring-slate-200">
      <div className="flex items-center gap-2 border-b border-slate-100 px-4 py-3">
        <MessagesSquare className="h-4 w-4 text-brand" />
        <h2 className="text-sm font-semibold text-slate-700">Ask a follow-up</h2>
      </div>

      <div className="space-y-3 px-4 py-4">
        {messages.length === 0 && followUps?.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {followUps.map((q) => (
              <button
                key={q}
                onClick={() => ask(q)}
                className="rounded-full bg-slate-50 px-3 py-1.5 text-left text-xs text-slate-600 ring-1 ring-slate-200 hover:text-brand hover:ring-brand"
              >
                {q}
              </button>
            ))}
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "flex justify-end" : ""}>
            <div
              className={
                m.role === "user"
                  ? "max-w-[85%] rounded-2xl rounded-br-sm bg-brand px-3.5 py-2 text-sm text-white"
                  : "prose-chat max-w-none text-sm text-slate-700"
              }
            >
              {m.role === "user" ? (
                m.content
              ) : m.content ? (
                <ReactMarkdown>{m.content}</ReactMarkdown>
              ) : (
                <span className="text-slate-400">{status || "Thinking…"}</span>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          ask(input);
        }}
        className="flex items-center gap-2 border-t border-slate-100 p-3"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask anything about this story…"
          disabled={streaming}
          className="w-full rounded-xl bg-slate-50 px-3.5 py-2.5 text-sm outline-none ring-1 ring-slate-200 focus:ring-brand disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={streaming || !input.trim()}
          className="shrink-0 rounded-xl bg-brand p-2.5 text-white transition hover:bg-brand/90 disabled:opacity-40"
        >
          <Send className="h-4 w-4" />
        </button>
      </form>
    </section>
  );
}
