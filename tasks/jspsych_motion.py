from __future__ import annotations

import json
from collections.abc import Iterator

import numpy as np

from renderers.jspsych_preview import motion_trial_stimulus_html
from schemas.contracts import JsPsychTrial


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
            # Use equal base stimulus weights and encode side-specific strength
            # in stim_levels so argmax maps cleanly to the correct side.
            stim = [1.0, 1.0]
            stim_levels = [level, 0.0] if stim_dir == -1 else [0.0, level]
            correct_index = 0 if stim_dir == -1 else 1
            correct_key = "ArrowLeft" if correct_index == 0 else "ArrowRight"
            motion = "left" if correct_index == 0 else "right"
            trials.append(
                {
                    "type": "motion-coherence",
                    "stim_level": level,
                    "stim": stim,
                    "stim_levels": stim_levels,
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
        """Convert internal trial objects to executable jsPsych timeline trials."""
        timeline: list[dict[str, object]] = []
        for i, tr in enumerate(trials):
            timeline.append(self._build_jspsych_timeline_trial(tr, i, trial_duration_ms=trial_duration_ms))
        return timeline

    def _build_jspsych_timeline_trial(
        self,
        tr: JsPsychTrial,
        trial_index: int,
        *,
        trial_duration_ms: int | None,
    ) -> dict[str, object]:
        """Create one jsPsych trial entry from a typed trial contract."""
        correct_index = int(tr["correct_index"])
        direction = "left" if correct_index == 0 else "right"
        stim_html = motion_trial_stimulus_html(
            stim_level=float(tr["stim_level"]),
            motion_direction=direction,
            trial_id=f"trial-{trial_index}",
        )
        timeline_trial: dict[str, object] = {
            "type": "html-keyboard-response",
            "stimulus": stim_html,
            "choices": tr["choices"],
            "response_ends_trial": True,
            "data": {
                **tr["data"],
                "correct_key": tr["correct_key"],
                "correct_index": correct_index,
                "trial_index_py": trial_index,
            },
            "on_finish": (
                "function(data){"
                "if (window.jsPsych && jsPsych.pluginAPI && jsPsych.pluginAPI.compareKeys) {"
                "data.correct = jsPsych.pluginAPI.compareKeys(data.response, data.correct_key);"
                "} else {"
                "data.correct = String(data.response) === String(data.correct_key);"
                "}"
                "}"
            ),
            "on_load": (
                "function(){"
                "if (window.__startAllMotionCanvases) { window.__startAllMotionCanvases(); }"
                "}"
            ),
        }
        if trial_duration_ms is not None:
            timeline_trial["trial_duration"] = int(trial_duration_ms)
        return timeline_trial

