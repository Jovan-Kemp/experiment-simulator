# Visionboard

## Project Understanding

This project is building a modular experimentation stack for behavioral tasks, centered on a `marimo` app and jsPsych runtime integration, with HSSM-based analysis at the end of the pipeline.

At a high level, the system is designed to support:

- **Demo experiments** for interactive teaching and rapid iteration
- **Simulated experiments** using configurable virtual observers
- **Participant-facing experiments** using browser-native task execution
- **Unified analysis outputs** using sequential sampling models (HSSM) and summary plots

## Core Design Intent

The architecture separates concerns so pieces can be swapped without rewriting the full workflow:

- `tasks/` defines trial structure and experiment logic
- `renderers/` defines stimulus display helpers and preview behavior
- `agents/` defines observer behavior for synthetic data generation
- `runtime/` executes jsPsych timelines in browser-compatible form
- `analysis/` holds model fitting and descriptive statistics
- `apps/` orchestrates controls, execution flow, and visualization

The key idea is **interchangeability**:
- new tasks should plug into the same run/fit pipeline
- new stimuli modalities should reuse orchestration patterns
- human and virtual response sources should be exchangeable
- analysis should remain decoupled from task implementation details

## Current Working Flow

1. User explores live motion previews (coherence A/B/C sliders, adjustable dot lifetime).
2. User runs the jsPsych demo (intro → countdown → motion trials with feedback → in-iframe result charts); **Restart demo** rebuilds the iframe.
3. User configures observer and sampling parameters.
4. Simulation generates trial-level response/RT data via `NAfcObserver`.
5. HSSM fitting is run from dedicated controls.
6. Model summaries and model-cartoon visualization are shown in-app.

## Near-Term Priorities

- Finish wiring `postMessage` jsPsych results into a validated dataframe ingest path (human participants).
- Add regression coverage for jsPsych v7 runner callbacks (`window.__jsPsychInstance` contract).
- Keep run controls explicit and predictable (simulate first, fit second).
- Improve robustness and interpretability of HSSM outputs under low-sample settings.
- Expand reusable statistics utilities (`analysis/descriptive_stats.py`).
- Preserve clean module boundaries as new task types are added.

## Long-Term Direction

Evolve from a single demo into a reusable experiment framework where task templates, observers, rendering strategies, and analysis modules can be composed quickly for new paradigms.

## Immediate TODO

- Add a task registry API so new paradigms can be selected and launched without editing `apps/coherence_app.py`.
- Define a shared trial/result adapter interface between `tasks/`, `runtime/`, and `analysis/` to reduce task-specific glue code.
- Implement persistent run-state management in the app (simulation complete, fit complete, last dataset) so workflows are explicit and recoverable.
- Ingest human jsPsych results (`postMessage` -> dataframe schema) parallel to the simulated observer path.
- Expand `analysis/` with reusable report builders (summary tables + standard plots) independent of any single task.
- Add validation tests for `agents/evidence_observer.py`, `tasks/trial_generator.py`, and `analysis/descriptive_stats.py` to lock in expected behavior.
- Add a second task prototype (non-motion or multi-choice variant) to verify interchangeability claims in practice.
- Provide environment profile docs/scripts for reproducible setup across Linux variants (system deps + Python/uv workflow).
- Add lightweight CI checks (import/syntax/tests) so modular refactors stay safe as components grow.
- Create a configurable app shell in `apps/` so multiple demos/tasks can share common controls, run buttons, and plotting layout.

## Current Observer Notes

The evidence observer path is anchored on an evidence-based decision rule with explicit separations between latent evidence generation, lapse behavior, and RT construction.

- Trial encoding for binary motion: `motion_stimulus_to_strengths` in `coherence_app.py` maps experiment params to observer latent strengths.
- `evidence_weight=(1,1)` on the observer means no directional bias.
- Sensory noise is difficulty-scaled in the default evidence model (`coherence = max(stim_strengths)`, noise uses `1 - coherence`).
- Observer noise is parameterized by `sigma0` (noise floor) and `sigma_scale` (difficulty slope).
- The observer supports an optional custom signal-model hook so both decisions and non-lapse RTs can share a custom latent signal.
- Non-lapse RT uses `ndt + rt_scale / evidence` with additive Gaussian noise; at very low evidence, RT can become large.

This behavior is currently useful for exploratory simulation and model-shape intuition, with a known trade-off around low-evidence RT tails.

## Current Runtime Notes

The browser runner is split into composable assets under `runtime/`:

- **Core** (`jspsych_runner_core.js`): timeline decode, plugin binding, jsPsych lifecycle, optional arrow-key scroll guard.
- **Boot** (`jspsych_runner_boot.js`): reads base64-injected config + timeline.
- **Stimulus display** (`runtime/stimulus_display/motion_rdk.js`): time-based motion (px/s), dot lifetime with edge/out-of-bounds respawn; started from trial `on_load`.
- **Demo charts** (`demo_results_charts.js`): Vega-Lite accuracy and mean RT bars in the iframe when `RunnerConfig.show_results_charts` is enabled.
- **Assembly** (`jspsych_runner.py` + `.html` + `.css`): inlined into marimo `srcdoc` iframes.

jsPsych **v7** requires the instance from `initJsPsych()` — exposed as `window.__jsPsychInstance` for Python-authored string callbacks (`on_finish`, dynamic `stimulus` functions). Global `jsPsych` must not be used in timeline strings.

Motion display parameters:

- **Speed**: pixels per second via `data-speed-px-s` (not per-frame), for cross-browser consistency.
- **Canvas**: fixed pixel dimensions in HTML/CSS (no responsive resize).
- **Dot lifetime**: user-adjustable in `coherence_app.py`; dots respawn after lifetime expiry or leaving the aperture.
- **App-specific defaults** (canvas size, dot count, speed, seed) live in `coherence_app.py`; passed via each trial's `stimulus_params`.

Trial generation architecture:

- Generic `Trial` contract: `stimulus_params` and presentation timing only (no latent evidence on trial).
- Abstract `TrialGenerator` stores trial parameter dicts with `next_trial()` / `reset()`; `FactorTrialGenerator` is the concrete factorial/list implementation.
- Observer hyperparameters (`sigma0`, lapse, RT scale, …) remain on `NAfcObserver` only.

Recent alignment with this model:

- Motion trial encoding uses side-strength coding so `argmax(evidence)` matches correct side.
- Demo timeline uses slider-defined coherence levels, countdown, per-trial feedback, and iframe restart.
- End-of-demo charts render inside the jsPsych iframe (filtered to `motion_coherence` trials).
- `MigrationError` from global `jsPsych` usage resolved in motion scoring and demo feedback trials.
