# Project Documentation

## Scope

This repository is organized as a modular experimentation and analysis workspace.  
It supports:

- browser-based task logic and previews
- interactive control and orchestration in `marimo`
- synthetic and participant-facing data collection flows
- downstream sequential-sampling analysis and visualization

The design favors interchangeable components so task logic, stimulus delivery, and observer/input sources can evolve without rewriting the full stack.

## Directory Map

Current structure:

- `apps/`
  - `coherence_app.py` - marimo orchestration app (demo runner, controls, simulation wiring, plotting, model calls)
- `tasks/`
  - `jspsych_motion.py` - motion trial generation (internal trial contracts)
  - `jspsych_timeline.py` - generic jsPsych timeline adapters and motion trial builder
  - `timelines/motion_demo.py` - precomposed demo timeline + demo `RunnerConfig`
- `renderers/`
  - `jspsych_preview.py` - browser Canvas/iframe stimulus previews
- `agents/`
  - `evidence_observer.py` - virtual observer behavior models
  - `agentsDescriptions.md` - notes and flowcharts for each agent (`NAfcObserver` decision and RT rules)
- `runtime/`
  - `jspsych_runner.py` - `RunnerConfig` + HTML assembly (timeline/config base64 injection)
  - `jspsych_plugins.py` - jsPsych CDN plugin registry
  - `embed.py` - marimo `srcdoc` iframe helper
  - `jspsych_runner.html` - runner page skeleton
  - `jspsych_runner.css` - runner layout overrides (inlined)
  - `jspsych_runner_core.js` - generic timeline decode, plugin bind, jsPsych lifecycle
  - `jspsych_runner_boot.js` - reads injected config/timeline and starts core
  - `stimulus_display/motion_rdk.js` - motion RDK canvas animation (optional per `RunnerConfig`)
- `analysis/`
  - `hssm_pipeline.py` - fit/summarize helpers for HSSM analyses
  - `descriptive_stats.py` - d-prime and standard error descriptive statistics helpers
- `schemas/`
  - `contracts.py` - shared typed data contracts
- `README.md` - quickstart and run instructions
- `DOCUMENTATION.md` - this architecture guide
- `pyproject.toml` - project metadata and dependencies
- `uv.lock` - locked dependency graph for reproducible environments
- `.python-version` - local Python version hint

## Module Responsibilities

### `apps/coherence_app.py`

Role:

- assembles the end-to-end interactive workflow in marimo
- includes an interactive participant-like demo block above controls
- exposes UI controls for coherence/task/sampling settings
- uses separate run controls for simulation and HSSM fit
- renders task previews in the notebook UI
- runs data simulation loops using trial and observer modules
- executes HSSM model fitting and displays summaries/charts including an HSSM model cartoon plot

Key integration boundaries:

- imports trial builders from `tasks/`
- imports observer behavior from `agents/`
- imports preview rendering helpers from `renderers/`
- imports model-fit utilities from `analysis/`
- keeps orchestration separate from implementation modules

Key helper structure:

- builds demo timeline via `tasks/timelines/motion_demo.py`
- uses `runtime/embed.py` for iframe embedding and `RunnerConfig` for demo runner options

### `tasks/jspsych_motion.py`

Role:

- defines motion-coherence trial generation (`make_trials`, internal `JsPsychTrial` contracts)
- delegates jsPsych export to `tasks/jspsych_timeline.py`

Current behavior:

- random left/right direction per trial
- simulation uses trial contracts directly; browser demo uses timeline adapters

### `tasks/jspsych_timeline.py`

Role:

- generic `to_jspsych_timeline(trials, trial_builder, ...)`
- motion-specific `build_motion_keyboard_trial` + `motion_to_jspsych_timeline`
- motion trial `on_finish` scoring and `on_load` canvas hooks (strings revived in browser)

### `tasks/timelines/motion_demo.py`

Role:

- demo-only timeline composition (intro, motion blocks, feedback, summary)
- exports `motion_demo_runner_config()` and `build_motion_demo_timeline()`
- demo coherence levels come from marimo sliders (Stim Level A/B/C), not hardcoded constants

### `agents/evidence_observer.py`

Role:

- contains virtual observer classes for synthetic behavioral data
- models response policy, sensory uncertainty behavior, and lapse/random errors
- can be expanded to host multiple observer families (simple heuristics, SSM-consistent agents, etc.)

Current `NAfcObserver` behavior:

- Latent evidence defaults to `evidence_weight * stim_strengths + Gaussian noise` (`evidence_weight` all ones = no directional bias).
- Sensory noise uses `sigma = sigma0 + sigma_scale * c` where `c` is driven by task difficulty (`1 - coherence`, `coherence = max(stim_strengths)`).
- Lapse path is explicit: with probability `lapse_rate`, choice is random and RT is generated from lapse RT logic.
- Non-lapse choice for n-AFC uses `argmax(evidence)`; 1-stimulus mode uses sign-threshold detection.
- Non-lapse RT uses evidence margin (`abs(chosen - max(other))` for n-AFC) with `rt = ndt + rt_scale / margin_abs + noise`.
- Optional `evidence_model` can override latent evidence generation while preserving shared evidence for choice and non-lapse RT.

