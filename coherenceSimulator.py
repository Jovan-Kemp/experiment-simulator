import marimo

from observers import MotionCoherenceObserver
from graphics import motion_coherence_preview_iframe_html
from simulators import JsPsychStyleTrialSimulator

app = marimo.App(width="full")


@app.cell
def _():
    import numpy as np
    import pandas as pd

    import marimo as mo

    return mo, np, pd


@app.cell
def _():
    # Re-export for marimo dependency injection
    from observers import MotionCoherenceObserver
    from graphics import motion_coherence_preview_iframe_html
    from simulators import JsPsychStyleTrialSimulator

    return (
        JsPsychStyleTrialSimulator,
        MotionCoherenceObserver,
        motion_coherence_preview_iframe_html,
    )


@app.cell
def _(mo):
    mo.md(
        r"""
## Motion coherence tutorial (simulation + HSSM fit)

This app simulates a **binary left/right motion task** at **three coherence levels** shown side-by-side.

- **Observer**: makes a noisy internal motion estimate with **Gaussian noise that depends on coherence**, plus a **lapse rate** (random responses).
- **Task**: trials use **jsPsych-style** objects (JSON-serializable timeline items) generated in Python; motion previews run in the browser via **Canvas** (no PsychoPy).
- **Fit**: fits a **HSSM** DDM with drift \(v\) regressed on coherence.
"""
    )
    return


@app.cell
def _(mo):
    coh1 = mo.ui.slider(0.0, 1.0, value=0.2, step=0.05, label="Coherence A")
    coh2 = mo.ui.slider(0.0, 1.0, value=0.5, step=0.05, label="Coherence B")
    coh3 = mo.ui.slider(0.0, 1.0, value=0.8, step=0.05, label="Coherence C")

    n_trials = mo.ui.slider(20, 2000, value=200, step=20, label="Trials per coherence")
    n_observers = mo.ui.slider(1, 30, value=3, step=1, label="Observers")

    sigma0 = mo.ui.slider(0.05, 2.0, value=0.9, step=0.05, label="Stimulus-dependent noise scale (σ0)")
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
            mo.md("#### Motion coherence (Canvas preview, 20 dots; jsPsych-style RDK logic)"),
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
        coh1,
        coh2,
        coh3,
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
def _(coh1, coh2, coh3, mo, motion_coherence_preview_iframe_html):
    def preview(coh: float, label: str):
        html = motion_coherence_preview_iframe_html(
            float(coh),
            instance_label=label,
            n_dots=20,
            duration_s=5.0,
            seed=42,
        )
        return mo.Html(html)

    panel = mo.hstack(
        [
            mo.vstack([preview(coh1.value, "A"), coh1], gap=0.4),
            mo.vstack([preview(coh2.value, "B"), coh2], gap=0.4),
            mo.vstack([preview(coh3.value, "C"), coh3], gap=0.4),
        ],
        gap=1.2,
    )
    panel
    return (panel,)


@app.cell
def _(
    JsPsychStyleTrialSimulator,
    MotionCoherenceObserver,
    auto_run,
    coh1,
    coh2,
    coh3,
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

    coherences = [float(coh1.value), float(coh2.value), float(coh3.value)]
    coherences = [float(np.clip(c, 0.0, 1.0)) for c in coherences]

    nT = int(n_trials.value)
    nS = int(n_observers.value)

    rng = np.random.default_rng(12345)
    sim = JsPsychStyleTrialSimulator(rng=rng)

    rows: list[dict] = []
    for subj in range(nS):
        obs_rng = np.random.default_rng(rng.integers(0, 2**32 - 1))
        obs = MotionCoherenceObserver(sigma0=float(sigma0.value), lapse_rate=float(lapse.value), rng=obs_rng)

        for c in coherences:
            trials = sim.make_trials(coherence=c, n_trials=nT)
            for tr in sim.iter_trials(trials):
                stim_dir = int(tr["stim_dir"])
                response = obs.choose(stim_dir=stim_dir, coherence=c)
                rt = obs.rt(
                    stim_dir=stim_dir,
                    coherence=c,
                    ndt=float(ndt.value),
                    rt_scale=float(rt_scale.value),
                    rt_noise=float(rt_noise.value),
                )
                rows.append(
                    dict(
                        subj=subj,
                        coherence=c,
                        stim_dir=stim_dir,
                        response=int(response),
                        rt=float(rt),
                        correct=int(response == stim_dir),
                    )
                )

    df = pd.DataFrame(rows)
    df
    return coherences, df, nS, nT


@app.cell
def _(df, mo):
    by = (
        df.groupby(["coherence"], as_index=False)
        .agg(acc=("correct", "mean"), rt_mean=("rt", "mean"), rt_med=("rt", "median"), n=("rt", "size"))
        .sort_values("coherence")
    )

    mo.vstack(
        [
            mo.md("### Simulated behavior summary"),
            mo.Html(by.to_html(index=False, classes="dataframe")),
        ],
        gap=0.5,
    )
    return (by,)


@app.cell
def _(by, mo):
    chart = mo.ui.altair_chart(
        {
            "data": {"values": by.to_dict(orient="records")},
            "hconcat": [
                {
                    "mark": {"type": "bar"},
                    "encoding": {
                        "x": {"field": "coherence", "type": "quantitative"},
                        "y": {"field": "acc", "type": "quantitative", "scale": {"domain": [0, 1]}},
                        "tooltip": [{"field": "n"}, {"field": "rt_mean"}, {"field": "acc"}],
                    },
                    "width": 260,
                    "height": 220,
                    "title": "Accuracy by coherence",
                },
                {
                    "mark": {"type": "bar"},
                    "encoding": {
                        "x": {"field": "coherence", "type": "quantitative"},
                        "y": {"field": "rt_mean", "type": "quantitative"},
                        "tooltip": [{"field": "n"}, {"field": "rt_mean"}, {"field": "rt_med"}],
                    },
                    "width": 260,
                    "height": 220,
                    "title": "Mean RT by coherence",
                },
            ],
        }
    )
    mo.vstack([mo.md("### Plots"), chart], gap=0.5)
    return (chart,)


@app.cell
def _(df, fit_chains, fit_draws, fit_tune, mo):
    import hssm

    header = mo.md("### HSSM fit (DDM drift depends on coherence)")

    include = [
        {
            "name": "v",
            "formula": "v ~ 1 + coherence",
            "prior": {
                "Intercept": {"name": "Normal", "mu": 0.0, "sigma": 1.5},
                "coherence": {"name": "Normal", "mu": 0.0, "sigma": 2.0},
            },
            "link": "identity",
        }
    ]

    model = hssm.HSSM(data=df, model="ddm", include=include)
    idata = model.sample(
        draws=int(fit_draws.value),
        tune=int(fit_tune.value),
        chains=int(fit_chains.value),
        cores=min(4, int(fit_chains.value)),
        progressbar=True,
    )

    try:
        import arviz as az

        summ = az.summary(idata, var_names=["~log_likelihood"], round_to=3)
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

    return idata, model


if __name__ == "__main__":
    app.run()
