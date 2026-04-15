"""
Optional Streamlit UI for the executive board.

Run:  streamlit run streamlit_app.py

Requires the same Ollama setup as main.py.
"""
from __future__ import annotations

import streamlit as st

from board import format_result_for_print, run_board


def main() -> None:
    st.set_page_config(page_title="Executive Board (Ollama)", layout="wide")
    st.title("Personality-Driven Executive Board")
    st.caption("CEO · CFO · CMO · CTO · COO — powered by Ollama (llama3 by default)")

    problem = st.text_area(
        "Business problem",
        height=180,
        placeholder="Example: Should we launch a freemium tier in the EU market this quarter?",
    )
    save = st.checkbox("Save outcome to memory (simple RAG file)", value=True)

    if st.button("Run board", type="primary"):
        if not problem.strip():
            st.warning("Enter a business problem first.")
            return
        with st.spinner("Consulting executives and synthesizing consensus…"):
            try:
                result = run_board(problem.strip(), save_to_memory=save)
            except Exception as exc:  # noqa: BLE001
                st.error(f"Ollama error: {exc}")
                st.info("Ensure `ollama serve` is running and your model is pulled.")
                return

        if result.memory_context_used.strip():
            with st.expander("Memory context used (similar past cases)"):
                st.markdown(result.memory_context_used)

        st.subheader("Round 1 — independent views")
        for role, text in result.round1.items():
            with st.expander(role):
                st.markdown(text)

        if result.round2:
            st.subheader("Round 2 — after seeing peers")
            for role, text in result.round2.items():
                with st.expander(role):
                    st.markdown(text)

        st.subheader("Final decision (consensus)")
        st.markdown(result.consensus or "_Empty response — check Ollama._")

        st.download_button(
            "Download full report (text)",
            data=format_result_for_print(result),
            file_name="board_report.txt",
            mime="text/plain",
        )


if __name__ == "__main__":
    main()
