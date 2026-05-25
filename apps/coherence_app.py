import marimo

# Ensure project root is importable when running via `marimo run apps/coherence_app.py`.
import sys
from pathlib import Path

ROOT = str(Path(__file__).resolve().parents[1])
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

app = marimo.App(width="full")


@app.cell
def _():
    import numpy as np
    import pandas as pd

    import marimo as mo

    return mo, np, pd


@app.cell
def _():
    import sys
    from pathlib import Path

    # Ensure module folders (agents/, tasks/, etc.) are importable regardless
    # of marimo launch cwd/cell execution order.
    candidates = [Path.cwd(), Path(__file__).resolve().parents[1]]
    for root in candidates:
        if (root / "agents").exists() and str(root) not in sys.path:
            sys.path.insert(0, str(root))

    from agents.evidence_observer import NAfcObserver
    from analysis.hssm_pipeline import (
        fit_hssm_model,
        summarize_behavior,
        summarize_posterior,
    )
    from renderers.jspsych_preview import motion_coherence_preview_iframe_html
    from runtime.embed import render_srcdoc_iframe
    from runtime.jspsych_runner import build_jspsych_runner_html
    from tasks.jspsych_motion import JsPsychTrialEngine
    from tasks.timelines.motion_demo import (
        build_motion_demo_levels,
        build_motion_demo_timeline,
        motion_demo_runner_config,
    )

    return (
        JsPsychTrialEngine,
        NAfcObserver,
        Path,
        build_jspsych_runner_html,
        build_motion_demo_levels,
        build_motion_demo_timeline,
        fit_hssm_model,
        motion_coherence_preview_iframe_html,
        motion_demo_runner_config,
        render_srcdoc_iframe,
        summarize_behavior,
        summarize_posterior,
    )


@app.cell
def _(Path, mo):
    import base64

    logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo" / "hssm_white.png"
    logo_b64 = base64.b64encode(logo_path.read_bytes()).decode("ascii")
    logo_block = mo.Html(
        f'<div style="background:#ffffff;padding:1rem 1.25rem;border-radius:8px;">'
        f'<img alt="HSSM" src="data:image/png;base64,{logo_b64}" '
        f'style="max-height:80px;width:auto;display:block;" />'
        f"</div>"
    )
    intro = mo.md(
        r"""
## HSSM demonstration with motion coherence simulated experiment

This app simulates a **binary left/right motion task** at **three coherence levels** (0–1, dimensionless) you set with the sliders (shown side-by-side).

- **Observer**: n-AFC virtual observer with **stimulus-level dependent Gaussian noise** plus lapse noise.
- **Task**: trials use **jsPsych-style** objects generated in Python; jsPsych can execute these trials directly in-browser.
- **Fit**: fits a **HSSM** DDM with drift \(v\) regressed on coherence (`stim_level`, proportion).
"""
    )
    mo.vstack([logo_block, intro], gap=0.75)
    return


@app.cell
def _(mo):
    lvl1 = mo.ui.slider(0.0, 1.0, value=0.2, step=0.05, label="Coherence A (proportion)")
    lvl2 = mo.ui.slider(0.0, 1.0, value=0.5, step=0.05, label="Coherence B (proportion)")
    lvl3 = mo.ui.slider(0.0, 1.0, value=0.8, step=0.05, label="Coherence C (proportion)")
    return lvl1, lvl2, lvl3


@app.cell
def _(lvl1, lvl2, lvl3, mo, motion_coherence_preview_iframe_html):
    def preview(stim_level: float, label: str):
        html = motion_coherence_preview_iframe_html(
            float(stim_level),
            instance_label=label,
            n_dots=80,
            duration_s=5.0,
            seed=42,
        )
        return mo.Html(html)

    panel = mo.vstack(
        [
            mo.md("### Stimulus Selection for Simulation"),
            mo.hstack(
                [
                    mo.vstack([preview(lvl1.value, "A"), lvl1], gap=0.4),
                    mo.vstack([preview(lvl2.value, "B"), lvl2], gap=0.4),
                    mo.vstack([preview(lvl3.value, "C"), lvl3], gap=0.4),
                ],
                gap=1.2,
                justify="center",
            ),
        ],
        gap=0.5,
    )
    panel
    return


@app.cell
def _(mo):
    demo_trials_per_level = mo.ui.number(
        start=1,
        stop=20,
        value=5,
        label="Trials per level (count, demonstration)",
    )
    demo_restart = mo.ui.refresh(label="Restart demo")
    return demo_restart, demo_trials_per_level


