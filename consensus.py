"""
Consensus step: one more call to Ollama that reads every executive's view and outputs a single plan.

This simulates the CEO/chair synthesizing the board — we still use the language model, but with
a prompt focused on integration rather than a single functional silo.
"""
from __future__ import annotations

from typing import Mapping

from ollama_client import chat_completion

CONSENSUS_SYSTEM = """You are the board chair synthesizing a multi-executive discussion into an actionable decision.

CRITICAL RULE #0 — TOPIC FOCUS: Your entire response must be about the SPECIFIC business problem stated below.
Do NOT introduce topics, industries, or solutions not mentioned in the problem (e.g., if the question is about hiring, do not discuss delivery routing, CRM systems, or smart lockers).

Your job:
1. Acknowledge key tensions (e.g., growth vs. risk, speed vs. quality).
2. Produce ONE clear recommendation a leadership team could act on this quarter.
3. Call out major risks and how to mitigate them — specific to THIS problem only.
4. List 3–7 concrete next steps with owners implied by role (CEO/CFO/CMO/CTO/COO).

Quality bar:
- Ground every section in the actual problem constraints; avoid generic advice.
- Do NOT invent financial numbers unless the problem already provided them.
- If the problem is underspecified, include a short "Open questions" section with up to 3 questions.
- Keep the whole response under ~200 lines; prefer concise bullets.

Output format (use these exact headings):
## Executive summary
## Recommended decision
## Rationale (how you balanced conflicting views)
## Risks and mitigations
## Next steps (numbered)
## What we should measure
## Open questions (if needed)
"""


def build_consensus_user_message(
    problem: str,
    agent_outputs: Mapping[str, str],
    devil_critique: str | None = None,
) -> str:
    parts = [
        f"Business problem:\n{problem}\n",
        "Individual executive inputs:\n",
    ]
    for role, text in agent_outputs.items():
        parts.append(f"### {role}\n{text}\n")
    if devil_critique and devil_critique.strip():
        parts.append("### Devil's Advocate critique\n")
        parts.append(devil_critique.strip() + "\n")
    parts.append(
        "\nSynthesize the above into the structured final decision requested in your system instructions."
    )
    return "\n".join(parts)


def synthesize_final_decision(
    problem: str,
    agent_outputs: Mapping[str, str],
    devil_critique: str | None = None,
) -> str:
    user_msg = build_consensus_user_message(problem, agent_outputs, devil_critique)
    return chat_completion(CONSENSUS_SYSTEM, user_msg)
