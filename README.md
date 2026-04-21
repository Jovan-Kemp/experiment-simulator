## Simulator

This project contains a small interactive tutorial written as a `marimo` app.

It is organized as a modular workflow that combines:

- a participant-like jsPsych motion-coherence demo (embedded in the app),
- a virtual-observer simulation pipeline for synthetic datasets, and
- an HSSM analysis stage with behavior summaries and plots.

### Run

From this directory:

```bash
uv run marimo run apps/coherence_app.py
```

Or open it in the editor:

```bash
uv run marimo edit apps/coherence_app.py
```

### Notes

- The tutorial simulates a **binary left/right motion task** for multiple observers and trials using **jsPsych-style** trial objects in Python; motion previews use **Canvas** in the browser.
- It then fits a DDM to the simulated data using `hssm`.

### Project docs

- Detailed file/directory responsibilities: `DOCUMENTATION.md`
