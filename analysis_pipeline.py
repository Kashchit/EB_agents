from __future__ import annotations

from typing import Any

from agents.devil import run_devil
from board import run_executive_phases
from consensus import synthesize_final_decision
from debate_resolution import brief_resolution, summarize_debate
from config import ENABLE_BRIEF_RESOLUTION, ENABLE_DEBATE_SUMMARY, ENABLE_DEVILS_ADVOCATE
from memory import append_decision

API_AGENT_ORDER = ["CEO", "CFO", "CTO", "CMO", "COO"]


def _validate_problem(problem: str) -> str | None:
    p = (problem or "").strip()
    if not p:
        return "Please enter a business problem (1–3 sentences)."
    if len(p) < 12 and p.lower() in {"hi", "hello", "hey", "test"}:
        return "That looks like a greeting. Please describe a business decision you want the board to make (1–3 sentences)."
    if len(p) < 20:
        return "Please add a bit more detail (goal, constraint, and context). Example: “Should we launch a freemium tier in the EU next quarter?”"
    return None


def stream_web_analysis(problem: str, save_to_memory: bool = True):
    """Generator yielding messages one by one as they are generated."""
    msg = _validate_problem(problem)
    if msg:
        yield {"role": "System", "content": msg}
        return

    # Phase 1: Executives
    problem, memory_block, round1, round2, final_views = run_executive_phases(problem)
    
    # Yield each agent view immediately
    for role in API_AGENT_ORDER:
        if role in final_views:
            yield {"role": role, "content": final_views[role]}

    # Optional debate summary (extra call)
    if ENABLE_DEBATE_SUMMARY:
        round2_or_none = round2 if round2 else None
        debate_text = summarize_debate(problem, round1, round2_or_none)
        yield {"role": "Debate", "content": debate_text}
    else:
        debate_text = ""

    # Optional Devil's Advocate (extra call)
    devil_text = ""
    if ENABLE_DEVILS_ADVOCATE:
        devil_text = run_devil(problem, memory_block, debate_text, final_views)
        yield {"role": "Devil", "content": devil_text}

    # Phase 4: Final Decision
    consensus_text = synthesize_final_decision(problem, final_views, devil_text)
    if ENABLE_BRIEF_RESOLUTION:
        resolution_text = brief_resolution(consensus_text)
        yield {"role": "Resolution", "content": resolution_text}
    
    # Final Full Report Signal
    if save_to_memory and consensus_text.strip():
        append_decision(problem, consensus_text.strip())
    
    yield {"role": "FinalReport", "content": consensus_text.strip()}


def run_web_analysis(problem: str, save_to_memory: bool = True) -> dict[str, Any]:
    """Legacy synchronous wrapper for the stream."""
    messages = []
    final_report = ""
    for chunk in stream_web_analysis(problem, save_to_memory):
        if chunk["role"] == "FinalReport":
            final_report = chunk["content"]
        else:
            messages.append(chunk)
    return {"messages": messages, "finalReport": final_report}
