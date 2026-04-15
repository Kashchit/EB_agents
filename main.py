"""
Entry point: interactive CLI for the personality-driven multi-agent board.

Prerequisites:
- Install Ollama (https://ollama.com) and run `ollama pull llama3` (or set OLLAMA_MODEL).
- `pip install -r requirements.txt`

Run:  python main.py
"""
from __future__ import annotations

import argparse
import sys

from board import format_result_for_print, run_board


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Virtual executive board powered by Ollama (multi-agent business decisions)."
    )
    parser.add_argument(
        "problem",
        nargs="?",
        default=None,
        help="Business problem in one argument (optional; otherwise prompts interactively).",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Do not append this run to decision_memory.json.",
    )
    args = parser.parse_args()

    print("\nPersonality-Driven Multi-Agent AI — Executive Board (Ollama)\n")
    print("Roles: CEO, CFO, CMO, CTO, COO → consensus synthesis.\n")

    if args.problem:
        problem = args.problem
    else:
        print("Describe your business problem (end with a blank line or Ctrl+Z then Enter on Windows):\n")
        lines: list[str] = []
        try:
            while True:
                line = input()
                if line == "" and lines:
                    break
                lines.append(line)
        except EOFError:
            pass
        problem = "\n".join(lines).strip()
        if not problem:
            print("No problem text provided. Exiting.", file=sys.stderr)
            sys.exit(1)

    try:
        result = run_board(problem, save_to_memory=not args.no_save)
    except Exception as exc:  # noqa: BLE001 — beginner-friendly surface for connection errors
        print(
            "\nError talking to Ollama. Is the server running (`ollama serve`) and the model installed?\n"
            f"Details: {exc}\n",
            file=sys.stderr,
        )
        sys.exit(2)

    print(format_result_for_print(result))


if __name__ == "__main__":
    main()
