"""Pydantic schemas for the news-intelligence API.

These define the structured `Briefing` that Claude produces via the
Messages API structured-outputs feature, plus the request/response models
for the HTTP layer.

Kept deliberately simple (str / list / enum only) so the JSON schema stays
within the subset supported by `output_config.format` — no min/max length,
no numeric bounds, no recursion.
"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

# A coarse left→right political lean. Used both for individual outlets and for
# grouping how "sides" are covering a story.
Lean = Literal[
    "left",
    "center-left",
    "center",
    "center-right",
    "right",
    "unknown",
]


class Source(BaseModel):
    """A single article/outlet that informed the briefing."""

    title: str = Field(description="Headline of the article.")
    publisher: str = Field(description="Name of the outlet, e.g. 'Reuters'.")
    url: str = Field(description="Canonical URL of the article.")
    lean: Lean = Field(
        description="Editorial lean of the OUTLET (not the article's tone)."
    )
    takeaway: str = Field(
        description="One sentence on what this source emphasizes or adds."
    )


class ContestedClaim(BaseModel):
    """A claim that sources disagree on, or that is unverified."""

    claim: str = Field(description="The disputed or unverified claim.")
    status: Literal["disputed", "unverified", "misleading", "evolving"] = Field(
        description="Why this claim is not settled fact."
    )
    detail: str = Field(
        description="Who is asserting/disputing it and the current state of evidence."
    )


class SideFraming(BaseModel):
    """How one part of the spectrum is framing the story."""

    side: Literal["left", "center", "right"] = Field(
        description="Which part of the spectrum this framing represents."
    )
    narrative: str = Field(
        description="The through-line / angle this side leads with."
    )
    emphasis: List[str] = Field(
        description="Specific points this side foregrounds.",
        default_factory=list,
    )
    omits: str = Field(
        description="What this side tends to downplay or leave out.",
    )


class Briefing(BaseModel):
    """The full structured briefing rendered by the frontend."""

    headline: str = Field(description="A neutral, descriptive headline.")
    summary: str = Field(
        description="A neutral 2-4 sentence executive summary of what is happening."
    )
    key_facts: List[str] = Field(
        description="Claims that are well-sourced and broadly agreed upon.",
        default_factory=list,
    )
    contested_claims: List[ContestedClaim] = Field(
        description="Claims that are disputed, evolving, or unverified.",
        default_factory=list,
    )
    framing_by_side: List[SideFraming] = Field(
        description="How left, center, and right are each covering the story.",
        default_factory=list,
    )
    blind_spots: List[str] = Field(
        description="Important context most coverage is missing entirely.",
        default_factory=list,
    )
    sources: List[Source] = Field(
        description="The outlets/articles this briefing draws on, spanning the spectrum.",
        default_factory=list,
    )
    follow_up_questions: List[str] = Field(
        description="3-4 sharp questions the reader might ask next.",
        default_factory=list,
    )


# ---------------------------------------------------------------------------
# HTTP request models
# ---------------------------------------------------------------------------


# What the user is allowed to pick for the research stage. Restricted to models
# that support the modern web tools + effort parameter.
ResearchModel = Literal["claude-opus-4-8", "claude-sonnet-4-6"]
Effort = Literal["low", "medium", "high"]


class BriefingRequest(BaseModel):
    # Length cap guards against runaway/abusive inputs (each briefing spends
    # Opus + web-search budget).
    query: str = Field(min_length=1, max_length=500)
    # Optional per-request overrides for the research stage (None → server
    # default). Effort also scales the web search/fetch budget.
    model: Optional[ResearchModel] = None
    effort: Optional[Effort] = None


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=8000)


class ChatRequest(BaseModel):
    query: str = Field(max_length=500)
    """The original topic the briefing was about (used to ground the chat)."""
    briefing: Optional[Briefing] = None
    """The briefing the user is asking follow-ups about."""
    research_notes: str = Field(default="", max_length=100_000)
    """Raw research context gathered during the briefing (RAG grounding)."""
    history: List[ChatTurn] = Field(default_factory=list, max_length=40)
    message: str = Field(min_length=1, max_length=2000)
    """The new user message."""