Why it exists:

- clean separation between *task definition* and *response-generation policy*
- enables swapping human-input channels vs simulated agents with minimal orchestration changes

### `renderers/jspsych_preview.py`

Role:

- provides UI-facing stimulus preview rendering helpers
- currently generates browser iframe/Canvas snippets for motion previews
- provides trial stimulus canvas markup (data-attribute based) for jsPsych keyboard trials

Why it exists:

- visual preview logic should not live inside trial-generation or observer classes
- allows changing rendering implementation (Canvas, jsPsych plugin views, media assets) without changing trial or analysis code

### `runtime/jspsych_runner.py`

Role:

- creates a standalone jsPsych runtime HTML document for iframe `srcdoc`
- `RunnerConfig` selects plugins, optional `extra_scripts`, and input policies
- injects timeline + config as base64 JSON for the boot script
- loads CDN plugin scripts from `jspsych_plugins.py`

### `runtime/embed.py`

Role:

- wraps runner HTML in a marimo-safe `<iframe srcdoc="...">` helper

### jsPsych v7 runtime contract

The runner targets **jsPsych 7** (CDN). There is **no global `jsPsych*`* object.

- `jspsych_runner_core.js` calls `initJsPsych(...)` and assigns `window.__jsPsychInstance`.
- Eval'd trial callbacks (Python string `on_finish` / `stimulus` functions) must use `window.__jsPsychInstance` for `data`, `pluginAPI`, etc.
- Do not reference bare `jsPsych` in timeline strings (throws `MigrationError`).

Example (motion scoring):

```javascript
function(data) {
  const j = window.__jsPsychInstance;
  data.correct = j.pluginAPI.compareKeys(data.response, data.correct_key);
}
```

Extension pattern for new tasks:

1. Add renderer HTML contract (if needed) under `renderers/`
2. Add optional browser stimulus display script under `runtime/stimulus_display/`
3. Add trial builder adapter under `tasks/` (or reuse `to_jspsych_timeline`)
4. Pass `RunnerConfig(plugins=(...), extra_scripts=(...), input_arrow_keys=...)` when building HTML
5. Use `window.__jsPsychInstance` in any eval'd jsPsych trial callbacks

### `analysis/descriptive_stats.py`

Role:

- provides descriptive statistics helpers independent of fitting pipeline
- includes `dprime(...)` with mode-based inputs (`rates` or `counts`)
- includes `standard_error(...)` with mode-based inputs (`values` or `percentages`)
- keeps utility statistics separate from HSSM model-fitting code

## Runtime Flow

### Browser demo (participant-like)

1. marimo builds a timeline via `build_motion_demo_timeline()` using slider levels A/B/C (two A→C blocks).
2. `build_jspsych_runner_html(timeline, config=motion_demo_runner_config())` inlines HTML/CSS/JS assets.
3. `render_srcdoc_iframe()` embeds the runner; user clicks **Restart demo** to rebuild with fresh random directions.
4. Boot script decodes timeline + config, `JsPsychRunnerCore` binds plugins and runs jsPsych.
5. Motion trials call `__startAllMotionCanvases` on `on_load`; scoring uses `__jsPsychInstance` on `on_finish`.
6. On experiment end, runner posts `{ type: "jspsych-results", rows }` to parent (ingest path not yet wired in app).

### Python simulation + HSSM

1. marimo UI collects task and observer parameters.
2. `JsPsychTrialEngine.make_trials()` creates trials with random left/right and side-strength coding (`evidence_weight=[1,1]`).
3. `NAfcObserver.choose()` builds latent evidence, choice, and RT (explicit lapse path).
4. tabular data is assembled for modeling.
5. user triggers HSSM fit with dedicated run control.
6. summaries and charts are rendered in-app (including model cartoon).

## Extension Guidelines

Use these boundaries when adding new functionality:

- **New task types**: add simulator classes/functions under `tasks/`
- **New stimuli modalities**: add preview/render helpers under `renderers/`
- **New observer/input sources**: add classes under `agents/` and keep choice/RT coupled to the same latent signal model when possible
- **New analysis models**: add model-specific fit/plot helpers under `analysis/`

Prefer data contracts (plain dict/dataframe schemas) between modules over direct cross-calls to keep components interchangeable.

## Data Contracts (Current)

Trial-level fields currently used by the pipeline:

- `stim_level`
- `evidence_weight`
- `stim_strengths`
- `correct_index`
- jsPsych metadata fields (`type`, `choices`, `correct_key`, nested `data`, etc.)

Modeled dataset fields:

- `subj`
- `stim_level`
- `choice_index`
- `response`
- `rt`
- `correct`

Any new task module should document equivalent fields and provide a normalization step if names differ.

## Packaging Notes

The project follows a split-by-concern layout (`tasks/`, `renderers/`, `agents/`, `analysis/`, `schemas/`) with `apps/` housing marimo entrypoints.