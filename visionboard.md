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

1. User explores a live jsPsych-style demo in the app (coherence levels follow Stim Level A/B/C sliders; **Restart demo** rebuilds the iframe).
2. User configures stimulus and observer parameters.
3. Simulation generates trial-level response/RT data via `NAfcObserver`.
4. HSSM fitting is run from dedicated controls.
5. Model summaries and model-cartoon visualization are shown in-app.

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
- Add validation tests for `agents/evidence_observer.py`, `tasks/jspsych_motion.py`, and `analysis/descriptive_stats.py` to lock in expected behavior.
- Add a second task prototype (non-motion or multi-choice variant) to verify interchangeability claims in practice.
- Provide environment profile docs/scripts for reproducible setup across Linux variants (system deps + Python/uv workflow).
- Add lightweight CI checks (import/syntax/tests) so modular refactors stay safe as components grow.
- Create a configurable app shell in `apps/` so multiple demos/tasks can share common controls, run buttons, and plotting layout.


## Current Observer Notes

The evidence observer path is anchored on an evidence-based decision rule with explicit separations between latent evidence generation, lapse behavior, and RT construction.

- Trial encoding for binary motion now uses side-strength coding (`evidence_weight=[1,1]`, side-specific `stim_strengths`) so `argmax(evidence)` aligns with the correct side.
- Sensory noise is difficulty-scaled in the default evidence model (`coherence = max(stim_strengths)`, noise uses `1 - coherence`).
- Observer noise is parameterized by `sigma0` (noise floor) and `sigma_scale` (difficulty slope).
- The observer supports an optional custom signal-model hook so both decisions and non-lapse RTs can share a custom latent signal.
- Non-lapse RT uses `ndt + rt_scale / evidence` with additive Gaussian noise; at very low evidence, RT can become large.

This behavior is currently useful for exploratory simulation and model-shape intuition, with a known trade-off around low-evidence RT tails.

## Current Runtime Notes

The browser runner is split into composable assets under `runtime/`:

- **Core** (`jspsych_runner_core.js`): timeline decode, plugin binding, jsPsych lifecycle, optional arrow-key scroll guard.
- **Boot** (`jspsych_runner_boot.js`): reads base64-injected config + timeline.
- **Stimulus display** (`runtime/stimulus_display/`, e.g. `motion_rdk.js`): optional browser animation; motion is started from trial `on_load`, not globally at boot.
- **Assembly** (`jspsych_runner.py` + `.html` + `.css`): inlined into marimo `srcdoc` iframes.

jsPsych **v7** requires the instance from `initJsPsych()` — exposed as `window.__jsPsychInstance` for Python-authored string callbacks (`on_finish`, dynamic `stimulus` functions). Global `jsPsych` must not be used in timeline strings.

Recent fixes aligned with this model:

- Motion trial encoding uses side-strength coding so `argmax(evidence)` matches correct side.
- Demo timeline uses slider-defined coherence levels and supports iframe restart.
- `MigrationError` from global `jsPsych` usage resolved in motion scoring and demo summary trials.
