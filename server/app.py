"""FastAPI app exposing the news-intelligence agent over Server-Sent Events.

Endpoints:
  GET  /api/health        — liveness + whether ANTHROPIC_API_KEY is configured
  POST /api/briefing      — SSE: research a topic, then stream a structured briefing
  POST /api/chat          — SSE: grounded follow-up chat over a briefing

SSE event types emitted by /api/briefing:
  status   {label}                 high-level progress ("Searching the web…")
  thinking {text}                  streamed summarized reasoning
  notes    {text}                  streamed research prose
  source   {title, url}            a source discovered via web search
  briefing {briefing, research_notes}   the final structured briefing
  error    {message}

SSE event types emitted by /api/chat:
  status {label} | token {text} | error {message}

Cost controls:
  * The streaming worker is cancelled as soon as the client disconnects, so an
    abandoned briefing stops spending tokens immediately.
  * Inputs are length-capped in schemas.py and /api/briefing is rate-limited
    per IP (in-memory; fine for a single instance).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from collections import defaultdict, deque
from contextlib import suppress
from pathlib import Path
from typing import Awaitable, Callable, Deque, Dict

from dotenv import load_dotenv

# Load env from server/.env first, then fall back to the project root .env.
load_dotenv(Path(__file__).parent / ".env")
load_dotenv(Path(__file__).parent.parent / ".env")

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse, StreamingResponse  # noqa: E402

import agent  # noqa: E402
import store  # noqa: E402
from schemas import Briefing, BriefingRequest, ChatRequest  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

store.init_db()

app = FastAPI(title="News Intelligence API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",  # disable proxy buffering so events flush
}

# --- light per-IP rate limit (in-memory sliding window) --------------------
RATE_LIMIT = 12          # requests
RATE_WINDOW = 60.0       # seconds
_hits: Dict[str, Deque[float]] = defaultdict(deque)


def _rate_ok(ip: str) -> bool:
    now = time.monotonic()
    dq = _hits[ip]
    while dq and now - dq[0] > RATE_WINDOW:
        dq.popleft()
    if len(dq) >= RATE_LIMIT:
        return False
    dq.append(now)
    return True


def _sse(
    request: Request, worker: Callable[[agent.Emit], Awaitable[None]]
) -> StreamingResponse:
    """Run `worker(emit)` and turn its emitted events into an SSE response.

    Cancels the worker if the client disconnects so we stop spending tokens on
    a briefing nobody is watching.
    """

    async def event_stream():
        queue: asyncio.Queue = asyncio.Queue()

        async def emit(event_type: str, payload: dict) -> None:
            await queue.put((event_type, payload))

        async def run() -> None:
            try:
                await worker(emit)
            except Exception as exc:  # surface errors to the client as an event
                logging.exception("worker failed")
                await queue.put(("error", {"message": str(exc)}))
            finally:
                await queue.put(None)

        task = asyncio.create_task(run())
        try:
            while True:
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    if await request.is_disconnected():
                        logging.info("client disconnected; cancelling worker")
                        break
                    yield ": keepalive\n\n"  # comment frame keeps the stream warm
                    continue
                if item is None:
                    break
                event_type, payload = item
                yield f"event: {event_type}\ndata: {json.dumps(payload)}\n\n"
        finally:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

    return StreamingResponse(
        event_stream(), media_type="text/event-stream", headers=SSE_HEADERS
    )


@app.get("/api/health")
async def health() -> dict:
    return {
        "status": "ok",
        "anthropic_key_configured": bool(os.getenv("ANTHROPIC_API_KEY")),
        "models": {
            "research": agent.RESEARCH_MODEL,
            "synthesis": agent.SYNTHESIS_MODEL,
            "chat": agent.CHAT_MODEL,
        },
    }


@app.post("/api/briefing")
async def briefing(req: BriefingRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not _rate_ok(client_ip):
        return JSONResponse(
            {"error": "Rate limit exceeded. Please wait a moment and try again."},
            status_code=429,
        )

    query = req.query.strip()
    # Resolve the research model/effort for this request (None → server default).
    model = req.model or agent.RESEARCH_MODEL
    effort = req.effort or agent.RESEARCH_EFFORT

    async def worker(emit: agent.Emit) -> None:
        if not query:
            await emit("error", {"message": "Query is required."})
            return

        # Cache: reuse a recent identical briefing (same query + settings)
        # instead of re-spending budget.
        cached = store.find_fresh(query, model, effort)
        if cached:
            logging.info("cache hit for %r -> %s", query, cached["id"])
            await emit("status", {"label": "Found a recent briefing…"})
            for s in cached["briefing"].get("sources", []):
                await emit("source", {"title": s["title"], "url": s["url"]})
            await emit(
                "briefing",
                {"briefing": cached["briefing"], "research_notes": cached["research_notes"]},
            )
            await emit("saved", {"id": cached["id"], "cached": True})
            return

        await emit("status", {"label": "Researching across the spectrum…"})
        notes, sources = await agent.research(query, emit, model=model, effort=effort)

        # No sources means the topic was too vague to research (the agent asks
        # for clarification). Skip the wasted synthesis call and return its
        # message directly — renders fine in the existing briefing UI. Not saved.
        if not sources:
            clarification = Briefing(
                headline="I need a bit more detail",
                summary=notes.strip()[:1500]
                or "I couldn't find coverage for that. Try a more specific topic.",
            )
            await emit(
                "briefing",
                {"briefing": clarification.model_dump(), "research_notes": notes},
            )
            return

        await emit("status", {"label": "Synthesizing the briefing…"})
        result = await agent.synthesize(query, notes, sources)
        briefing_dict = result.model_dump()
        await emit("briefing", {"briefing": briefing_dict, "research_notes": notes})

        # Persist so the briefing is shareable and shows up in trending.
        briefing_id = store.save_briefing(query, briefing_dict, notes, model, effort)
        await emit("saved", {"id": briefing_id})

    return _sse(request, worker)


@app.post("/api/chat")
async def chat(req: ChatRequest, request: Request):
    async def worker(emit: agent.Emit) -> None:
        message = req.message.strip()
        if not message:
            await emit("error", {"message": "Message is required."})
            return
        await agent.chat(
            query=req.query,
            briefing=req.briefing,
            notes=req.research_notes,
            history=req.history,
            message=message,
            emit=emit,
        )

    return _sse(request, worker)


@app.get("/api/briefing/{briefing_id}")
async def get_saved_briefing(briefing_id: str):
    record = store.get_briefing(briefing_id)
    if record is None:
        return JSONResponse({"error": "Briefing not found."}, status_code=404)
    return record


@app.get("/api/trending")
async def trending(limit: int = 12) -> dict:
    return {"briefings": store.recent(limit)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
