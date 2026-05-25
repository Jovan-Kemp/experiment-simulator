from __future__ import annotations

import json
from collections.abc import Iterator

import numpy as np

from schemas.contracts import JsPsychTrial
from tasks.jspsych_timeline import motion_to_jspsych_timeline


class JsPsychTrialEngine:
    """Build and execute jsPsych-native motion-coherence trial objects."""

    def __init__(self, rng: np.random.Generator | None = None):
        self.rng = rng if rng is not None else np.random.default_rng()

    def make_trials(self, stim_level: float, n_trials: int) -> list[JsPsychTrial]:
        n = int(n_trials)
        # Independent random left/right on each trial (unbiased over many trials).
        dirs = self.rng.choice([-1, 1], size=n)

        level = float(stim_level)
        trials: list[JsPsychTrial] = []
        for d in dirs:
            stim_dir = int(d)
            # Binary discrimination special-case (n=2 alternatives):
            # index 0 -> left option, index 1 -> right option.
            # Per-alternative evidence multiplier; all ones => no directional bias.
            evidence_weight = [1.0, 1.0]
            # Encode side-specific strength in stim_strengths so argmax maps cleanly.
            stim_strengths = [level, 0.0] if stim_dir == -1 else [0.0, level]
            correct_index = 0 if stim_dir == -1 else 1
            correct_key = "ArrowLeft" if correct_index == 0 else "ArrowRight"
            motion = "left" if correct_index == 0 else "right"
            trials.append(
                {
                    "type": "motion-coherence",
                    "stim_level": level,
                    "evidence_weight": evidence_weight,
                    "stim_strengths": stim_strengths,
                    "correct_index": correct_index,
                    "choices": ["ArrowLeft", "ArrowRight"],
                    "correct_key": correct_key,
                    "data": {
                        "stim_level": level,
                        "motion_direction": motion,
                        "correct_response": correct_key,
                        "task": "motion_coherence",
                    },
                }
            )
        return trials

    def iter_trials(self, trials: list[JsPsychTrial]) -> Iterator[JsPsychTrial]:
        for t in trials:
            yield t

    def trials_to_jspsych_json(self, trials: list[JsPsychTrial]) -> str:
        return json.dumps(trials, indent=2)

    def to_jspsych_timeline(
        self,
        trials: list[JsPsychTrial],
        *,
        trial_duration_ms: int | None = None,
    ) -> list[dict[str, object]]:
        """Convert internal motion trials to executable jsPsych timeline trials."""
        return motion_to_jspsych_timeline(trials, trial_duration_ms=trial_duration_ms)
