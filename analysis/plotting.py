# Shared Altair templates for behavior summaries (accuracy and RT by stim level).
# Used by marimo demos for both simulated and jsPsych-exported trial data.

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import pandas as pd

if TYPE_CHECKING:
    import altair as alt

CHART_WIDTH = 260
CHART_HEIGHT = 220

SUMMARY_COLUMN_LABELS: dict[str, str] = {
    "stim_level": "coherence (proportion)",
    "acc": "accuracy (proportion)",
    "rt_mean": "mean RT (s)",
    "rt_med": "median RT (s)",
    "n": "trials (count)",
}


def label_summary_table(by: pd.DataFrame) -> pd.DataFrame:
    """Rename summarize_behavior columns for display tables."""
    return by.rename(columns=SUMMARY_COLUMN_LABELS)


def accuracy_by_stim_chart(by: pd.DataFrame, *, alt: Any) -> Any:
    """Bar chart: accuracy (proportion) by coherence level."""
    base = alt.Chart(by)
    return (
        base.mark_bar()
        .encode(
            x=alt.X("stim_level:Q", title="Coherence (proportion)"),
            y=alt.Y(
                "acc:Q",
                title="Accuracy (proportion)",
                scale=alt.Scale(domain=[0, 1]),
            ),
            tooltip=[
                alt.Tooltip("stim_level:Q", title="Coherence (proportion)", format=".2f"),
                alt.Tooltip("acc:Q", title="Accuracy (proportion)", format=".3f"),
                alt.Tooltip("n:Q", title="Trials (count)"),
                alt.Tooltip("rt_mean:Q", title="Mean RT (s)", format=".3f"),
            ],
        )
        .properties(width=CHART_WIDTH, height=CHART_HEIGHT, title="Accuracy by coherence")
    )


def rt_mean_by_stim_chart(by: pd.DataFrame, *, alt: Any) -> Any:
    """Bar chart: mean RT (s) by coherence level."""
    base = alt.Chart(by)
    return (
        base.mark_bar()
        .encode(
            x=alt.X("stim_level:Q", title="Coherence (proportion)"),
            y=alt.Y("rt_mean:Q", title="Mean RT (s)"),
            tooltip=[
                alt.Tooltip("stim_level:Q", title="Coherence (proportion)", format=".2f"),
                alt.Tooltip("rt_mean:Q", title="Mean RT (s)", format=".3f"),
                alt.Tooltip("rt_med:Q", title="Median RT (s)", format=".3f"),
                alt.Tooltip("n:Q", title="Trials (count)"),
            ],
        )
        .properties(width=CHART_WIDTH, height=CHART_HEIGHT, title="Mean RT by coherence")
    )


def behavior_summary_vega_lite_specs(*, alt: Any) -> dict[str, dict[str, object]]:
    """Vega-Lite chart shells (empty ``data.values``) for in-browser demo result charts."""
    placeholder = pd.DataFrame(
        [{"stim_level": 0.0, "acc": 0.0, "rt_mean": 0.0, "rt_med": 0.0, "n": 0}]
    )
    acc_spec = json.loads(
        accuracy_by_stim_chart(placeholder, alt=alt).to_json(format="vega-lite")
    )
    rt_spec = json.loads(
        rt_mean_by_stim_chart(placeholder, alt=alt).to_json(format="vega-lite")
    )
    acc_spec["data"] = {"values": []}
    rt_spec["data"] = {"values": []}
    return {"accuracy": acc_spec, "rt_mean": rt_spec}


def behavior_summary_charts(by: pd.DataFrame, *, alt: Any) -> Any:
    """Side-by-side accuracy and mean RT charts."""
    return alt.hconcat(
        accuracy_by_stim_chart(by, alt=alt),
        rt_mean_by_stim_chart(by, alt=alt),
    )


def render_behavior_summary(
    by: pd.DataFrame,
    *,
    mo: Any,
    alt: Any,
    section_title: str,
    plots_heading: str = "### Plots",
    empty_message: str | None = None,
) -> Any:
    """Marimo stack: section title, summary table, and Altair charts."""
    if by.empty:
        msg = empty_message or "_No trials to summarize yet._"
        blocks: list[object] = []
        if section_title:
            blocks.append(mo.md(section_title))
        blocks.append(mo.md(msg))
        return mo.vstack(blocks, gap=0.5)

    by_labeled = label_summary_table(by)
    chart = mo.ui.altair_chart(behavior_summary_charts(by, alt=alt))
    blocks = []
    if section_title:
        blocks.append(mo.md(section_title))
    blocks.append(mo.Html(by_labeled.to_html(index=False, classes="dataframe")))
    if plots_heading:
        blocks.append(mo.md(plots_heading))
    blocks.append(chart)
    return mo.vstack(blocks, gap=0.5)
