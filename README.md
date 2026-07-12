# Lumen — News Intelligence

Ask any question about the news and get a **balanced, sourced briefing** instead of a
list of headlines. An AI agent (Claude Opus 4.8) searches the live web across the
political spectrum, then synthesizes what's happening, how each side is framing it,
what's established vs. contested, and what everyone's missing — with citations and a
grounded follow-up chat.

This is a ground-up rewrite of the original News-Analysis project (which classified
articles with a static BERT bias model). The old Flask/Celery/NewsAPI/Postgres stack
now lives in [`legacy/`](legacy/) for reference.

## How it works

```
Browser (Vite + React)
   │  POST /api/briefing  (Server-Sent Events)
   ▼
FastAPI (server/)
   │
   ├─ 1. research()    Opus 4.8 + web_search + web_fetch → cross-spectrum coverage,
   │                   reading the most important articles in full
   ├─ 2. synthesize()  Sonnet 4.6 structured-outputs call → validated Briefing JSON
   └─ 3. chat()        Sonnet 4.6 grounded follow-up Q&A (RAG over the sources)
```

Models are tiered for cost (Opus for agentic research, Sonnet for the rest) and
env-overridable — see `server/.env.example`. The UI also exposes a per-briefing
**Model** (Opus / Sonnet) and **Thinking** (Deep / Balanced / Quick) control;
"Thinking" sets the research effort *and* scales the web-search/fetch budget
(Deep 12/3 · Balanced 8/2 · Quick 5/1), which is the main speed-vs-depth lever.
Defaults to Opus + Balanced; pick Sonnet + Quick for a fast pass.

- **Live web search** replaces the old NewsAPI cron + Node scraper + Postgres.
- **Structured outputs** guarantee a typed `Briefing` the UI can render, and
  every cited source is validated against what web search actually returned.
- **Prompt caching** keeps multi-turn follow-up chat cheap.
- **SSE streaming** lets you watch the agent research in real time (and the
  worker is cancelled if you close the tab, so it stops spending tokens).
- **Persistence & sharing** — every briefing is saved to SQLite, gets a
  shareable `/b/:id` link, and appears on the trending homepage. Identical
  queries within 30 min are served from cache (no new API spend) — tune
  `CACHE_TTL_SECONDS` in `server/store.py`.

## Prerequisites

- Python 3.9+
- Node 18+
- An Anthropic API key — https://console.anthropic.com/settings/keys

## Run it

**1. Backend** (terminal 1):

```bash
cd server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then put your key in server/.env
python app.py               # serves http://127.0.0.1:8000
```

**2. Frontend** (terminal 2):

```bash
npm install
npm run dev                 # serves http://localhost:5173 (proxies /api → :8000)
```

Open http://localhost:5173 and ask about a news topic.

## Project layout

| Path | What |
|------|------|
| `server/app.py` | FastAPI app + SSE endpoints (briefing, chat, get-by-id, trending) |
| `server/agent.py` | The 3-stage research → synthesize → chat pipeline |
| `server/store.py` | SQLite persistence: save, fetch-by-id, recent, query cache |
| `server/schemas.py` | Pydantic models (incl. the structured `Briefing`) |
| `server/prompts.py` | System prompts for each stage |
| `src/` | Vite + React + Tailwind frontend |
| `legacy/` | The original Flask/Celery/Node app (archived) |

