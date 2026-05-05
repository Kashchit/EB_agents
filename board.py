"""
Orchestrates the virtual executive board: parallel first opinions, optional second round
with shared context, then consensus.

Beginners: this file is the "conductor" — agents are instruments; consensus is the finale.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Tuple, Type

from agents import CEOAgent, CFOAgent, CMOAgent, COOAgent, CTOAgent
from agents.base import BaseExecutiveAgent
from config import ENABLE_CROSS_AGENT_CONTEXT
from consensus import synthesize_final_decision
from memory import append_decision, format_memory_context, retrieve_similar

# Fixed order for predictable printing and prompts (classes are callable factories).
AGENT_CLASSES: List[Type[BaseExecutiveAgent]] = [
    CEOAgent,
    CFOAgent,
    CTOAgent,
    CMOAgent,
    COOAgent,
]


def _run_one_agent(
    cls: Type[BaseExecutiveAgent],
    problem: str,
    memory_context: str,
    peer_round1: Mapping[str, str] | None,
) -> Tuple[str, str]:
    """Fresh instance per call — safe when multiple threads hit Ollama at once."""
    agent = cls()
    return agent.role_name, agent.respond(problem, memory_context, peer_round1)


@dataclass
class BoardResult:
    """Everything the CLI or UI needs to render."""

    problem: str
    memory_context_used: str
    round1: Dict[str, str] = field(default_factory=dict)
    round2: Dict[str, str] = field(default_factory=dict)
    final_agent_views: Dict[str, str] = field(default_factory=dict)
    consensus: str = ""

    def views_for_consensus(self) -> Dict[str, str]:
        """Prefer refined round-2 statements when present."""
        if self.round2:
            return self.round2
        return self.round1


def _run_parallel(
    problem: str,
    memory_context: str,
    peer_round1: Mapping[str, str] | None,
) -> Dict[str, str]:
    """Call each agent in parallel using threads."""
    results: Dict[str, str] = {}
    
    with ThreadPoolExecutor(max_workers=len(AGENT_CLASSES)) as executor:
        future_to_role = {
            executor.submit(_run_one_agent, cls, problem, memory_context, peer_round1): cls.role_name
            for cls in AGENT_CLASSES
        }
        
        for future in as_completed(future_to_role):
            role = future_to_role[future]
            try:
                _, text = future.result()
                results[role] = text
            except Exception as exc:
                print(f"Agent {role} generated an exception: {exc}")
                results[role] = f"Error generating response: {exc}"
    
    return results


def run_executive_phases(
    problem: str,
) -> tuple[str, str, Dict[str, str], Dict[str, str], Dict[str, str]]:
    problem = problem.strip()
    similar = retrieve_similar(problem)
    memory_block = format_memory_context(similar)
    round1 = _run_parallel(problem, memory_block, peer_round1=None)
    round2: Dict[str, str] = {}
    if ENABLE_CROSS_AGENT_CONTEXT:
        round2 = _run_parallel(problem, memory_block, peer_round1=round1)
    final_views = round2 if round2 else round1
    return problem, memory_block, round1, round2, final_views


def run_board(problem: str, save_to_memory: bool = True) -> BoardResult:
    problem, memory_block, round1, round2, final_views = run_executive_phases(problem)
    consensus_text = synthesize_final_decision(problem, final_views)

    if save_to_memory and consensus_text.strip():
        append_decision(problem, consensus_text.strip())

    return BoardResult(
        problem=problem,
        memory_context_used=memory_block,
        round1=round1,
        round2=round2,
        final_agent_views=final_views,
        consensus=consensus_text.strip(),
    )


def format_result_for_print(result: BoardResult) -> str:
    """Plain-text report for the CLI."""
    lines: List[str] = []
    lines.append("=" * 72)
    lines.append("BUSINESS PROBLEM")
    lines.append("=" * 72)
    lines.append(result.problem)
    if result.memory_context_used.strip():
        lines.append("")
        lines.append("-" * 72)
        lines.append("MEMORY / PAST SIMILAR CASES (injected into prompts)")
        lines.append("-" * 72)
        lines.append(result.memory_context_used)
    lines.append("")
    lines.append("=" * 72)
    lines.append("EXECUTIVE INPUTS — ROUND 1 (independent views)")
    lines.append("=" * 72)
    for role, text in result.round1.items():
        lines.append(f"\n>>> {role}\n")
        lines.append(text.strip())
    if result.round2:
        lines.append("\n")
        lines.append("=" * 72)
        lines.append("EXECUTIVE INPUTS — ROUND 2 (after seeing peers)")
        lines.append("=" * 72)
        for role, text in result.round2.items():
            lines.append(f"\n>>> {role}\n")
            lines.append(text.strip())
    lines.append("\n")
    lines.append("=" * 72)
    lines.append("FINAL BOARD DECISION (consensus synthesis)")
    lines.append("=" * 72)
    lines.append(result.consensus or "(empty response — check Ollama is running and model is pulled.)")
    lines.append("")
    return "\n".join(lines)
