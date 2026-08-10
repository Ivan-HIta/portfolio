"""Transparent, offline proxy evaluation for synthetic LLM/RAG-style answers."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from app import (
    configure_page,
    data_source_label,
    evaluate_llm_outputs,
    get_llm_eval_data,
    inject_styles,
    render_page_header,
    render_sidebar_context,
    render_synthetic_disclaimer,
    set_llm_eval_data,
)


configure_page("LLM Output Evaluation · AI Governance Toolkit")
inject_styles()
render_sidebar_context()
render_page_header(
    "LLM Output Evaluation",
    "Use an inspectable synthetic evaluation set to screen context coverage, relevance, answer length, and unsupported-claim proxies.",
    "LLM / RAG validation",
)


def _upload_controls() -> None:
    with st.sidebar:
        st.markdown("### Synthetic evaluation input")
        upload = st.file_uploader("Optional synthetic LLM evaluation CSV", type=["csv"], key="llm_evaluation_upload")
        if upload is not None:
            signature = (upload.name, upload.size)
            if st.session_state.get("uploaded_llm_signature") != signature:
                try:
                    uploaded_data = pd.read_csv(upload)
                    set_llm_eval_data(uploaded_data, f"Uploaded synthetic CSV · {upload.name}")
                    st.session_state["uploaded_llm_signature"] = signature
                    st.success("Synthetic LLM evaluation data loaded for this browser session.")
                except (UnicodeDecodeError, pd.errors.ParserError) as error:
                    st.error(f"Could not read the CSV: {error}")
        if st.button("Restore bundled LLM evaluation data", use_container_width=True):
            for key in ("llm_eval_data", "llm_eval_source", "llm_evaluation", "uploaded_llm_signature"):
                st.session_state.pop(key, None)
            st.rerun()


_upload_controls()
data = get_llm_eval_data()
render_synthetic_disclaimer(compact=True)
st.caption(f"Active data source: {data_source_label('llm')} · {len(data):,} synthetic prompts")

evaluation = evaluate_llm_outputs(data)
summary = evaluation["summary"]
results = evaluation["results"].copy()

st.markdown("### Evaluation snapshot")
columns = st.columns(6)
columns[0].metric("Answers screened", f"{summary['rows']:,}")
columns[1].metric("Keyword coverage", f"{summary['mean_keyword_coverage']:.1%}")
columns[2].metric("Relevance proxy", f"{summary['mean_relevance']:.1%}")
columns[3].metric("Human rating", f"{summary['mean_human_rating']:.2f} / 5")
columns[4].metric("Missing-context warnings", f"{summary['missing_context_rate']:.1%}")
columns[5].metric("Unsupported-claim proxy", f"{summary['hallucination_proxy_rate']:.1%}")

left, right = st.columns((1, 1), gap="large")
with left:
    st.markdown("### Coverage and relevance")
    figure = px.scatter(
        results,
        x="keyword_coverage",
        y="relevance_proxy_score",
        size="answer_length",
        color="human_rating",
        hover_data=["evaluation_id", "missing_context_warning", "hallucination_proxy"],
        labels={
            "keyword_coverage": "Keyword coverage",
            "relevance_proxy_score": "Relevance proxy score",
            "human_rating": "Human rating",
            "answer_length": "Answer words",
        },
        color_continuous_scale="Blues",
    )
    figure.add_vline(x=0.67, line_dash="dash", line_color="#e9a23b")
    figure.update_layout(height=405, margin=dict(l=20, r=20, t=25, b=20))
    st.plotly_chart(figure, use_container_width=True)
with right:
    st.markdown("### Warning distribution")
    warnings = pd.DataFrame(
        {
            "indicator": ["Missing context", "Unsupported-claim proxy", "No warning"],
            "answers": [
                int(results["missing_context_warning"].sum()),
                int(results["hallucination_proxy"].sum()),
                int((~results["missing_context_warning"] & ~results["hallucination_proxy"]).sum()),
            ],
        }
    )
    figure = px.bar(
        warnings,
        x="indicator",
        y="answers",
        text="answers",
        color="indicator",
        color_discrete_map={"Missing context": "#e9a23b", "Unsupported-claim proxy": "#d1495b", "No warning": "#2a9d8f"},
        labels={"indicator": "", "answers": "Synthetic answers"},
    )
    figure.update_traces(textposition="outside")
    figure.update_layout(height=405, margin=dict(l=20, r=20, t=25, b=20), showlegend=False)
    st.plotly_chart(figure, use_container_width=True)

st.markdown("### Answer-length and rating distribution")
left, right = st.columns((1, 1), gap="large")
with left:
    figure = px.histogram(
        results,
        x="answer_length",
        color="missing_context_warning",
        nbins=18,
        barmode="overlay",
        opacity=0.72,
        labels={"answer_length": "Answer length (words)", "missing_context_warning": "Missing-context warning"},
        color_discrete_map={False: "#315cbd", True: "#e9a23b"},
    )
    figure.update_layout(height=320, margin=dict(l=20, r=20, t=25, b=20))
    st.plotly_chart(figure, use_container_width=True)
with right:
    rating_counts = results["human_rating"].value_counts().sort_index().rename_axis("rating").reset_index(name="answers")
    figure = px.bar(
        rating_counts,
        x="rating",
        y="answers",
        text="answers",
        labels={"rating": "Human rating (1–5)", "answers": "Synthetic answers"},
        color_discrete_sequence=["#7b61a8"],
    )
    figure.update_traces(textposition="outside")
    figure.update_layout(height=320, margin=dict(l=20, r=20, t=25, b=20), showlegend=False)
    st.plotly_chart(figure, use_container_width=True)

st.markdown("### Review queue")
show_only = st.checkbox("Show only answers with a warning", value=True)
queue = results.loc[
    (results["missing_context_warning"] | results["hallucination_proxy"]) if show_only else pd.Series(True, index=results.index)
].copy()
queue["warning_reason"] = ""
queue.loc[queue["missing_context_warning"], "warning_reason"] += "Missing context; "
queue.loc[queue["hallucination_proxy"], "warning_reason"] += "Unsupported-claim proxy;"
queue = queue.sort_values(["hallucination_proxy", "missing_context_warning", "relevance_proxy_score"], ascending=[False, False, True])
display_columns = [
    "evaluation_id",
    "prompt",
    "expected_context",
    "model_answer",
    "human_rating",
    "keyword_coverage",
    "context_overlap",
    "relevance_proxy_score",
    "warning_reason",
]
st.dataframe(
    queue.loc[:, display_columns].style.format(
        {"keyword_coverage": "{:.1%}", "context_overlap": "{:.1%}", "relevance_proxy_score": "{:.1%}"}
    ),
    use_container_width=True,
    hide_index=True,
    height=420,
)
st.download_button(
    "Download LLM evaluation evidence (CSV)",
    data=results.to_csv(index=False).encode("utf-8"),
    file_name="synthetic_llm_output_evaluation.csv",
    mime="text/csv",
)

with st.expander("How the transparent proxy checks work"):
    st.markdown(
        """
        - **Keyword coverage:** share of expected synthetic keywords found in the answer.
        - **Missing-context warning:** triggered when keyword coverage or simple context-token overlap is low.
        - **Unsupported-claim proxy:** triggered by a small set of absolute or guarantee-like phrases in this synthetic sample.
        - **Relevance proxy:** a documented combination of coverage and context overlap, reduced when an unsupported-claim proxy appears.

        These are lightweight validation signals, not semantic truth, safety, or hallucination guarantees. A production evaluation should include curated scenarios, domain-expert grading, adverse-case testing, traceability, and continuous monitoring.
        """
    )

