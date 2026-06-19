"""The news-intelligence agent.

A three-stage pipeline built on the Anthropic Messages API:

  1. research()    — Claude uses the live `web_search` + `web_fetch` server tools
                     to gather coverage across the political spectrum, read the
                     most important articles in full, and write grounded notes.
                     Progress is streamed via an `emit` callback.
  2. synthesize()  — a structured-outputs call turns the notes + sources into a
                     balanced `Briefing`, then sources are reconciled against
                     what was actually found so nothing invented slips through.
  3. chat()        — grounded multi-turn follow-up; reuses the research as
                     context (RAG-style) and can search/fetch for anything new.

Model & effort tiering (overridable via env): research runs on Opus 4.8 (it's
agentic and tool-heavy); synthesis and chat default to the cheaper, fast
Sonnet 4.6 — structured extraction and grounded Q&A are well within its range.
Web search/fetch use the dynamic-filtering `_20260209` variants.
"""

from __future__ import annotations

import logging
import os
from typing import Awaitable, Callable, Dict, List, Tuple
from urllib.parse import urlparse

from anthropic import AsyncAnthropic

import prompts
from schemas import Briefing, ChatTurn, Source

logger = logging.getLogger("newsagent")

# --- model & effort tiering (env-overridable) ------------------------------
RESEARCH_MODEL = os.getenv("RESEARCH_MODEL", "claude-opus-4-8")
SYNTHESIS_MODEL = os.getenv("SYNTHESIS_MODEL", "claude-sonnet-4-6")
CHAT_MODEL = os.getenv("CHAT_MODEL", "claude-sonnet-4-6")
# Default research effort is "medium" (not "high") for snappier latency; the
# user can pick "high" (Deep) per request. Effort also scales the tool budget.
RESEARCH_EFFORT = os.getenv("RESEARCH_EFFORT", "medium")
SYNTHESIS_EFFORT = os.getenv("SYNTHESIS_EFFORT", "medium")
CHAT_EFFORT = os.getenv("CHAT_EFFORT", "medium")

# How many web searches / full-article fetches the research stage may spend,
# keyed by effort. Lower effort = fewer tool calls = lower latency. This is the
# main latency lever. The prompt tells the model to stop and write once the
# budget is exhausted rather than "waiting for a rate limit to reset".
_RESEARCH_BUDGETS = {"high": (12, 3), "medium": (8, 2), "low": (5, 1)}
_FETCH_CONTENT_TOKENS = 6000  # caps how much each fetched article pulls in


def _research_tools(effort: str) -> list:
    searches, fetches = _RESEARCH_BUDGETS.get(effort, _RESEARCH_BUDGETS["medium"])
    return [
        {"type": "web_search_20260209", "name": "web_search", "max_uses": searches},
        {
            "type": "web_fetch_20260209",
            "name": "web_fetch",
            "max_uses": fetches,
            "max_content_tokens": _FETCH_CONTENT_TOKENS,
        },
    ]


# Follow-up chat keeps a lighter, fixed tool budget — it's a quick interaction,
# not a full research pass.
CHAT_TOOLS = [
    {"type": "web_search_20260209", "name": "web_search", "max_uses": 5},
    {
        "type": "web_fetch_20260209",
        "name": "web_fetch",
        "max_uses": 2,
        "max_content_tokens": _FETCH_CONTENT_TOKENS,
    },
]

# Server-side tool loops can pause after ~10 internal iterations (pause_turn).
MAX_CONTINUATIONS = 4

# An emit callback: (event_type, payload) -> awaitable. Used to push SSE events.
Emit = Callable[[str, dict], Awaitable[None]]


def _client() -> AsyncAnthropic:
    return AsyncAnthropic()  # reads ANTHROPIC_API_KEY from the environment


async def _noop_emit(_type: str, _payload: dict) -> None:  # pragma: no cover
    return None


# ---------------------------------------------------------------------------
# URL helpers — used to validate that briefing sources are ones we actually saw
# ---------------------------------------------------------------------------


def _hostname(url: str) -> str:
    try:
        return urlparse(url).netloc.replace("www.", "") or url
    except Exception:
        return url


