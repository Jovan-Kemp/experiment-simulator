/** In-iframe Vega-Lite charts aligned with marimo Altair plots (accuracy & mean RT). */
window.JsPsychDemoCharts = (() => {
  const CHART_W = 260;
  const CHART_H = 220;

  function summarizeRows(rows) {
    const bins = {};
    for (const r of rows) {
      const key = String(r.stim_level);
      if (!bins[key]) bins[key] = { correct: 0, n: 0, rt: [] };
      bins[key].n += 1;
      if (r.correct) bins[key].correct += 1;
      const rt = Number(r.rt);
      if (Number.isFinite(rt)) bins[key].rt.push(rt / 1000);
    }
    return Object.entries(bins)
      .map(([level, b]) => {
        const rts = b.rt;
        const sorted = rts.slice().sort((a, c) => a - c);
        const mid = Math.floor(sorted.length / 2);
        const rt_med =
          sorted.length === 0
            ? null
            : sorted.length % 2
              ? sorted[mid]
              : (sorted[mid - 1] + sorted[mid]) / 2;
        return {
          stim_level: parseFloat(level),
          acc: b.correct / b.n,
          rt_mean: rts.length ? rts.reduce((s, v) => s + v, 0) / rts.length : null,
          rt_med,
          n: b.n,
        };
      })
      .sort((a, b) => a.stim_level - b.stim_level);
  }

  function accuracySpec(values) {
    return {
      $schema: "https://vega.github.io/schema/vega-lite/v5.json",
      width: CHART_W,
      height: CHART_H,
      title: "Accuracy by coherence",
      data: { values },
      mark: "bar",
      encoding: {
        x: {
          field: "stim_level",
          type: "quantitative",
          title: "Coherence (proportion)",
        },
        y: {
          field: "acc",
          type: "quantitative",
          title: "Accuracy (proportion)",
          scale: { domain: [0, 1] },
        },
        tooltip: [
          { field: "stim_level", type: "quantitative", title: "Coherence (proportion)" },
          { field: "acc", type: "quantitative", title: "Accuracy (proportion)" },
          { field: "n", type: "quantitative", title: "Trials (count)" },
          { field: "rt_mean", type: "quantitative", title: "Mean RT (s)" },
        ],
      },
    };
  }

  function rtSpec(values) {
    return {
      $schema: "https://vega.github.io/schema/vega-lite/v5.json",
      width: CHART_W,
      height: CHART_H,
      title: "Mean RT by coherence",
      data: { values },
      mark: "bar",
      encoding: {
        x: {
          field: "stim_level",
          type: "quantitative",
          title: "Coherence (proportion)",
        },
        y: { field: "rt_mean", type: "quantitative", title: "Mean RT (s)" },
        tooltip: [
          { field: "stim_level", type: "quantitative", title: "Coherence (proportion)" },
          { field: "rt_mean", type: "quantitative", title: "Mean RT (s)" },
          { field: "rt_med", type: "quantitative", title: "Median RT (s)" },
          { field: "n", type: "quantitative", title: "Trials (count)" },
        ],
      },
    };
  }

  function renderPanelHtml(rows) {
    const trials = rows.filter((r) => r && r.stim_level !== undefined);
    if (!trials.length) {
      return '<div class="demo-results-empty">No trials to summarize.</div>';
    }
    const correct = trials.filter((r) => r.correct).length;
    return (
      '<div class="demo-results-panel">' +
      `<div class="demo-results-heading">Demo complete — ${correct} / ${trials.length} correct</div>` +
      '<div class="demo-results-charts">' +
      '<div id="demo-chart-acc"></div>' +
      '<div id="demo-chart-rt"></div>' +
      "</div>" +
      '<p class="demo-results-restart">Click <strong>Restart demo</strong> below this window to run the experiment again.</p>' +
      "</div>"
    );
  }

  async function embedCharts(rows) {
    if (typeof vegaEmbed !== "function") {
      console.warn("vegaEmbed unavailable; cannot render demo charts.");
      return;
    }
    const values = summarizeRows(
      rows.filter((r) => r && r.stim_level !== undefined)
    );
    if (!values.length) return;
    const opts = { actions: false, renderer: "svg" };
    await vegaEmbed("#demo-chart-acc", accuracySpec(values), opts);
    await vegaEmbed("#demo-chart-rt", rtSpec(values), opts);
  }

  function mount(rows) {
    const trials = rows.filter((r) => r && r.stim_level !== undefined);
    const root = document.getElementById("jspsych-target");
    if (!root) return;
    root.innerHTML = renderPanelHtml(trials);
    void embedCharts(trials);
  }

  return { mount, renderPanelHtml, summarizeRows, accuracySpec, rtSpec };
})();
