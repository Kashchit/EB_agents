from __future__ import annotations

from typing import Mapping

from ollama_client import chat_completion

SYSTEM = """You are the Devil's Advocate in a board meeting. Your job is to stress-test the plan.
Challenge assumptions, surface blind spots, regulatory or reputational risks, and second-order effects.
Be sharp but constructive: end with what would need to be true for the direction to still make sense.
Use short paragraphs or bullets. Do not be agreeable for its own sake."""


def run_devil(
    problem: str,
    memory_context: str,
    debate_summary: str,
    executive_views: Mapping[str, str],
) -> str:
    parts: list[str] = []
    if memory_context.strip():
        parts.append(memory_context.strip())
    parts.append(f"Business problem:\n{problem.strip()}")
    if debate_summary.strip():
        parts.append(f"Debate / evolution summary:\n{debate_summary.strip()}")
    parts.append("Latest executive positions:")
    for role, text in executive_views.items():
        parts.append(f"--- {role} ---\n{text.strip()}")
    user_message = "\n\n".join(parts)
    return chat_completion(SYSTEM, user_message)
