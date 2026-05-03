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


