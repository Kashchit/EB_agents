"""
Central settings for the executive board system.
Change the model name here if you use a different Ollama tag (e.g. llama3:8b).
"""
import os
from pathlib import Path

# Ollama model used for every agent and the consensus step
# llama3.2:3b gives much better reasoning than 1b; override with OLLAMA_MODEL env var.
# To use a larger model: export OLLAMA_MODEL=llama3:8b  (then `ollama pull llama3:8b`)
OLLAMA_MODEL: str = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")

# Generation knobs
# num_predict: 2048 prevents answers from being cut off mid-thought
# temperature: 0.3 reduces hallucination (small models drift badly at 0.7)
OLLAMA_NUM_PREDICT: int = int(os.environ.get("OLLAMA_NUM_PREDICT", "2048"))
OLLAMA_TEMPERATURE: float = float(os.environ.get("OLLAMA_TEMPERATURE", "0.3"))

# Where past decisions are stored (simple JSON file for beginner-friendly RAG)
MEMORY_PATH: Path = Path(__file__).resolve().parent / "data" / "decision_memory.json"

# How many similar past cases to inject into prompts (0 disables retrieval text)
TOP_K_SIMILAR: int = int(os.environ.get("TOP_K_SIMILAR", "1"))

# Minimum Jaccard similarity score (0–1) for a past case to be injected.
# Below this threshold the memory is considered unrelated and is NOT injected,
# which prevents answers from a different topic leaking into the current question.
SIMILARITY_THRESHOLD: float = float(os.environ.get("SIMILARITY_THRESHOLD", "0.15"))

# If True, run a second round where each agent sees others' first-round answers
ENABLE_CROSS_AGENT_CONTEXT: bool = os.environ.get("ENABLE_CROSS_AGENT_CONTEXT", "0") not in (
    "0",
    "false",
    "False",
)

# Extra phases (default off for speed; UI/API can enable)
ENABLE_DEBATE_SUMMARY: bool = os.environ.get("ENABLE_DEBATE_SUMMARY", "0") not in (
    "0",
    "false",
    "False",
)
ENABLE_DEVILS_ADVOCATE: bool = os.environ.get("ENABLE_DEVILS_ADVOCATE", "0") not in (
    "0",
    "false",
    "False",
)
ENABLE_BRIEF_RESOLUTION: bool = os.environ.get("ENABLE_BRIEF_RESOLUTION", "1") not in (
    "0",
    "false",
    "False",
)
