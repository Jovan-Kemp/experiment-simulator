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
        summarize_drift_posterior_hssm_api,
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
        summarize_drift_posterior_hssm_api,
        summarize_posterior,
    )


@app.cell
def _(mo):
    mo.md(
        r"""
## HSSM demonstration with motion coherence simulated experiment

This app simulates a **binary left/right motion task** at **three stimulus levels** shown side-by-side.

- **Observer**: n-AFC virtual observer with **stimulus-level dependent Gaussian noise** plus lapse noise.
- **Task**: trials use **jsPsych-style** objects generated in Python; jsPsych can execute these trials directly in-browser.
- **Fit**: fits a **HSSM** DDM with drift \(v\) regressed on `stim_level`.
"""
    )
    return


@app.cell
def _(build_jspsych_runner_html):
    DEMO_LEVELS = [("A", 0.2), ("B", 0.5), ("C", 0.8), ("A", 0.2), ("B", 0.5), ("C", 0.8)]

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
            "Your accuracy was ${c} / ${n}<br/>check out the simulated experiment below."
            "</div>`;"
            "}"
        ),
        "choices": "ALL_KEYS",
    }

    def build_demo_timeline(engine: object) -> list[dict[str, object]]:
        demo_trials: list[dict] = []
        for idx, (label, level) in enumerate(DEMO_LEVELS, start=1):
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
def _(JsPsychTrialEngine, build_demo_timeline, mo, render_runner_iframe):
    demo_engine = JsPsychTrialEngine()
    demo_timeline = build_demo_timeline(demo_engine)
    demo_iframe = mo.Html(render_runner_iframe(demo_timeline, title="jsPsych Demo", height=280))
    mo.vstack([mo.md("### Demonstration"), demo_iframe], gap=0.5)
    return


@app.cell
def _(mo):
    lvl1 = mo.ui.slider(0.0, 1.0, value=0.2, step=0.05, label="Stim Level A")
    lvl2 = mo.ui.slider(0.0, 1.0, value=0.5, step=0.05, label="Stim Level B")
    lvl3 = mo.ui.slider(0.0, 1.0, value=0.8, step=0.05, label="Stim Level C")

    n_trials = mo.ui.slider(20, 2000, value=200, step=20, label="Trials per stim level")
    n_observers = mo.ui.slider(1, 30, value=3, step=1, label="Observers")

    sigma0 = mo.ui.slider(0.05, 10.0, value=0.9, step=0.05, label="Stimulus-dependent noise (Higher value means more noise for lower coherence levels)")
    lapse = mo.ui.slider(0.0, 0.2, value=0.02, step=0.005, label="Lapse rate")

    ndt = mo.ui.slider(0.05, 1.0, value=0.30, step=0.01, label="Non-decision time (s)")
    rt_scale = mo.ui.slider(0.05, 2.0, value=0.65, step=0.05, label="RT scale")
    rt_noise = mo.ui.slider(0.0, 0.5, value=0.05, step=0.01, label="RT noise (s)")

    auto_run = mo.ui.checkbox(value=False, label="Auto-run (rerun on slider changes)")
    run_sim = mo.ui.run_button(kind="success", label="Run simulation + fit")

    fit_draws = mo.ui.slider(100, 2000, value=600, step=100, label="HSSM draws")
    fit_tune = mo.ui.slider(100, 2000, value=600, step=100, label="HSSM tune")
    fit_chains = mo.ui.slider(1, 4, value=2, step=1, label="HSSM chains")

    controls = mo.vstack(
        [
            mo.md("### Controls"),
            mo.md("#### Motion preview (Canvas, 20 dots; jsPsych-style RDK logic)"),
            mo.hstack([n_trials, n_observers], gap=1),
            mo.hstack([sigma0, lapse], gap=1),
            mo.hstack([ndt, rt_scale, rt_noise], gap=1),
            mo.hstack([auto_run, run_sim], gap=1),
            mo.md("### Fit settings (HSSM / PyMC)"),
            mo.hstack([fit_draws, fit_tune, fit_chains], gap=1),
        ],
        gap=0.6,
    )
    controls
    return (
        auto_run,
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
    )


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

    panel = mo.hstack(
        [
            mo.vstack([preview(lvl1.value, "A"), lvl1], gap=0.4),
            mo.vstack([preview(lvl2.value, "B"), lvl2], gap=0.4),
            mo.vstack([preview(lvl3.value, "C"), lvl3], gap=0.4),
        ],
        gap=1.2,
    )
    panel
    return


