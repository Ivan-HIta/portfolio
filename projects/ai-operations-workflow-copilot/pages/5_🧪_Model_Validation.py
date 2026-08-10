"""Holdout validation, diagnostic examples, and portfolio-model caveats."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app import (
    configure_page,
    get_ticket_data,
    get_validation_report,
    inject_styles,
    render_empty_data_notice,
    render_page_header,
    render_sidebar_context,
)


configure_page("Model Validation | AI Operations Copilot")
inject_styles()
render_sidebar_context()
render_page_header(
    "Model validation",
    "Inspect reproducible holdout metrics, confusion patterns, and concrete failure cases before trusting AI-assisted routing.",
    "Step 5 · model risk and quality",
)

st.warning(
    "Portfolio simulation disclaimer: all records in this project are synthetic. Metrics demonstrate an engineering workflow, "
    "not production model performance or a recommendation for automated operational decisions."
)

data = get_ticket_data()
if data.empty:
    render_empty_data_notice()
    st.stop()

with st.spinner("Running reproducible 80/20 holdout validation..."):
    report = get_validation_report(data)

if not report.get("available"):
    st.error(report.get("message", "Validation is not available for the active data set."))
    st.stop()

metric_columns = st.columns(4)
metric_columns[0].metric("Accuracy", f"{report['accuracy']:.1%}")
metric_columns[1].metric("Macro precision", f"{report['macro_precision']:.1%}")
metric_columns[2].metric("Macro recall", f"{report['macro_recall']:.1%}")
metric_columns[3].metric("Macro F1", f"{report['macro_f1']:.1%}")
st.caption(f"Evaluation setup: {report['train_size']:,} training tickets and {report['test_size']:,} held-out tickets · TF-IDF + Logistic Regression · random_state=42.")

st.markdown("### Confusion matrix")
labels = report["labels"]
matrix = report["confusion_matrix"]
heatmap = go.Figure(
    data=go.Heatmap(
        z=matrix,
        x=labels,
        y=labels,
        colorscale="Blues",
        hovertemplate="Actual: %{y}<br>Predicted: %{x}<br>Tickets: %{z}<extra></extra>",
        colorbar_title="Tickets",
    )
)
heatmap.update_layout(
    xaxis_title="Predicted category",
    yaxis_title="Actual category",
    margin=dict(l=8, r=8, t=20, b=110),
    height=500,
)
st.plotly_chart(heatmap, use_container_width=True)

st.markdown("### Category-level validation")
per_class_rows = []
for label in labels:
    values = report["per_class"].get(label, {})
    per_class_rows.append(
        {
            "Category": label,
            "Precision": values.get("precision", 0.0),
            "Recall": values.get("recall", 0.0),
            "F1 score": values.get("f1-score", 0.0),
            "Support": int(values.get("support", 0)),
        }
    )
per_class_frame = pd.DataFrame(per_class_rows)
st.dataframe(
    per_class_frame.style.format({"Precision": "{:.1%}", "Recall": "{:.1%}", "F1 score": "{:.1%}"}),
    use_container_width=True,
    hide_index=True,
)

st.markdown("### Prediction diagnostics")
examples = report["examples"].copy()
sample_columns = ["ticket_id", "issue_description", "issue_category", "predicted_category", "confidence", "priority", "process_area"]
st.markdown("#### Sample held-out predictions")
sample = examples.sample(min(12, len(examples)), random_state=42).loc[:, sample_columns]
st.dataframe(
    sample.style.format({"confidence": "{:.1%}"}),
    use_container_width=True,
    hide_index=True,
    height=330,
)

st.markdown("#### Misclassified examples")
misclassified = examples.loc[~examples["correct"], sample_columns]
if misclassified.empty:
    st.success("No misclassified examples were found in this holdout split.")
else:
    st.dataframe(
        misclassified.head(20).style.format({"confidence": "{:.1%}"}),
        use_container_width=True,
        hide_index=True,
        height=330,
    )
    st.caption("Reviewing these examples helps identify ambiguous descriptions, sparse labels, and categories that need clearer operating definitions.")

st.download_button(
    "Download held-out prediction diagnostics",
    data=examples.to_csv(index=False).encode("utf-8"),
    file_name="model_validation_predictions.csv",
    mime="text/csv",
)

st.divider()
st.markdown("### Model limitations and controls")
limitations_left, limitations_right = st.columns(2)
with limitations_left:
    st.markdown(
        """
        - The labels and descriptions are synthetic, so performance may not transfer to a real operations environment.
        - Short, overlapping, or novel issue descriptions can be ambiguous for a bag-of-words classifier.
        - Class imbalance and changing processes can degrade category-level recall.
        - The model does not verify facts in source systems or infer financial-materiality impact.
        """
    )
with limitations_right:
    st.markdown(
        """
        - Human review is required for high-impact, policy, override, and exception workflows.
        - Decisions are captured in a local SQLite audit trail for transparency.
        - Production deployment would require data governance, privacy review, monitoring, drift detection, and approval controls.
        - Thresholds, routing rules, and training labels should be periodically recalibrated with accountable process owners.
        """
    )