@app.cell
def _(
    JsPsychTrialEngine,
    build_motion_demo_levels,
    build_jspsych_runner_html,
    build_motion_demo_timeline,
    demo_restart,
    demo_trials_per_level,
    lvl1,
    lvl2,
    lvl3,
    mo,
    motion_demo_runner_config,
    render_srcdoc_iframe,
):
    _ = demo_restart.value
    a = max(0.0, min(1.0, float(lvl1.value)))
    b = max(0.0, min(1.0, float(lvl2.value)))
    c = max(0.0, min(1.0, float(lvl3.value)))
    reps = max(1, min(20, int(demo_trials_per_level.value or 5)))
    demo_levels = build_motion_demo_levels(a, b, c, reps_per_level=reps)
    n_motion = len(demo_levels)
    demo_engine = JsPsychTrialEngine()
    demo_timeline = build_motion_demo_timeline(demo_engine, demo_levels)
    demo_html = build_jspsych_runner_html(
        demo_timeline,
        config=motion_demo_runner_config(),
    )
    demo_iframe = mo.Html(
        render_srcdoc_iframe(demo_html, title="jsPsych Demo", height=520)
    )
    mo.vstack(
        [
            mo.md("### Demonstration"),
            mo.md(
                f"_{reps} trials per stim level ({n_motion} motion trials across A, B, C). "
                "Motion direction is random each trial. "
                "When you finish, bar charts matching the **Plots** section appear in this window._"
            ),
            demo_trials_per_level,
            demo_iframe,
            demo_restart,
        ],
        gap=0.5,
    )
    return


@app.cell
def _(mo):
    n_trials = mo.ui.number(
        start=10,
        stop=300,
        value=100,
        label="Trials per level (count)",
    )
    n_observers = mo.ui.number(
        start=1,
        stop=30,
        value=3,
        label="Participants (count)",
    )

    sigma0 = mo.ui.slider(
        0.0, 2.0, value=0.0, step=0.05, label="σ₀ — noise floor (evidence SD)"
    )
    sigma_scale = mo.ui.slider(
        0.0, 10.0, value=0.9, step=0.05, label="σ scale (evidence SD / coherence)"
    )
    lapse = mo.ui.slider(
        0.0, 0.2, value=0.0, step=0.005, label="Lapse rate (proportion)"
    )

    ndt = mo.ui.slider(0.05, 1.0, value=0.30, step=0.01, label="Non-decision time (s)")
    rt_scale = mo.ui.slider(0.05, 1.0, value=0.35, step=0.05, label="RT scale (s)")
    rt_noise = mo.ui.slider(0.0, 0.2, value=0.03, step=0.01, label="RT noise SD (s)")

    run_sim = mo.ui.run_button(label="Run simulation")

    fit_draws = mo.ui.slider(
        100, 2000, value=600, step=100, label="HSSM posterior draws (samples)"
    )
    fit_tune = mo.ui.slider(
        100, 2000, value=600, step=100, label="HSSM warmup tune (samples)"
    )
    fit_chains = mo.ui.slider(1, 4, value=2, step=1, label="HSSM MCMC chains (count)")
    return (
        fit_chains,
        fit_draws,
        fit_tune,
        lapse,
        n_observers,
        n_trials,
        ndt,
        rt_noise,
        rt_scale,
        run_sim,
        sigma0,
        sigma_scale,
    )