def _normalize_url(url: str) -> str:
    """Scheme/query/fragment-insensitive key for matching the same article."""
    try:
        p = urlparse((url or "").strip())
        host = (p.netloc or "").lower().replace("www.", "")
        path = (p.path or "").rstrip("/")
        return f"{host}{path}"
    except Exception:
        return (url or "").strip().lower()


def _log_usage(stage: str, model: str, usage) -> None:
    if usage is None:
        return
    server = getattr(usage, "server_tool_use", None)
    searches = getattr(server, "web_search_requests", None) if server else None
    logger.info(
        "usage[%s/%s] in=%s out=%s cache_read=%s web_searches=%s",
        stage,
        model,
        getattr(usage, "input_tokens", "?"),
        getattr(usage, "output_tokens", "?"),
        getattr(usage, "cache_read_input_tokens", 0),
        searches if searches is not None else "-",
    )


# ---------------------------------------------------------------------------
# Stage 1: research
# ---------------------------------------------------------------------------


async def research(
    query: str,
    emit: Emit = _noop_emit,
    model: str | None = None,
    effort: str | None = None,
) -> Tuple[str, List[dict]]:
    """Search + read the web and gather grounded notes for `query`.

    `model` / `effort` are optional per-request overrides (fall back to the
    server defaults). Effort also scales the web search/fetch budget.

    Returns (research_notes, sources) where sources is a deduped list of
    {"title", "url", "publisher"} discovered via web search/fetch.
    """
    model = model or RESEARCH_MODEL
    effort = effort or RESEARCH_EFFORT
    tools = _research_tools(effort)

    client = _client()
    messages: List[dict] = [
        {
            "role": "user",
            "content": (
                f"Research this news topic and gather coverage across the "
                f"political spectrum:\n\n{query}"
            ),
        }
    ]

    notes_parts: List[str] = []
    sources: Dict[str, dict] = {}

    async def add_source(url, title) -> None:
        if url and url not in sources:
            sources[url] = {
                "title": title or url,
                "url": url,
                "publisher": _hostname(url),
            }
            await emit("source", {"title": sources[url]["title"], "url": url})

    for _ in range(MAX_CONTINUATIONS):
        async with client.messages.stream(
            model=model,
            max_tokens=16000,
            system=prompts.RESEARCH_SYSTEM,
            thinking={"type": "adaptive", "display": "summarized"},
            output_config={"effort": effort},
            tools=tools,
            messages=messages,
        ) as stream:
            async for event in stream:
                if event.type == "content_block_start":
                    block = event.content_block
                    if getattr(block, "type", None) == "server_tool_use":
                        name = getattr(block, "name", "")
                        label = (
                            "Reading a key article…"
                            if name == "web_fetch"
                            else "Searching the web…"
                        )
                        await emit("status", {"label": label})
                elif event.type == "content_block_delta":
                    delta = event.delta
                    if delta.type == "thinking_delta":
                        await emit("thinking", {"text": delta.thinking})
                    elif delta.type == "text_delta":
                        notes_parts.append(delta.text)
                        await emit("notes", {"text": delta.text})

            final = await stream.get_final_message()

        _log_usage("research", model, getattr(final, "usage", None))

        # Harvest sources from both search results and fetched documents.
        for block in final.content:
            btype = getattr(block, "type", None)
            if btype == "web_search_tool_result":
                results = block.content  # a list on success, an error dict otherwise
                if isinstance(results, list):
                    for r in results:
                        await add_source(getattr(r, "url", None), getattr(r, "title", ""))
            elif btype == "web_fetch_tool_result":
                content = getattr(block, "content", None)
                url = getattr(content, "url", None)
                doc = getattr(content, "content", None)
                await add_source(url, getattr(doc, "title", None))

        if final.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": final.content})
            continue
        break

    return "".join(notes_parts), list(sources.values())


# ---------------------------------------------------------------------------
# Stage 2: synthesize (+ source reconciliation)
# ---------------------------------------------------------------------------


