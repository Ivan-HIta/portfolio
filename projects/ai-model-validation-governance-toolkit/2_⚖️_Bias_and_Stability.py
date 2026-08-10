"""Segment screening and drift-readiness view for synthetic validation artifacts."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app import (
    SEGMENT_LABELS,
    TARGET_COLUMN,
    add_buckets,
    configure_page,
    get_credit_data,
    get_drift_profile,
    get_validation_bundle,
    inject_styles,
    render_page_header,
    render_sidebar_context,
    render_synthetic_disclaimer,
    segment_performance,
    status_color,
)


configure_page("Bias & Stability · AI Governance Toolkit")
inject_styles()
render_sidebar_context()
render_page_header(
    "Bias and Stability",
    "Screen outcome consistency across synthetic segments and test whether simulated data movement would trigger monitoring attention.",
    "Segment and drift review",
)
render_synthetic_disclaimer(compact=True)

data = get_credit_data()
validation = get_validation_bundle(data)
if not validation.get("available"):
    st.error(validation.get("message", "Validation artifacts could not be created."))
    st.stop()

model_names = list(validation["models"])
controls_left, controls_right = st.columns((0.52, 0.48))
with controls_left:
    selected_model = st.selectbox("Model for segment screening", model_names, key="bias_model_choice")
with controls_right:
    group_column = st.selectbox("Segment view", list(SEGMENT_LABELS), format_func=lambda key: SEGMENT_LABELS[key])

predictions = validation["models"][selected_model]["predictions"].copy()
segment_data = segment_performance(predictions, group_column)
st.markdown("### Segment performance screen")
st.caption(
    "The view compares recall, false-positive rate, and false-negative rate across groups. "
    "It is a diagnostic screen only: small samples and synthetic data prohibit fairness conclusions."
)
if segment_data.empty:
    st.warning("The selected segment is not available in the current data.")
else:
    event_groups = int((segment_data["actual_events"] > 0).sum())
    metrics_left, metrics_mid, metrics_right, metrics_far = st.columns(4)
    metrics_left.metric("Segments reviewed", f"{len(segment_data):,}")
    metrics_mid.metric("Segments with events", f"{event_groups:,}")
    metrics_right.metric("Recall range", f"{segment_data['recall'].max() - segment_data['recall'].min():.1%}")
    metrics_far.metric("FPR range", f"{segment_data['false_positive_rate'].max() - segment_data['false_positive_rate'].min():.1%}")

    left, right = st.columns((1.05, 0.95), gap="large")
    with left:
        visual = segment_data.melt(
            id_vars=["segment", "records"],
            value_vars=["recall", "false_positive_rate", "false_negative_rate"],
            var_name="measure",
            value_name="rate",
        )
        visual["measure"] = visual["measure"].map(
            {"recall": "Recall", "false_positive_rate": "False positive rate", "false_negative_rate": "False negative rate"}
        )
        figure = px.bar(
            visual,
            x="segment",
            y="rate",
            color="measure",
            barmode="group",
            labels={"segment": SEGMENT_LABELS[group_column], "rate": "Rate", "measure": ""},
            color_discrete_map={"Recall": "#315cbd", "False positive rate": "#df8a2e", "False negative rate": "#d1495b"},
        )
        figure.update_layout(height=390, margin=dict(l=20, r=20, t=25, b=50), legend=dict(orientation="h", y=-0.27))
        st.plotly_chart(figure, use_container_width=True)
    with right:
        st.markdown("#### Review notes")
        largest_recall_gap = segment_data.loc[segment_data["recall"].idxmax(), "segment"]
        lowest_recall = segment_data.loc[segment_data["recall"].idxmin(), "segment"]
        st.markdown(
            f"""
            <div class="insight-card">
              <h4>What to examine</h4>
              <p>Highest observed recall: <b>{largest_recall_gap}</b>; lowest: <b>{lowest_recall}</b>.
              Inspect event counts, decision costs, missingness, feature rationale, and threshold effects before deciding whether a difference is material.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
        low_count = int((segment_data["actual_events"] < 10).sum())
        if low_count:
            st.warning(f"{low_count} segment(s) have fewer than 10 observed events; rate estimates are especially unstable.", icon="⚠️")
        else:
            st.success("Each listed segment has at least 10 observed events in this synthetic holdout sample.")
    st.dataframe(
        segment_data.style.format(
            {
                "event_rate": "{:.1%}",
                "recall": "{:.1%}",
                "false_positive_rate": "{:.1%}",
                "false_negative_rate": "{:.1%}",
                "precision": "{:.1%}",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.download_button(
        "Download segment screening table (CSV)",
        data=segment_data.to_csv(index=False).encode("utf-8"),
        file_name=f"{selected_model.lower().replace(' ', '_')}_{group_column}_segment_screen.csv",
        mime="text/csv",
    )

st.divider()
st.markdown("### Stability and drift readiness")
st.caption(
    "The current sample is a deterministic synthetic distribution shift. PSI-like thresholds are illustrative: "
    "Stable < 0.10, Watch 0.10–0.24, Review ≥ 0.25."
)
profile = get_drift_profile(data)
drift_table = profile["feature_drift"].copy()
review_count = int((drift_table["status"] == "Review").sum())
watch_count = int((drift_table["status"] == "Watch").sum())
baseline_target = profile["baseline_target_rate"]
current_target = profile["current_target_rate"]

metrics_left, metrics_mid, metrics_right, metrics_far = st.columns(4)
metrics_left.metric("Review flags", review_count)
metrics_mid.metric("Watch flags", watch_count)
metrics_right.metric("Baseline event rate", f"{baseline_target:.1%}")
metrics_far.metric("Simulated current rate", f"{current_target:.1%}", delta=f"{current_target - baseline_target:+.1%}")

left, right = st.columns((1, 1), gap="large")
with left:
    figure = px.bar(
        drift_table.sort_values("psi_like_score"),
        x="psi_like_score",
        y="feature",
        color="status",
        orientation="h",
        labels={"psi_like_score": "PSI-like score", "feature": ""},
        color_discrete_map={"Stable": "#2a9d8f", "Watch": "#e9a23b", "Review": "#d1495b"},
    )
    figure.add_vline(x=0.10, line_dash="dash", line_color="#e9a23b", annotation_text="Watch")
    figure.add_vline(x=0.25, line_dash="dash", line_color="#d1495b", annotation_text="Review")
    figure.update_layout(height=405, margin=dict(l=20, r=20, t=25, b=20), legend=dict(orientation="h", y=-0.18))
    st.plotly_chart(figure, use_container_width=True)
with right:
    comparison_feature = st.selectbox("Compare synthetic distributions", drift_table["feature"].tolist())
    baseline = profile["baseline"]
    current = profile["current"]
    if comparison_feature in {"region", "customer_segment"}:
        base_counts = baseline[comparison_feature].value_counts(normalize=True).rename("Baseline")
        current_counts = current[comparison_feature].value_counts(normalize=True).rename("Simulated current")
        comparison = pd.concat([base_counts, current_counts], axis=1).fillna(0).reset_index(names="category")
        figure = px.bar(
            comparison.melt(id_vars="category", var_name="sample", value_name="share"),
            x="category",
            y="share",
            color="sample",
            barmode="group",
            labels={"category": comparison_feature.replace("_", " ").title(), "share": "Share", "sample": ""},
            color_discrete_sequence=["#315cbd", "#df8a2e"],
        )
    else:
        distribution = pd.concat(
            [
                pd.DataFrame({"value": baseline[comparison_feature], "sample": "Baseline"}),
                pd.DataFrame({"value": current[comparison_feature], "sample": "Simulated current"}),
            ],
            ignore_index=True,
        )
        figure = px.histogram(
            distribution,
            x="value",
            color="sample",
            barmode="overlay",
            nbins=35,
            histnorm="probability density",
            opacity=0.58,
            labels={"value": comparison_feature.replace("_", " ").title(), "sample": ""},
            color_discrete_sequence=["#315cbd", "#df8a2e"],
        )
    figure.update_layout(height=405, margin=dict(l=20, r=20, t=25, b=35), legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(figure, use_container_width=True)

st.markdown("#### Drift findings")
st.dataframe(
    drift_table.style.format({"psi_like_score": "{:.3f}"}).applymap(
        lambda status: f"color: {status_color(status)}; font-weight: 600" if status in {"Stable", "Watch", "Review"} else "",
        subset=["status"],
    ),
    use_container_width=True,
    hide_index=True,
)
st.download_button(
    "Download drift readiness evidence (CSV)",
    data=drift_table.to_csv(index=False).encode("utf-8"),
    file_name="synthetic_drift_readiness_evidence.csv",
    mime="text/csv",
)

