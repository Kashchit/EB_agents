"""
Thin wrapper around the Ollama Python client.

Keeps all model calls in one place so beginners can swap models or add logging easily.
"""
from __future__ import annotations

from typing import List

import ollama

from config import OLLAMA_MODEL, OLLAMA_NUM_PREDICT, OLLAMA_TEMPERATURE


def _extract_message_content(response: object) -> str:
    """Support both dict-shaped and object-shaped responses from ollama-python."""
    if isinstance(response, dict):
        msg = response.get("message") or {}
        if isinstance(msg, dict):
            return str(msg.get("content", "")).strip()
        return str(getattr(msg, "content", "") or "").strip()
    msg = getattr(response, "message", None)
    if msg is not None:
        return str(getattr(msg, "content", "") or "").strip()
    return str(response).strip()


def chat_completion(
    system_prompt: str,
    user_message: str,
    model: str | None = None,
) -> str:
    """
    Send a chat request to Ollama and return the assistant's text.

    system_prompt: instructions that define the agent's role and personality.
    user_message: the actual business problem (plus any extra context we add).
    """
    use_model = model or OLLAMA_MODEL
    messages: List[dict] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    response = ollama.chat(
        model=use_model,
        messages=messages,
        options={
            "temperature": OLLAMA_TEMPERATURE,
            "num_predict": OLLAMA_NUM_PREDICT,
        },
    )
    return _extract_message_content(response)


if __name__ == "__main__":
    try:
        text = chat_completion(
            "You are a helpful assistant. Reply briefly.",
            "Say hello in one short sentence.",
        )
        print(text)
    except Exception as exc:  # pragma: no cover - smoke test entrypoint
        print(f"Ollama chat failed: {exc}")
        print(
            "Tip: ensure `ollama serve` is running, pull a model "
            f"(e.g. `ollama pull {OLLAMA_MODEL}`), or set OLLAMA_MODEL to a tag you have."
        )
        raise SystemExit(1) from exc