def _reconcile_sources(briefing: Briefing, harvested: List[dict]) -> Briefing:
    """Drop any briefing source that wasn't actually found via web search/fetch.

    The briefing's credibility depends on every cited URL being real. We match
    the model's sources against the harvested set (scheme/query-insensitive),
    canonicalize matched URLs, and discard anything invented. If the model
    produced no valid sources at all, we fall back to listing what was found.
    """
    if not harvested:
        return briefing

    by_norm = {_normalize_url(h["url"]): h for h in harvested}

    validated: List[Source] = []
    seen: set = set()
    dropped = 0
    for s in briefing.sources:
        match = by_norm.get(_normalize_url(s.url))
        if match is None:
            dropped += 1
            continue
        if match["url"] in seen:
            continue
        seen.add(match["url"])
        s.url = match["url"]  # canonical URL we actually fetched
        if not s.publisher:
            s.publisher = match["publisher"]
        validated.append(s)

    if dropped:
        logger.warning("dropped %s unverified source(s) from briefing", dropped)

    if not validated:
        logger.warning("no model sources matched harvest; falling back to harvested")
        validated = [
            Source(
                title=h["title"],
                publisher=h["publisher"],
                url=h["url"],
                lean="unknown",
                takeaway="",
            )
            for h in harvested[:10]
        ]

    briefing.sources = validated
    return briefing


async def synthesize(query: str, notes: str, sources: List[dict]) -> Briefing:
    """Turn research notes + sources into a validated, structured Briefing."""
    client = _client()

    source_lines = "\n".join(
        f"- {s['publisher']}: {s['title']} — {s['url']}" for s in sources
    )
    user_content = (
        f"<topic>{query}</topic>\n\n"
        f"<research_notes>\n{notes}\n</research_notes>\n\n"
        f"<sources>\n{source_lines}\n</sources>\n\n"
        "Produce the structured briefing."
    )

    response = await client.messages.parse(
        model=SYNTHESIS_MODEL,
        max_tokens=8000,
        system=prompts.SYNTHESIS_SYSTEM,
        messages=[{"role": "user", "content": user_content}],
        output_format=Briefing,
        output_config={"effort": SYNTHESIS_EFFORT},
    )
    _log_usage("synthesize", SYNTHESIS_MODEL, getattr(response, "usage", None))
    return _reconcile_sources(response.parsed_output, sources)


# ---------------------------------------------------------------------------
# Stage 3: grounded follow-up chat
# ---------------------------------------------------------------------------


def _grounding_system(query: str, briefing: Briefing | None, notes: str) -> List[dict]:
    """Build a cacheable system prompt carrying the briefing as grounding."""
    grounding_parts = [f"<topic>{query}</topic>"]
    if briefing is not None:
        grounding_parts.append(
            "<briefing>\n" + briefing.model_dump_json(indent=2) + "\n</briefing>"
        )
    if notes:
        grounding_parts.append(f"<research_notes>\n{notes}\n</research_notes>")
    grounding = "\n\n".join(grounding_parts)

    return [
        {"type": "text", "text": prompts.CHAT_SYSTEM},
        # Cache the (large, stable) grounding so multi-turn follow-ups are cheap.
        {"type": "text", "text": grounding, "cache_control": {"type": "ephemeral"}},
    ]


async def chat(
    query: str,
    briefing: Briefing | None,
    notes: str,
    history: List[ChatTurn],
    message: str,
    emit: Emit = _noop_emit,
):
    """Stream a grounded answer to a follow-up question."""
    client = _client()

    messages: List[dict] = [{"role": t.role, "content": t.content} for t in history]
    messages.append({"role": "user", "content": message})

    for _ in range(MAX_CONTINUATIONS):
        async with client.messages.stream(
            model=CHAT_MODEL,
            max_tokens=8000,
            system=_grounding_system(query, briefing, notes),
            thinking={"type": "adaptive"},
            output_config={"effort": CHAT_EFFORT},
            tools=CHAT_TOOLS,
            messages=messages,
        ) as stream:
            async for event in stream:
                if event.type == "content_block_start":
                    block = event.content_block
                    if getattr(block, "type", None) == "server_tool_use":
                        name = getattr(block, "name", "")
                        label = (
                            "Reading a key article…"
                            if name == "web_fetch"
                            else "Searching the web…"
                        )
                        await emit("status", {"label": label})
                elif event.type == "content_block_delta":
                    if event.delta.type == "text_delta":
                        await emit("token", {"text": event.delta.text})

            final = await stream.get_final_message()

        _log_usage("chat", CHAT_MODEL, getattr(final, "usage", None))

        if final.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": final.content})
            continue
        break