@app.cell
def _(
    fit_chains,
    fit_draws,
    fit_tune,
    lapse,
    mo,
    n_observers,
    n_trials,
    ndt,
    rt_noise,
    rt_scale,
    run_sim,
    sigma0,
    sigma_scale,
):
    run_fit = mo.ui.run_button(label="Run hssm fit", disabled=not bool(run_sim.value))

    simulator_info_row = mo.Html(
        """
<div style="display:inline-flex;align-items:flex-start;gap:0.4rem;max-width:100%;">
  <details style="position:relative;margin:0;">
    <summary
      aria-label="How the simulated observer works"
      style="cursor:pointer;list-style:none;display:inline-flex;align-items:center;gap:0.35rem;
        font-weight:600;color:inherit;"
    >
      <span>Simulator Info</span>
      <span
        style="display:inline-flex;align-items:center;justify-content:center;width:1.35rem;
          height:1.35rem;border:1px solid #cbd5e1;border-radius:999px;font-size:0.8rem;
          font-weight:600;color:#64748b;background:#f8fafc;"
      >?</span>
    </summary>
    <div
      style="position:absolute;left:calc(100% + 0.4rem);top:0;z-index:1000;min-width:18rem;
        max-width:min(22rem,calc(100vw - 2rem));padding:0.65rem 0.75rem;font-size:0.82rem;
        line-height:1.45;color:#0f172a;background:#fff;border:1px solid #cbd5e1;border-radius:6px;
        box-shadow:0 4px 12px rgba(15,23,42,0.12);text-align:left;"
    >
      <p style="margin:0 0 0.5rem 0;"><strong>Experiment.</strong> For each participant, the app
      runs every combination of the three coherence levels (A/B/C) and your chosen trial count.
      Each trial is a binary left/right motion discrimination with random direction, using the
      same side-strength encoding as the browser demo.</p>
      <p style="margin:0 0 0.5rem 0;"><strong>Observer.</strong> Responses are generated by
      <code>NAfcObserver</code>: per-alternative evidence is <em>weight × strength + noise</em>,
      with noise increasing as coherence decreases; choices follow a lapse draw or
      <code>argmax</code> on evidence; RT uses non-decision time plus a term inversely related
      to the evidence margin (or a lapse RT path).</p>
      <p style="margin:0;"><strong>Output.</strong> Run simulation builds a trial-level table
      (accuracy, RT in s) used by the summary table, plots, and (after fitting) HSSM.</p>
    </div>
  </details>
</div>
"""
    )

    mo.md("### Simulation")
    mo.vstack(
        [
            mo.accordion(
                {
                    "Simulator settings": mo.vstack(
                        [
                            mo.hstack([n_trials, n_observers], gap=1),
                            mo.hstack([sigma0, sigma_scale, lapse], gap=1),
                            mo.hstack([ndt, rt_scale, rt_noise], gap=1),
                        ],
                        gap=0.6,
                    ),
                }
            ),
            run_sim,
            simulator_info_row,
            mo.accordion(
                {
                    "Fitting settings": mo.vstack(
                        [mo.hstack([fit_draws, fit_tune, fit_chains], gap=1)],
                        gap=0.6,
                    ),
                }
            ),
            run_fit,
        ],
        gap=0.5,
    )
    return run_fit


@app.cell
def _(
    JsPsychTrialEngine,
    NAfcObserver,
    lvl1,
    lvl2,
    lvl3,
    lapse,
    mo,
    n_observers,
    n_trials,
    ndt,
    np,
    pd,
    rt_noise,
    rt_scale,
    run_sim,
    sigma0,
    sigma_scale,
):
    mo.stop(not run_sim.value)

    condition_levels = [float(lvl1.value), float(lvl2.value), float(lvl3.value)]
    condition_levels = [max(0.0, c) for c in condition_levels]

    nT = max(10, min(300, int(n_trials.value or 100)))
    nS = max(1, min(30, int(n_observers.value or 3)))

    rng = np.random.default_rng(12345)
    sim = JsPsychTrialEngine(rng=rng)

    rows: list[dict] = []
    for subj in range(nS):
        obs_rng = np.random.default_rng(rng.integers(0, 2**32 - 1))
        obs = NAfcObserver(
            sigma0=float(sigma0.value),
            sigma_scale=float(sigma_scale.value),
            lapse_rate=float(lapse.value),
            rt_scale=float(rt_scale.value),
            rt_noise=float(rt_noise.value),
            rng=obs_rng,
        )
        for level in condition_levels:
            trials = sim.make_trials(stim_level=level, n_trials=nT)
            for tr in sim.iter_trials(trials):
                choice_index, rt = obs.choose(
                    evidence_weight=tr["evidence_weight"],
                    stim_strengths=tr["stim_strengths"],
                    ndt=float(ndt.value),
                )
                response = -1 if int(choice_index) == 0 else 1
                rows.append(
                    dict(
                        subj=subj,
                        stim_level=level,
                        choice_index=int(choice_index),
                        response=int(response),
                        rt=float(rt),
                        correct=int(int(choice_index) == int(tr["correct_index"])),
                    )
                )

    df = pd.DataFrame(rows)
    df
    return df


@app.cell
def _(df, mo, summarize_behavior):
    by = summarize_behavior(df)
    by_labeled = by.rename(
        columns={
            "stim_level": "coherence (proportion)",
            "acc": "accuracy (proportion)",
            "rt_mean": "mean RT (s)",
            "rt_med": "median RT (s)",
            "n": "trials (count)",
        }
    )
    mo.vstack(
        [
            mo.md("### Simulated behavior summary"),
            mo.Html(by_labeled.to_html(index=False, classes="dataframe")),
        ],
        gap=0.5,
    )
    return by


