from __future__ import annotations

from typing import Mapping

from ollama_client import chat_completion

DEBATE_SYSTEM = """You summarize how the executive team debated.
Describe where they aligned, where they clashed (e.g., growth vs. risk, speed vs. quality), and how positions evolved between round 1 and round 2 if both exist.
Write as one cohesive narrative suitable for a group chat message: 2–4 short paragraphs, no role-play prefixes."""

RESOLUTION_SYSTEM = """You write a concise board resolution: 4–7 sentences that capture the decision, key trade-offs accepted, and what happens next.
Do not repeat the full long report; be crisp and authoritative. No markdown headings."""


def _format_views(views: Mapping[str, str]) -> str:
    blocks = []
    for role, text in views.items():
        blocks.append(f"{role}:\n{text.strip()}")
    return "\n\n".join(blocks)


def summarize_debate(
    problem: str,
    round1: Mapping[str, str],
    round2: Mapping[str, str] | None,
) -> str:
    body = f"Business problem:\n{problem.strip()}\n\n"
    body += "Round 1 executive views:\n" + _format_views(round1) + "\n\n"
    if round2 and len(round2) > 0:
        body += "Round 2 executive views (after seeing peers):\n" + _format_views(round2)
    else:
        body += "There was only one round of executive views (no second round)."
    return chat_completion(DEBATE_SYSTEM, body)


def brief_resolution(full_consensus_report: str) -> str:
    return chat_completion(
        RESOLUTION_SYSTEM,
        f"Full structured board report:\n\n{full_consensus_report.strip()}",
    )
