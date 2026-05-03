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

    from agents.motion_observer import NAfcObserver
    from analysis.hssm_pipeline import (
        fit_hssm_model,
        summarize_behavior,
        summarize_posterior,
    )
    from renderers.jspsych_preview import motion_coherence_preview_iframe_html
    from runtime.jspsych_runner import build_jspsych_runner_html
    from tasks.jspsych_motion import JsPsychTrialEngine

    return (
        JsPsychTrialEngine,
        NAfcObserver,
        build_jspsych_runner_html,
        fit_hssm_model,
        motion_coherence_preview_iframe_html,
        summarize_behavior,
        summarize_posterior,
    )


@app.cell
def _(mo):
    mo.md(
        r"""
## HSSM demonstration with motion coherence simulated experiment

This app simulates a **binary left/right motion task** at **three stimulus levels** you set with the sliders (shown side-by-side).

- **Observer**: n-AFC virtual observer with **stimulus-level dependent Gaussian noise** plus lapse noise.
- **Task**: trials use **jsPsych-style** objects generated in Python; jsPsych can execute these trials directly in-browser.
- **Fit**: fits a **HSSM** DDM with drift \(v\) regressed on `stim_level`.
"""
    )
    return


@app.cell
def _(build_jspsych_runner_html):
    intro_trial = {
        "type": "html-button-response",
        "stimulus": (
            '<div style="font-size:20px;line-height:1.6;text-align:center;">'
            "Press left arrow for motion to the left, and right arrow for motion to the right"
            "</div>"
        ),
        "choices": ["click here to begin."],
    }
    feedback_trial = {
        "type": "html-keyboard-response",
        "stimulus": (
            "function(){"
            "const d = jsPsych.data.get().last(1).values()[0] || {};"
            "const ok = !!d.correct;"
            "const txt = ok ? 'Correct' : 'Incorrect';"
            "const color = ok ? '#15803d' : '#dc2626';"
            "return `<div style=\"font-size:30px;font-weight:700;color:${color};text-align:center;\">${txt}</div>`;"
            "}"
        ),
        "choices": "NO_KEYS",
        "trial_duration": 1000,
    }
    final_trial = {
        "type": "html-keyboard-response",
        "stimulus": (
            "function(){"
            "const d = jsPsych.data.get().filterCustom(x => x && x.task === 'motion_coherence').values();"
            "const n = d.length;"
            "const c = d.filter(x => x.correct).length;"
            "return `<div style=\"font-size:24px;line-height:1.6;text-align:center;\">"
            "Your accuracy was ${c} / ${n}<br/>"
            "Check out the simulated experiment below.<br/><br/>"
            "<span style=\"font-size:18px;color:#444;\">"
            "Press any key to finish, then use <b>Restart demo</b> under the demo to run again."
            "</span>"
            "</div>`;"
            "}"
        ),
        "choices": "ALL_KEYS",
    }

    def build_demo_timeline(
        engine: object, demo_levels: list[tuple[str, float]]
    ) -> list[dict[str, object]]:
        demo_trials: list[dict] = []
        for idx, (label, level) in enumerate(demo_levels, start=1):
            trial = engine.make_trials(stim_level=level, n_trials=1)[0]
            trial["data"]["label"] = label
            trial["data"]["trial_num"] = idx
            demo_trials.append(trial)
        motion_trials = engine.to_jspsych_timeline(demo_trials, trial_duration_ms=None)
        timeline: list[dict[str, object]] = [intro_trial]
        for trial in motion_trials:
            timeline.extend([trial, feedback_trial])
        timeline.append(final_trial)
        return timeline

    def render_runner_iframe(timeline: list[dict[str, object]], *, title: str, height: int) -> str:
        html = build_jspsych_runner_html(timeline, title=title)
        srcdoc = html.replace("&", "&amp;").replace('"', "&quot;")
        return (
            f'<iframe title="{title}" srcdoc="{srcdoc}" '
            f'width="100%" height="{int(height)}" '
            'style="border:1px solid #ddd;border-radius:6px;"></iframe>'
        )

    return build_demo_timeline, render_runner_iframe


@app.cell
def _(mo):
    demo_restart = mo.ui.refresh(label="Restart demo")
    return demo_restart


@app.cell
def _(
    JsPsychTrialEngine,
    build_demo_timeline,
    demo_restart,
    lvl1,
    lvl2,
    lvl3,
    mo,
    render_runner_iframe,
):
    _ = demo_restart.value
    a = max(0.0, min(1.0, float(lvl1.value)))
    b = max(0.0, min(1.0, float(lvl2.value)))
    c = max(0.0, min(1.0, float(lvl3.value)))
    demo_levels = [
        ("A", a),
        ("B", b),
        ("C", c),
        ("A", a),
        ("B", b),
        ("C", c),
    ]
    demo_engine = JsPsychTrialEngine()
    demo_timeline = build_demo_timeline(demo_engine, demo_levels)
    demo_iframe = mo.Html(render_runner_iframe(demo_timeline, title="jsPsych Demo", height=280))
    mo.vstack(
        [
            mo.md("### Demonstration"),
            demo_iframe,
            demo_restart,
            mo.md(
                "_Coherence levels match **Stim Level A / B / C** above (two blocks A→C). "
                "Motion direction is random each trial. "
                "After the summary screen, click **Restart demo** for a new run._"
            ),
        ],
        gap=0.5,
    )
    return