@app.cell
def _(by, mo):
    import altair as alt

    base = alt.Chart(by)
    acc_chart = (
        base.mark_bar()
        .encode(
            x=alt.X("stim_level:Q", title="Coherence (proportion)"),
            y=alt.Y("acc:Q", title="Accuracy (proportion)", scale=alt.Scale(domain=[0, 1])),
            tooltip=[
                alt.Tooltip("stim_level:Q", title="Coherence (proportion)", format=".2f"),
                alt.Tooltip("acc:Q", title="Accuracy (proportion)", format=".3f"),
                alt.Tooltip("n:Q", title="Trials (count)"),
                alt.Tooltip("rt_mean:Q", title="Mean RT (s)", format=".3f"),
            ],
        )
        .properties(width=260, height=220, title="Accuracy by coherence")
    )
    rt_chart = (
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
        .properties(width=260, height=220, title="Mean RT by coherence")
    )
    chart = mo.ui.altair_chart(alt.hconcat(acc_chart, rt_chart))
    mo.vstack([mo.md("### Plots"), chart], gap=0.5)
    return


@app.cell
def _(df, fit_chains, fit_draws, fit_tune, mo, fit_hssm_model, run_fit, summarize_posterior):
    mo.stop(not run_fit.value)

    header = mo.md("### HSSM fit (DDM drift depends on coherence)")
    model, idata = fit_hssm_model(
        df,
        draws=int(fit_draws.value),
        tune=int(fit_tune.value),
        chains=int(fit_chains.value),
    )
    summ = summarize_posterior(idata)
    _blocks = [mo.md("#### Posterior summary"), mo.Html(summ.to_html(classes="dataframe"))]
    if int(fit_chains.value) < 2:
        _blocks.append(
            mo.Html(
                '<div style="font-size:0.85rem;color:#92400e;margin-top:0.15rem;">'
                "Note: convergence diagnostics like <code>r_hat</code> require at least 2 chains; "
                "current fit used 1 chain."
                "</div>"
            )
        )
    summary_block = mo.vstack(_blocks, gap=0.5)
    mo.vstack([header, summary_block], gap=0.75)
    return model, idata


@app.cell
def _(df, idata, mo, model):
    import base64 as _base64
    import io as _io

    import hssm.plotting as _hplot
    _idata_pp = model.sample_posterior_predictive(
        idata=idata,
        inplace=False,
        include_group_specific=False,
        kind="response",
    )
    _ax_or_grid = _hplot.plot_model_cartoon(
        model,
        idata=_idata_pp,
        data=df,
        predictive_group="posterior_predictive",
        plot_data=True,
        n_samples=20,
        plot_predictive_samples=True,
        bins=100,
        title="HSSM Model Cartoon",
        xlabel="Response time (s)",
    )

    if isinstance(_ax_or_grid, list) and _ax_or_grid:
        _obj = _ax_or_grid[0]
    else:
        _obj = _ax_or_grid

    _fig = getattr(_obj, "figure", None)
    if _fig is None:
        _fig = getattr(_obj, "fig", None)
    if _fig is None and hasattr(_obj, "get_figure"):
        _fig = _obj.get_figure()
    if _fig is None:
        raise TypeError(f"Unexpected plot object type: {type(_obj)}")
    _w, _h = _fig.get_size_inches()
    _scale = 2.0 / 3.0
    _fig.set_size_inches(max(1.5, _w * _scale), max(1.0, _h * _scale))
    for _ax in _fig.axes:
        _ax.title.set_fontsize(max(6, _ax.title.get_fontsize() * _scale))
        _ax.xaxis.label.set_fontsize(max(6, _ax.xaxis.label.get_fontsize() * _scale))
        _ax.yaxis.label.set_fontsize(max(6, _ax.yaxis.label.get_fontsize() * _scale))
        _ax.tick_params(axis="both", labelsize=max(6, 10 * _scale))
        _legend = _ax.get_legend()
        if _legend is not None:
            _legend.set_title(
                _legend.get_title().get_text(),
                prop={"size": max(6, 10 * _scale)},
            )
            for _txt in _legend.get_texts():
                _txt.set_fontsize(max(6, _txt.get_fontsize() * _scale))
            _legend.borderpad *= _scale
            _legend.labelspacing *= _scale
            _legend.handlelength *= _scale
            _legend.handletextpad *= _scale
            _legend.borderaxespad *= _scale

    _buf = _io.BytesIO()
    _fig.savefig(_buf, format="png", dpi=150, bbox_inches="tight")
    _buf.seek(0)
    _b64 = _base64.b64encode(_buf.read()).decode("ascii")
    _img = mo.Html(
        f'<img alt="HSSM model cartoon" src="data:image/png;base64,{_b64}" '
        'style="width:50%;max-width:50%;height:auto;border:1px solid #ddd;border-radius:6px;" />'
    )
    _out = mo.vstack([mo.md("### HSSM model cartoon"), _img], gap=0.5)
    _out
    return


if __name__ == "__main__":
    app.run()

