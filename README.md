## Simulator

This project contains a small interactive tutorial written as a `marimo` app.

### Run

From this directory:

```bash
uv run marimo run coherenceSimulator.py
```

Or open it in the editor:

```bash
uv run marimo edit coherenceSimulator.py
```

### Notes

- The tutorial simulates a **binary left/right motion coherence task** for multiple observers and trials using **jsPsych-style** trial objects in Python; motion previews use **Canvas** in the browser (not PsychoPy).
- It then fits a DDM to the simulated data using `hssm`.
