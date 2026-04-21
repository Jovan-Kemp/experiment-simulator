# Notes

## Linux

### PsychoPy / wxPython build failures on Linux Mint (GTK detection)

Symptoms:

- `uv add psychopy` tries to build `wxpython==4.2.5`
- configure errors like "GTK+ development files were not found"
- long native compile followed by failure

What helped:

- Install GTK3 and build dependencies:
  - `build-essential`
  - `pkg-config`
  - `libgtk-3-dev`
  - `libglib2.0-dev`
  - `libcairo2-dev`
  - `libpango1.0-dev`
  - `libx11-dev`, `libxext-dev`, `libxrandr-dev`, `libxinerama-dev`, `libxcursor-dev`, `libxi-dev`
  - `libsm-dev`, `libxtst-dev`
  - image deps such as `libpng-dev`, `libjpeg-dev`, `libtiff-dev`
- Verify GTK visibility with:
  - `pkg-config --modversion gtk+-3.0`

Notes:

- On newer Ubuntu/Mint derivatives, `libwebkit2gtk-4.0-dev` may be unavailable; `libwebkit2gtk-4.1-dev` is often the available package.
- Mixed toolchains (Conda compiler + system GTK/pkg-config) can cause configure/link issues.

### Python/toolchain compatibility for large GUI stacks

Symptoms:

- Install attempts fall back to source builds for GUI dependencies (slow/fragile).

What helped:

- Use a Python version with better wheel availability for dependencies (e.g., 3.12 in this project context).
- Prefer clean, non-mixed environments when compiling native deps.

### Missing runtime dependency for marimo plotting

Symptoms:

- `ModuleNotFoundError: altair is required to use mo.ui.altair_chart`

What helped:

- Add `altair` to project dependencies and sync lock/env.

### Marimo launch target mismatch after app relocation

Symptoms:

- `uv run marimo run coherenceSimulator.py` fails because file is removed or not a valid marimo app

What helped:

- Launch the active app entrypoint:
  - `uv run marimo run apps/coherence_app.py`
  - `uv run marimo edit apps/coherence_app.py`

### jsPsych assets blocked or unresolved in iframe runner

Symptoms:

- jsPsych demo iframe is blank
- browser console shows:
  - `initJsPsych is not defined`
  - `jsPsychModule is not defined`
  - script/css load failures from CDN
  - MIME/nosniff issues for some CDN URLs

What helped:

- Use browser builds explicitly in the runner:
  - `https://cdn.jsdelivr.net/npm/jspsych@7.3.4/dist/index.browser.js`
  - `https://cdn.jsdelivr.net/npm/@jspsych/plugin-html-keyboard-response@1.1.3/dist/index.browser.js`
  - `https://cdn.jsdelivr.net/npm/@jspsych/plugin-html-button-response@1.1.3/dist/index.browser.js`
- Keep a visible error message in runner HTML when `initJsPsych` is unavailable.

### Python f-string / embedded JavaScript syntax conflicts

Symptoms:

- marimo cell import fails with Python `SyntaxError` pointing at JavaScript lines in `runtime/jspsych_runner.py`.

What helped:

- Avoid large JavaScript blobs inside Python f-strings.
- Use a plain triple-quoted template and inject dynamic values with placeholder replacement.

### jsPsych dynamic hooks and key handling issues

Symptoms:

- motion canvas not animating during trials
- right/left key correctness not matching expected response
- arrow keys scroll page/iframe or behave inconsistently before clicking

What helped:

- Revive function-valued trial hooks (`on_finish`, `on_start`, `on_load`, `stimulus`) in runner timeline decoding.
- Start animation from `on_load` through a shared runner helper (`window.__startAllMotionCanvases`).
- Compare keys via `jsPsych.pluginAPI.compareKeys(...)` instead of raw string equality.
- Arm keyboard input on pointer interaction with the runner and prevent default arrow-key scrolling.

