"""Generate a portable Markdown governance record from current local evidence."""

from __future__ import annotations

import streamlit as st

from app import (
    configure_page,
    get_drift_profile,
    get_validation_bundle,
    inject_styles,
    model_card_markdown,
    render_page_header,
    render_sidebar_context,
    render_synthetic_disclaimer,
)


configure_page("Model Card Generator · AI Governance Toolkit")
inject_styles()
render_sidebar_context()
render_page_header(
    "Model Card Generator",
    "Convert current synthetic validation evidence into a concise Markdown artifact that supports review, ownership, and change-control conversations.",
    "Governance artifact",
)
render_synthetic_disclaimer(compact=True)

validation = get_validation_bundle()
if not validation.get("available"):
    st.error(validation.get("message", "Validation artifacts could not be created."))
    st.stop()

st.markdown("### Card configuration")
left, middle, right = st.columns((0.45, 0.30, 0.25))
with left:
    selected_model = st.selectbox("Validated model", list(validation["models"]), key="model_card_model_choice")
with middle:
    owner = st.text_input("Proposed accountable owner", value="Model Risk Review")
with right:
    review_status = st.selectbox("Review status", ["Draft", "Pending independent review", "Approved for simulation only"])

st.caption("The generated card always preserves the synthetic-data boundary and describes simulation-only use.")

base_card = model_card_markdown(selected_model, validation)
metadata = (
    "\n\n## Governance metadata\n\n"
    f"- **Proposed accountable owner:** {owner or 'Not assigned'}\n"
    f"- **Review status:** {review_status}\n"
    "- **Change-control trigger:** retraining, feature changes, threshold changes, material drift, or intended-use changes.\n"
)
card = base_card + metadata
st.session_state["model_card_markdown"] = card

model_metrics = validation["models"][selected_model]["metrics"]
drift = get_drift_profile()
columns = st.columns(4)
columns[0].metric("Model", selected_model)
columns[1].metric("Holdout ROC AUC", f"{model_metrics['roc_auc']:.3f}")
columns[2].metric("Holdout F1", f"{model_metrics['f1']:.3f}")
columns[3].metric("Drift watch / review flags", drift["warning_count"])

st.markdown("### Generated Markdown")
st.code(card, language="markdown", line_numbers=False)
st.download_button(
    "Download model card (.md)",
    data=card.encode("utf-8"),
    file_name=f"{selected_model.lower().replace(' ', '_')}_model_card.md",
    mime="text/markdown",
    use_container_width=False,
)

left, right = st.columns((1, 1), gap="large")
with left:
    st.markdown("### What this artifact captures")
    st.markdown(
        """
        - Intended and prohibited use
        - Synthetic data description and feature inventory
        - Holdout validation metrics
        - Known risks, limitations, and monitoring signals
        - LLM evaluation companion evidence
        - A review and approval checklist
        """
    )
with right:
    st.markdown("### Before any real deployment")
    st.warning(
        "A real release would require approved data governance, independent validation, fairness and privacy assessment, "
        "security controls, business threshold rationale, human accountability, monitoring implementation, and formal change control.",
        icon="⚠️",
    )

