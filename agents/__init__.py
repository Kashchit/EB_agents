"""
Executive agents: one module per role so prompts stay easy to find and edit.

Each agent exposes a small class with the same interface: .respond(...)
"""
from agents.ceo import CEOAgent
from agents.cfo import CFOAgent
from agents.cmo import CMOAgent
from agents.coo import COOAgent
from agents.cto import CTOAgent

__all__ = [
    "CEOAgent",
    "CFOAgent",
    "CMOAgent",
    "CTOAgent",
    "COOAgent",
]
