from __future__ import annotations

import json
from typing import Any, Iterator

import numpy as np


class JsPsychStyleTrialSimulator:
    """Trial generator using jsPsych-equivalent trial shapes (no PsychoPy).

    Produces trial dicts suitable for exporting to a jsPsych timeline and for
    iterating in Python simulators. Field layout mirrors common jsPsych ``data``
    conventions plus task-specific ``stim_dir`` for the simulator.
    """

    def __init__(self, rng: np.random.Generator | None = None):
        self.rng = rng if rng is not None else np.random.default_rng()

    def make_trials(self, coherence: float, n_trials: int) -> list[dict[str, Any]]:
        # Balanced left/right motion direction (maps to keyboard / button response in jsPsych).
        n = int(n_trials)
        half = n // 2
        dirs = [-1] * half + [1] * (n - half)
        self.rng.shuffle(dirs)
        trials: list[dict[str, Any]] = []
        coh = float(coherence)
        for d in dirs:
            stim_dir = int(d)
            motion = "left" if stim_dir == -1 else "right"
            trials.append(
                {
                    "type": "motion-coherence",  # custom plugin name in real jsPsych
                    "coherence": coh,
                    "stim_dir": stim_dir,
                    "choices": ["ArrowLeft", "ArrowRight"],
                    "correct_key": "ArrowLeft" if stim_dir == -1 else "ArrowRight",
                    "data": {
                        "coherence": coh,
                        "motion_direction": motion,
                        "correct_response": "ArrowLeft" if stim_dir == -1 else "ArrowRight",
                        "task": "motion_coherence",
                    },
                }
            )
        return trials

    def iter_trials(self, trials: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
        """Sequential trial iteration (replaces PsychoPy TrialHandler loop)."""
        for t in trials:
            yield t

    def trials_to_jspsych_json(self, trials: list[dict[str, Any]]) -> str:
        """Serialize trials for pasting into a jsPsych ``timeline`` (JSON array)."""
        return json.dumps(trials, indent=2)
