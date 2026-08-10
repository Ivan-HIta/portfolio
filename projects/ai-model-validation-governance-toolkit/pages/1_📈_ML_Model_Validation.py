"""Interactive holdout validation evidence for the two synthetic ML baselines."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app import (
    TARGET_COLUMN,
    build_confusion_figure,
    build_roc_figure,
    configure_page,
    data_source_label,
    get_credit_data,
    get_validation_bundle,
    inject_styles,
    render_page_header,
    render_sidebar_context,
    render_synthetic_disclaimer,
    set_credit_data,
)


configure_page("ML Model Validation · AI Governance Toolkit")
inject_styles()
render_sidebar_context()
render_page_header(
    "ML Model Validation",
    "Compare local baseline classifiers using a reproducible train/test split, discrimination, calibration, threshold, and lift evidence.",
    "Validation evidence",
)


def _upload_controls() -> None:
    """Allow a user to temporarily inspect another synthetic CSV locally."""
    with st.sidebar:
        st.markdown("### Synthetic data input")
        upload = st.file_uploader("Optional synthetic credit CSV", type=["csv"], key="ml_validation_upload")
        if upload is not None:
            signature = (upload.name, upload.size)
            if st.session_state.get("uploaded_credit_signature") != signature:
                try:
                    uploaded_data = pd.read_csv(upload)
                    set_credit_data(uploaded_data, f"Uploaded synthetic CSV · {upload.name}")
                    st.session_state["uploaded_credit_signature"] = signature
                    st.success("Synthetic CSV loaded for this browser session.")
                except (UnicodeDecodeError, pd.errors.ParserError) as error:
                    st.error(f"Could not read the CSV: {error}")
        if st.button("Restore bundled data", use_container_width=True):
            for key in ("credit_data", "credit_data_source", "validation_bundle", "drift_profile", "model_card_markdown", "uploaded_credit_signature"):
                st.session_state.pop(key, None)
            st.rerun()


def _classification_report_frame(report: dict) -> pd.DataFrame:
    records = []
    for label, values in report.items():
        if not isinstance(values, dict):
            continue
        records.append(
            {
                "class / aggregate": label,
                "precision": values.get("precision", 0.0),
                "recall": values.get("recall", 0.0),
                "f1-score": values.get("f1-score", 0.0),
                "support": int(values.get("support", 0)),
            }
        )
    return pd.DataFrame(records)


_upload_controls()
data = get_credit_data()
render_synthetic_disclaimer(compact=True)
st.caption(f"Active data source: {data_source_label('credit')} · {len(data):,} synthetic records")

validation = get_validation_bundle(data)
if not validation.get("available"):
    st.error(validation.get("message", "Validation artifacts could not be created."))
    st.stop()

model_names = list(validation["models"])
selected_model = st.radio("Validation model", model_names, horizontal=True, key="validation_model_choice")
artifact = validation["models"][selected_model]
metrics = artifact["metrics"]

st.markdown("### Holdout performance")
st.caption(
    f"Training rows: {validation['train_rows']:,} · Holdout rows: {validation['test_rows']:,} · "
    f"Target event rate: {validation['target_rate']:.1%}"
)
columns = st.columns(5)
for column, label, key in zip(columns, ("Accuracy", "Precision", "Recall", "F1 score", "ROC AUC"), ("accuracy", "precision", "recall", "f1", "roc_auc")):
    column.metric(label, f"{metrics[key]:.3f}")

left, right = st.columns((1.15, 0.85), gap="large")
with left:
    st.markdown("### Discrimination")
    st.plotly_chart(build_roc_figure(validation["models"]), use_container_width=True)
with right:
    st.markdown("### Classification outcomes")
    st.plotly_chart(build_confusion_figure(artifact["confusion_matrix"], selected_model), use_container_width=True)

left, right = st.columns((1, 1), gap="large")
with left:
    st.markdown("### Calibration check")
    calibration = artifact["calibration"]
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=calibration["predicted"],
            y=calibration["observed"],
            mode="lines+markers",
            name=selected_model,
            line=dict(color="#315cbd", width=3),
        )
    )
    figure.add_trace(
        go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="Perfect calibration", line=dict(color="#94a3b8", dash="dash")))
    figure.update_layout(
        xaxis_title="Mean predicted probability",
        yaxis_title="Observed event rate",
        height=355,
        margin=dict(l=20, r=20, t=25, b=20),
        legend=dict(orientation="h", y=-0.24),
    )
    st.plotly_chart(figure, use_container_width=True)
    st.caption("Calibration is a diagnostic, not a guarantee that scores are suitable for a business threshold.")
with right:
    st.markdown("### Threshold analysis")
    threshold_data = artifact["thresholds"].copy()
    figure = px.line(
        threshold_data,
        x="threshold",
        y=["precision", "recall", "f1", "false_positive_rate", "false_negative_rate"],
        markers=True,
        labels={"value": "Metric", "threshold": "Decision threshold", "variable": ""},
        color_discrete_sequence=["#315cbd", "#2a9d8f", "#7b61a8", "#df8a2e", "#d1495b"],
    )
    figure.update_layout(height=355, margin=dict(l=20, r=20, t=25, b=20), legend=dict(orientation="h", y=-0.26))
    st.plotly_chart(figure, use_container_width=True)
    selected_threshold = st.select_slider(
        "Review an operating point", options=threshold_data["threshold"].round(2).tolist(), value=0.50
    )
    selected_row = threshold_data.loc[threshold_data["threshold"].eq(selected_threshold)].iloc[0]
    st.caption(
        f"At {selected_threshold:.2f}: {selected_row['flagged_rate']:.1%} of holdout records flagged; "
        f"FPR {selected_row['false_positive_rate']:.1%}; FNR {selected_row['false_negative_rate']:.1%}."
    )

left, right = st.columns((1, 1), gap="large")
with left:
    st.markdown("### Decile / lift analysis")
    lift = artifact["lift_table"].copy()
    figure = px.bar(
        lift,
        x="decile",
        y="lift",
        text="lift",
        labels={"decile": "Risk-score decile (1 = highest score)", "lift": "Event-rate lift"},
        color_discrete_sequence=["#315cbd"],
    )
    figure.update_traces(texttemplate="%{text:.2f}×", textposition="outside")
    figure.update_layout(height=350, margin=dict(l=20, r=20, t=25, b=20), showlegend=False)
    st.plotly_chart(figure, use_container_width=True)
with right:
    st.markdown("### Feature contribution view")
    importance = artifact.get("feature_importance", pd.DataFrame())
    if importance.empty:
        st.caption("Feature importance is unavailable for this fitted estimator.")
    else:
        figure = px.bar(
            importance.sort_values("importance"),
            x="importance",
            y="feature",
            orientation="h",
            color_discrete_sequence=["#2a9d8f"],
            labels={"importance": "Relative contribution", "feature": ""},
        )
        figure.update_layout(height=350, margin=dict(l=20, r=20, t=25, b=20), showlegend=False)
        st.plotly_chart(figure, use_container_width=True)

st.markdown("### Classification report")
report = _classification_report_frame(metrics["classification_report"])
st.dataframe(
    report.style.format({"precision": "{:.3f}", "recall": "{:.3f}", "f1-score": "{:.3f}"}),
    use_container_width=True,
    hide_index=True,
)

st.markdown("### Holdout prediction sample")
predictions = artifact["predictions"].copy().sort_values("predicted_probability", ascending=False)
display_columns = ["customer_id", "region", "customer_segment", TARGET_COLUMN, "predicted_default", "predicted_probability", "correct"]
st.dataframe(
    predictions.loc[:, display_columns].head(20).style.format({"predicted_probability": "{:.1%}"}),
    use_container_width=True,
    hide_index=True,
)
st.download_button(
    "Download holdout prediction evidence (CSV)",
    data=predictions.to_csv(index=False).encode("utf-8"),
    file_name=f"{selected_model.lower().replace(' ', '_')}_holdout_predictions.csv",
    mime="text/csv",
)