@app.cell
def _(lvl1, lvl2, lvl3, mo, motion_coherence_preview_iframe_html):
    def preview(stim_level: float, label: str):
        html = motion_coherence_preview_iframe_html(
            float(stim_level),
            instance_label=label,
            n_dots=20,
            duration_s=5.0,
            seed=42,
        )
        return mo.Html(html)

    panel = mo.vstack(
        [mo.vstack(
            [mo.md("### Stimulus Selection for Simulation")],
            gap=0.5,
        ),
        mo.hstack(
            [
                mo.vstack([preview(lvl1.value, "A"), lvl1], gap=0.4),
                mo.vstack([preview(lvl2.value, "B"), lvl2], gap=0.4),
                mo.vstack([preview(lvl3.value, "C"), lvl3], gap=0.4),
            ],
            gap=1.2,
        ),
        ],
        gap=0.5,
    )
    panel
    return

@app.cell
def _(mo):
    lvl1 = mo.ui.slider(0.0, 1.0, value=0.2, step=0.05, label="Stim Level A")
    lvl2 = mo.ui.slider(0.0, 1.0, value=0.5, step=0.05, label="Stim Level B")
    lvl3 = mo.ui.slider(0.0, 1.0, value=0.8, step=0.05, label="Stim Level C")

    n_trials = mo.ui.slider(10, 300, value=100, step=10, label="Trials per stim level")
    n_observers = mo.ui.slider(1, 30, value=3, step=1, label="Observers")

    sigma0 = mo.ui.slider(0.0, 2.0, value=0.0, step=0.05, label="Sigma0 (noise floor)")
    sigma_scale = mo.ui.slider(0.0, 10.0, value=0.9, step=0.05, label="Sigma scale")
    lapse = mo.ui.slider(0.0, 0.2, value=0.0, step=0.005, label="Lapse rate")

    ndt = mo.ui.slider(0.05, 1.0, value=0.30, step=0.01, label="Non-decision time (s)")
    rt_scale = mo.ui.slider(0.05, 1.0, value=0.35, step=0.05, label="RT scale")
    rt_noise = mo.ui.slider(0.0, 0.2, value=0.03, step=0.01, label="RT noise (s)")

    run_sim = mo.ui.run_button(label="Run simulation")

    fit_draws = mo.ui.slider(100, 2000, value=600, step=100, label="HSSM draws")
    fit_tune = mo.ui.slider(100, 2000, value=600, step=100, label="HSSM tune")
    fit_chains = mo.ui.slider(1, 4, value=2, step=1, label="HSSM chains")
    return (
        lvl1,
        lvl2,
        lvl3,
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

    controls = mo.vstack(
        [
            mo.md("### Simulated Observer Settings"),
            mo.hstack([n_trials, n_observers], gap=1),
            mo.hstack([sigma0, sigma_scale, lapse], gap=1),
            mo.hstack([ndt, rt_scale, rt_noise], gap=1),
            mo.hstack([run_sim], gap=1),
            mo.md("### HSSM Fit Settings"),
            mo.hstack([fit_draws, fit_tune, fit_chains], gap=1),
            mo.hstack([run_fit], gap=1),
        ],
        gap=0.6,
    )
    controls
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

    stim_levels = [float(lvl1.value), float(lvl2.value), float(lvl3.value)]
    stim_levels = [max(0.0, c) for c in stim_levels]

    nT = int(n_trials.value)
    nS = int(n_observers.value)

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
        for level in stim_levels:
            trials = sim.make_trials(stim_level=level, n_trials=nT)
            for tr in sim.iter_trials(trials):
                choice_index, rt = obs.choose(
                    stim=tr["stim"],
                    stim_levels=tr["stim_levels"],
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
    mo.vstack(
        [
            mo.md("### Simulated behavior summary"),
            mo.Html(by.to_html(index=False, classes="dataframe")),
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
            x=alt.X("stim_level:Q"),
            y=alt.Y("acc:Q", scale=alt.Scale(domain=[0, 1])),
            tooltip=["n:Q", "rt_mean:Q", "acc:Q"],
        )
        .properties(width=260, height=220, title="Accuracy by stim level")
    )
    rt_chart = (
        base.mark_bar()
        .encode(
            x=alt.X("stim_level:Q"),
            y=alt.Y("rt_mean:Q"),
            tooltip=["n:Q", "rt_mean:Q", "rt_med:Q"],
        )
        .properties(width=260, height=220, title="Mean RT by stim level")
    )
    chart = mo.ui.altair_chart(alt.hconcat(acc_chart, rt_chart))
    mo.vstack([mo.md("### Plots"), chart], gap=0.5)
    return


@app.cell
def _(df, fit_chains, fit_draws, fit_tune, mo, fit_hssm_model, run_fit, summarize_posterior):
    mo.stop(not run_fit.value)

    header = mo.md("### HSSM fit (DDM drift depends on stim level)")
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
        xlabel="Response time",
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

