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

    problem = problem.strip()
    from memory import retrieve_similar, format_memory_context
    similar = retrieve_similar(problem)
    memory_block = format_memory_context(similar)

    # Phase 1: Executives (Parallel execution with streaming yield)
    from board import AGENT_CLASSES, _run_one_agent
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    final_views = {}
    with ThreadPoolExecutor(max_workers=len(AGENT_CLASSES)) as executor:
        futures = {
            executor.submit(_run_one_agent, cls, problem, memory_block, None): cls.role_name
            for cls in AGENT_CLASSES
        }
        for future in as_completed(futures):
            role, text = future.result()
            final_views[role] = text
            yield {"role": role, "content": text}

    # Optional debate summary
    debate_text = ""
    if ENABLE_DEBATE_SUMMARY:
        debate_text = summarize_debate(problem, final_views, None)
        yield {"role": "Debate", "content": debate_text}

    # Optional Devil's Advocate
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
