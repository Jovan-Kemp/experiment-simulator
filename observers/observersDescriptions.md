# Agent descriptions

Plain-language notes for virtual observers under `observers/`. Each section includes a flowchart aligned with the implementation.

---

## `NAfcObserver` (`heuristic_observer.py`)

Virtual n-AFC observer: one trial in, `(choice_index, rt)` out. Choice uses noisy latent evidence; non-lapse RT scales with coherence.

### Overview

- **Inputs per trial:** `stimulus_factors`, `ndt`
- **`stimulus_to_strengths`** maps experiment params to latent `stim_strengths` inside the observer
- **`evidence_weight`** (observer parameter; all ones = no bias) multiplies latent strengths before noise
- **Output:** `(choice_index, rt)`
- Optional **`evidence_model`** hook replaces default latent evidence generation

### Flowchart

Default path (`evidence_model` is `None`). Matches `choose()` → `_trial()` in `heuristic_observer.py`.

```mermaid
flowchart TD
    subgraph EV["Evidence · _default_evidence_model"]
        direction TB
        E1["coherence = max(stim_strengths)"]
        E2["σ = sigma0 + sigma_scale × max(0, 1 − coherence)"]
        E3["evidence = weight × strength + Normal(0, σ)"]
        E1 --> E2 --> E3
    end

    E3 --> LAP{"random() < lapse_rate?<br/>_trial"}

    LAP -->|yes| D1["choice_index = integers(0, n)"]
    LAP -->|no| D2["n=1: choice_index = int(evidence[0] > 0)<br/>n>1: choice_index = argmax(evidence)"]

    subgraph RTL["Lapse · _trial"]
        direction TB
        RL1["rt = max(0.05, ndt + rt_scale + Normal(0, rt_noise))"]
    end

    subgraph RTN["Non-lapse · _trial"]
        direction TB
        RN1["rt = ndt + rt_scale × (1 − coherence) + Normal(0, rt_noise)"]
    end

    D1 --> RL1
    D2 --> RN1
    RL1 --> OUT["(choice_index, rt)"]
    RN1 --> OUT
```

### Sensory noise

- `sigma = sigma0 + sigma_scale * c` where `c = max(0, stim_level)`
- In the default evidence model, difficulty uses `c = 1 - coherence` with `coherence = max(stim_strengths)`
- Lower coherence → larger sensory noise

### Evidence (latent signal)

- Default per alternative `i`:
  - `evidence[i] = evidence_weight[i] * stim_strengths[i] + Normal(0, sigma)`
- Custom: `evidence_model(observer, weight_arr, strength_arr)`

### Decision rule

1. Lapse check: if `random() < lapse_rate` → random `choice_index`
2. Else if **1-stimulus:** present/absent from `evidence[0] > 0`
3. Else **n-AFC:** `choice_index = argmax(evidence)`

### Reaction time (non-lapse)

- `coherence = max(stim_strengths)` (motion demo: proportion coherent)
- `rt = ndt + rt_scale × (1 − coherence) + Normal(0, rt_noise)` — lower coherence → longer RT

### Reaction time (lapse)

- Independent of evidence: `rt = max(0.05, ndt + rt_scale + Normal(0, rt_noise))`

### Notes

- Non-lapse RT depends on coherence only, not post-choice evidence
- Lapse RT has a lower floor of 0.05 s