@app.cell
def _(
    JsPsychTrialEngine,
    NAfcObserver,
    auto_run,
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
):
    mo.stop(not (auto_run.value or run_sim.value))

    stim_levels = [float(lvl1.value), float(lvl2.value), float(lvl3.value)]
    stim_levels = [max(0.0, c) for c in stim_levels]

    nT = int(n_trials.value)
    nS = int(n_observers.value)

    rng = np.random.default_rng(12345)
    sim = JsPsychTrialEngine(rng=rng)

    rows: list[dict] = []
    for subj in range(nS):
        obs_rng = np.random.default_rng(rng.integers(0, 2**32 - 1))
        obs = NAfcObserver(sigma0=float(sigma0.value), lapse_rate=float(lapse.value), rng=obs_rng)
        for level in stim_levels:
            trials = sim.make_trials(stim_level=level, n_trials=nT)
            for tr in sim.iter_trials(trials):
                choice_index = obs.choose(stim=tr["stim"], stim_levels=tr["stim_levels"])
                response = -1 if int(choice_index) == 0 else 1
                rt = obs.rt(
                    choice_index=choice_index,
                    stim=tr["stim"],
                    stim_levels=tr["stim_levels"],
                    ndt=float(ndt.value),
                    rt_scale=float(rt_scale.value),
                    rt_noise=float(rt_noise.value),
                )
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
def _(df, fit_chains, fit_draws, fit_tune, mo, fit_hssm_model, summarize_posterior):
    header = mo.md("### HSSM fit (DDM drift depends on stim level)")
    model, idata = fit_hssm_model(
        df,
        draws=int(fit_draws.value),
        tune=int(fit_tune.value),
        chains=int(fit_chains.value),
    )
    try:
        summ = summarize_posterior(idata)
        summary_block = mo.vstack(
            [
                mo.md("#### Posterior summary"),
                mo.Html(summ.to_html(classes="dataframe")),
            ],
            gap=0.5,
        )
    except Exception:
        summary_block = mo.md("Fit completed (could not compute ArviZ summary).").callout(kind="warn")
    mo.vstack([header, summary_block], gap=0.75)
    return model, idata


@app.cell
def _(by, idata, mo, model, summarize_drift_posterior_hssm_api):
    import altair as _alt

    try:
        _drift_df = summarize_drift_posterior_hssm_api(
            model,
            idata,
            by["stim_level"].tolist(),
            prob=0.95,
        )
        _band = (
            _alt.Chart(_drift_df)
            .mark_area(opacity=0.22, color="#2563eb")
            .encode(
                x=_alt.X("stim_level:Q", title="Stimulus level"),
                y=_alt.Y("v_lo:Q", title="Drift rate (v)"),
                y2="v_hi:Q",
                tooltip=["stim_level:Q", "v_lo:Q", "v_hi:Q"],
            )
        )
        _line = (
            _alt.Chart(_drift_df)
            .mark_line(color="#1d4ed8", strokeWidth=2.5, point=True)
            .encode(
                x=_alt.X("stim_level:Q", title="Stimulus level"),
                y=_alt.Y("v_mean:Q", title="Drift rate (v)"),
                tooltip=["stim_level:Q", "v_mean:Q", "v_median:Q"],
            )
        )
        _chart = mo.ui.altair_chart((_band + _line).properties(width=520, height=260))
        _out = mo.vstack([mo.md("### HSSM drift posterior"), _chart], gap=0.5)
    except Exception as e:
        _out = mo.md(
            "Could not build drift posterior plot from fit output.\n\n"
            f"Reason: `{type(e).__name__}: {e}`"
        ).callout(kind="warn")
    _out
    return


if __name__ == "__main__":
    app.run()

