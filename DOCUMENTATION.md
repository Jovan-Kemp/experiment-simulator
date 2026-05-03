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
  - `jspsych_motion.py` - jsPsych trial engine and timeline builders
- `renderers/`
  - `jspsych_preview.py` - browser Canvas/iframe stimulus previews
- `agents/`
  - `motion_observer.py` - virtual observer behavior models
- `runtime/`
  - `jspsych_runner.py` - executable jsPsych runner page generator and browser-side trial runtime glue
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

- builds demo timeline via helper composition (intro, motion trials, feedback, summary)
- isolates iframe embedding/runner HTML encoding from demo/simulation logic

### `tasks/jspsych_motion.py`

Role:

- defines task-trial generation in a transportable, JSON-serializable format
- emits and compiles trials for direct jsPsych runtime execution
- keeps sequencing logic independent from UI and analysis

Current behavior:

- emits balanced left/right binary trials for each `stim_level`
- includes `on_finish` scoring logic and `on_load` hook for canvas startup
- supports response-terminated trials (`trial_duration_ms=None`) for participant-paced runs

Why it exists:

- task procedures should be reusable across demo mode, simulation mode, and participant-facing runs
- trial schemas can be reused by front-end runners and backend simulation pipelines

### `agents/motion_observer.py`

Role:

- contains virtual observer classes for synthetic behavioral data
- models response policy, sensory uncertainty behavior, and lapse/random errors
- can be expanded to host multiple observer families (simple heuristics, SSM-consistent agents, etc.)

Current `NAfcObserver` behavior:

- Latent utility defaults to `stim * stim_levels + Gaussian noise`.
- Sensory noise uses `sigma = sigma0 + sigma_scale * c` where `c` is driven by task difficulty (`1 - coherence`, `coherence = max(stim_levels)`).
- Lapse path is explicit: with probability `lapse_rate`, choice is random and RT is generated from lapse RT logic.
- Non-lapse choice for n-AFC uses `argmax(utility)`; 1-stimulus mode uses sign-threshold detection.
- Non-lapse RT uses evidence margin (`abs(chosen - max(other))` for n-AFC) with `rt = ndt + rt_scale / evidence + noise`.
- Optional `signal_model` can override latent utility generation while preserving shared utility for choice and non-lapse RT.

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
- decodes base64 timeline payload and revives function-valued trial fields
- maps string trial types to loaded jsPsych plugin objects
- hosts canvas animation bootstrap used by motion-trial stimuli
- normalizes keyboard behavior for arrow-key task responses and posts results to parent

### `analysis/descriptive_stats.py`

Role:

- provides descriptive statistics helpers independent of fitting pipeline
- includes `dprime(...)` with mode-based inputs (`rates` or `counts`)
- includes `standard_error(...)` with mode-based inputs (`values` or `percentages`)
- keeps utility statistics separate from HSSM model-fitting code

## Runtime Flow

Typical run path for the current demo:

1. marimo app renders a participant-like jsPsych demo timeline (intro -> motion trials + feedback -> summary)
2. marimo UI collects task and fit parameters for simulation mode
3. trial generator creates balanced left/right trial definitions with side-strength coding
4. observer model builds latent utility, then generates choice and RT (with explicit lapse path)
5. tabular data is assembled for modeling
6. user triggers HSSM fit with dedicated run control
7. HSSM fit runs on prepared data
8. summaries and charts are rendered in-app (including model cartoon)

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
- `stim`
- `stim_levels`
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

