"""
Simple "memory" for past board decisions.

This is a beginner-friendly RAG-style helper: we store problems and outcomes in a JSON file
and retrieve the most similar past entries using word overlap (no embeddings required).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Sequence

from config import MEMORY_PATH, TOP_K_SIMILAR


def _tokenize(text: str) -> set[str]:
    """Lowercase words for rough similarity (good enough for a teaching project)."""
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def similarity_score(a: str, b: str) -> float:
    """
    Jaccard similarity over word sets: |A ∩ B| / |A ∪ B|.
    Returns 0.0 if both are empty.
    """
    sa, sb = _tokenize(a), _tokenize(b)
    if not sa and not sb:
        return 0.0
    inter = len(sa & sb)
    union = len(sa | sb) or 1
    return inter / union


def _ensure_memory_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("[]", encoding="utf-8")


def load_memory(path: Path | None = None) -> list[dict[str, Any]]:
    """Load all stored records from disk."""
    p = path or MEMORY_PATH
    _ensure_memory_file(p)
    raw = p.read_text(encoding="utf-8").strip() or "[]"
    data = json.loads(raw)
    if not isinstance(data, list):
        return []
    return data


def save_memory(records: list[dict[str, Any]], path: Path | None = None) -> None:
    """Overwrite the memory file with the given list."""
    p = path or MEMORY_PATH
    _ensure_memory_file(p)
    p.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")


@dataclass
class RetrievedCase:
    """One past problem/decision pair surfaced for the prompt."""

    problem: str
    final_decision: str
    score: float


def retrieve_similar(problem: str, k: int | None = None, path: Path | None = None) -> list[RetrievedCase]:
    """
    Find up to k past cases most similar to the current business problem.

    Similarity is lexical (shared words), which is easy to understand and requires no API keys.
    """
    k = TOP_K_SIMILAR if k is None else k
    records = load_memory(path)
    scored: list[tuple[float, dict[str, Any]]] = []
    for rec in records:
        past_problem = str(rec.get("problem", ""))
        score = similarity_score(problem, past_problem)
        scored.append((score, rec))
    scored.sort(key=lambda x: x[0], reverse=True)
    out: list[RetrievedCase] = []
    for score, rec in scored[:k]:
        if score <= 0:
            continue
        out.append(
            RetrievedCase(
                problem=str(rec.get("problem", "")),
                final_decision=str(rec.get("final_decision", "")),
                score=score,
            )
        )
    return out


def format_memory_context(cases: Sequence[RetrievedCase]) -> str:
    """Turn retrieved cases into a short block we can paste into agent prompts."""
    if not cases:
        return ""
    lines = [
        "Relevant past board decisions (use as reference only; the current problem may differ):",
    ]
    for i, c in enumerate(cases, start=1):
        lines.append(f"\n--- Case {i} (similarity ~{c.score:.2f}) ---")
        lines.append(f"Past problem: {c.problem}")
        lines.append(f"Past outcome summary: {c.final_decision[:1200]}")
    return "\n".join(lines)


def append_decision(problem: str, final_decision: str, path: Path | None = None) -> None:
    """Save a new decision so future runs can retrieve it."""
    p = path or MEMORY_PATH
    records = load_memory(p)
    records.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "problem": problem,
            "final_decision": final_decision,
        }
    )
    save_memory(records, p)
