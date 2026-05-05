"""
Shared base class for all C-suite agents.

Beginners: every agent shares the same mechanics (call Ollama); only the SYSTEM prompt changes.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Mapping

from ollama_client import chat_completion


class BaseExecutiveAgent(ABC):
    """Abstract agent: subclass sets role_name and system prompt."""

    role_name: str = "Executive"

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Role-specific instructions sent as the system message."""
        raise NotImplementedError

    def _build_user_message(
        self,
        problem: str,
        memory_context: str,
        peer_round1: Mapping[str, str] | None,
    ) -> str:
        """
        Combine the business problem with optional memory and peer viewpoints.

        memory_context: formatted similar past cases (may be empty string).
        peer_round1: other agents' first-round answers when we run a second pass.
        """
        chunks = []
        if memory_context.strip():
            chunks.append(memory_context.strip())
            chunks.append("")
        chunks.append("Current business problem to address:")
        chunks.append(problem.strip())
        if peer_round1:
            chunks.append("")
            chunks.append(
                "You can see the other executives' FIRST-round views below. "
                "Update your recommendation if needed; note agreements and disagreements briefly."
            )
            for role, text in peer_round1.items():
                if role == self.role_name:
                    continue
                chunks.append(f"\n--- {role} (first round) ---\n{text.strip()}")
        return "\n".join(chunks)

    def respond(
        self,
        problem: str,
        memory_context: str = "",
        peer_round1: Mapping[str, str] | None = None,
    ) -> str:
        """Generate this executive's analysis/recommendation."""
        user_message = self._build_user_message(problem, memory_context, peer_round1)
        system = (
            self.system_prompt.strip()
            + "\n\n"
            + "CRITICAL RULES — violating any of these is a failure:\n"
            + "1. STAY ON TOPIC: Every sentence must directly address the stated problem. "
            + "Never drift into unrelated topics (e.g., do not discuss delivery logistics if the question is about hiring).\n"
            + "2. NO GENERIC PLAYBOOKS: Do not copy-paste standard frameworks. "
            + "Reference the specific context of THIS problem only.\n"
            + "3. NO INVENTED NUMBERS: Do not invent revenue figures, percentages, or timelines "
            + "unless they were explicitly given in the problem statement.\n"
            + "4. MISSING INFO: If you lack critical details, state 1–2 explicit assumptions, then give your view.\n"
            + "5. LENGTH: 8–14 lines maximum. Use crisp bullets. Stop when done — do not pad.\n"
        )
        return chat_completion(system, user_message)
