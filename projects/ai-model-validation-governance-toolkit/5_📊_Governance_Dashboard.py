"""Executive-style synthesis of the local synthetic governance evidence pack."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app import (
    configure_page,
    evaluate_llm_outputs,
    get_credit_data,
    get_drift_profile,
    get_validation_bundle,
    inject_styles,
    render_page_header,
    render_sidebar_context,
    render_synthetic_disclaimer,
    segment_performance,
)


configure_page("Governance Dashboard · AI Governance Toolkit")
inject_styles()
render_sidebar_context()
render_page_header(
    "Governance Dashboard",
    "A concise decision-support view of current synthetic validation, segment-screening, drift-readiness, and LLM evaluation artifacts.",
    "Portfolio governance snapshot",
)
render_synthetic_disclaimer(compact=True)

data = get_credit_data()
validation = get_validation_bundle(data)
if not validation.get("available"):
    st.error(validation.get("message", "Validation artifacts could not be created."))
    st.stop()

drift = get_drift_profile(data)
llm_evaluation = evaluate_llm_outputs()
llm_summary = llm_evaluation["summary"]
model_scores = pd.DataFrame(
    [
        {
            "model": name,
            "accuracy": artifact["metrics"]["accuracy"],
            "precision": artifact["metrics"]["precision"],
            "recall": artifact["metrics"]["recall"],
            "f1": artifact["metrics"]["f1"],
            "roc_auc": artifact["metrics"]["roc_auc"],
        }
        for name, artifact in validation["models"].items()
    ]
)
best_model = model_scores.sort_values("roc_auc", ascending=False).iloc[0]
best_name = str(best_model["model"])
best_predictions = validation["models"][best_name]["predictions"]
region_screen = segment_performance(best_predictions, "region")
recall_gap = float(region_screen["recall"].max() - region_screen["recall"].min()) if not region_screen.empty else 0.0
review_flags = int((drift["feature_drift"]["status"] == "Review").sum())
watch_flags = int((drift["feature_drift"]["status"] == "Watch").sum())

st.markdown("### Current evidence at a glance")
columns = st.columns(5)
columns[0].metric("Synthetic records", f"{validation['data_rows']:,}")
columns[1].metric("Leading holdout model", best_name)
columns[2].metric("Leading ROC AUC", f"{best_model['roc_auc']:.3f}")
columns[3].metric("Drift review flags", review_flags, delta=f"{watch_flags} watch")
columns[4].metric("LLM warning rate", f"{llm_summary['missing_context_rate'] + llm_summary['hallucination_proxy_rate']:.1%}")

st.markdown("### Governance control posture")
validation_status = "Ready for review" if best_model["roc_auc"] >= 0.60 else "Needs review"
segment_status = "Review" if recall_gap >= 0.20 else "Screened"
stability_status = "Review" if review_flags else ("Watch" if watch_flags else "Stable")
llm_status = "Review" if llm_summary["hallucination_proxy_rate"] > 0.10 else "Screened"
controls = pd.DataFrame(
    [
        ("Baseline model validation", validation_status, f"{best_name} ROC AUC {best_model['roc_auc']:.3f}; holdout F1 {best_model['f1']:.3f}"),
        ("Segment performance screen", segment_status, f"Region recall range {recall_gap:.1%}; investigate material differences with event-count context."),
        ("Stability readiness", stability_status, f"{review_flags} review and {watch_flags} watch feature flags in the simulated comparison."),
        ("LLM output evaluation", llm_status, f"Coverage {llm_summary['mean_keyword_coverage']:.1%}; unsupported-claim proxy {llm_summary['hallucination_proxy_rate']:.1%}."),
        ("Model documentation", "Draft", "A downloadable Markdown model card is available and requires reviewer sign-off."),
        ("Production approval", "Not approved", "This synthetic portfolio project is not approved for any real business use."),
    ],
    columns=["control", "status", "evidence"],
)

def _status_style(value: str) -> str:
    colors = {
        "Ready for review": "#315cbd",
        "Screened": "#2a9d8f",
        "Stable": "#2a9d8f",
        "Watch": "#e9a23b",
        "Review": "#d1495b",
        "Draft": "#7b61a8",
        "Needs review": "#d1495b",
        "Not approved": "#d1495b",
    }
    return f"color: {colors.get(value, '#627d98')}; font-weight: 700"


st.dataframe(
    controls.style.applymap(_status_style, subset=["status"]),
    use_container_width=True,
    hide_index=True,
)

left, right = st.columns((1, 1), gap="large")
with left:
    st.markdown("### Baseline comparison")
    score_view = model_scores.melt(id_vars="model", value_vars=["accuracy", "precision", "recall", "f1", "roc_auc"], var_name="metric", value_name="score")
    figure = px.bar(
        score_view,
        x="metric",
        y="score",
        color="model",
        barmode="group",
        labels={"metric": "", "score": "Holdout score", "model": ""},
        color_discrete_sequence=["#315cbd", "#2a9d8f"],
    )
    figure.update_yaxes(range=[0, 1])
    figure.update_layout(height=390, margin=dict(l=20, r=20, t=25, b=20), legend=dict(orientation="h", y=-0.21))
    st.plotly_chart(figure, use_container_width=True)
with right:
    st.markdown("### Drift flag distribution")
    status_counts = drift["feature_drift"]["status"].value_counts().reindex(["Stable", "Watch", "Review"], fill_value=0).reset_index()
    status_counts.columns = ["status", "features"]
    figure = px.pie(
        status_counts,
        names="status",
        values="features",
        hole=0.58,
        color="status",
        color_discrete_map={"Stable": "#2a9d8f", "Watch": "#e9a23b", "Review": "#d1495b"},
    )
    figure.add_annotation(text=f"{len(drift['feature_drift'])}<br>features", x=0.5, y=0.5, showarrow=False, font=dict(size=19, color="#243b53"))
    figure.update_layout(height=390, margin=dict(l=20, r=20, t=25, b=20), legend=dict(orientation="h", y=-0.16))
    st.plotly_chart(figure, use_container_width=True)

left, right = st.columns((1, 1), gap="large")
with left:
    st.markdown("### LLM evaluation companion")
    llm_measures = pd.DataFrame(
        {
            "measure": ["Keyword coverage", "Relevance proxy", "Missing-context warnings", "Unsupported-claim proxy"],
            "rate": [
                llm_summary["mean_keyword_coverage"],
                llm_summary["mean_relevance"],
                llm_summary["missing_context_rate"],
                llm_summary["hallucination_proxy_rate"],
            ],
            "type": ["Positive signal", "Positive signal", "Warning", "Warning"],
        }
    )
    figure = px.bar(
        llm_measures,
        x="rate",
        y="measure",
        orientation="h",
        color="type",
        labels={"rate": "Rate", "measure": "", "type": ""},
        color_discrete_map={"Positive signal": "#315cbd", "Warning": "#d1495b"},
    )
    figure.update_xaxes(range=[0, 1])
    figure.update_layout(height=365, margin=dict(l=20, r=20, t=25, b=20), legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(figure, use_container_width=True)
with right:
    st.markdown("### Monitoring readiness")
    st.markdown(
        """
        <div class="insight-card">
          <h4>Recommended monitoring cadence</h4>
          <p><b>Each release:</b> data schema, feature contract, score and threshold checks.<br><br>
          <b>Monthly:</b> target rate, feature drift, calibration, segment outcomes, and LLM evaluation trends.<br><br>
          <b>On trigger:</b> economic / policy change, material drift, complaint patterns, retraining, or change in intended use.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)
    st.warning("Governance dashboard signals support escalation; they are not an automated approval mechanism.", icon="⚠️")

st.markdown("### Suggested review actions")
actions = []
if review_flags:
    actions.append(f"Investigate {review_flags} simulated feature-drift flag(s) before relying on prior validation conclusions.")
if recall_gap >= 0.20:
    actions.append("Review segment recall variation with event counts, threshold sensitivity, feature rationale, and business impact.")
if llm_summary["missing_context_rate"] > 0.10 or llm_summary["hallucination_proxy_rate"] > 0.05:
    actions.append("Sample flagged LLM answers with a domain reviewer and expand the synthetic adversarial test set.")
if not actions:
    actions.append("Maintain scheduled monitoring and document independent review before any change in model use.")
for action in actions:
    st.markdown(f"- {action}")

st.download_button(
    "Download governance dashboard evidence (CSV)",
    data=controls.to_csv(index=False).encode("utf-8"),
    file_name="synthetic_governance_dashboard_evidence.csv",
    mime="text/csv",
)

