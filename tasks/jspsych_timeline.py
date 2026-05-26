from __future__ import annotations

from collections.abc import Callable

from renderers.jspsych_preview import motion_trial_stimulus_html
from schemas.contracts import JsPsychTrial

REVIVE_KEYS = ("on_finish", "on_start", "on_load", "stimulus")

MOTION_SCORING_ON_FINISH = (
    "function(data){"
    "const j = window.__jsPsychInstance;"
    "if (j && j.pluginAPI && j.pluginAPI.compareKeys) {"
    "data.correct = j.pluginAPI.compareKeys(data.response, data.correct_key);"
    "} else {"
    "data.correct = String(data.response) === String(data.correct_key);"
    "}"
    "}"
)

MOTION_CANVAS_ON_LOAD = (
    "function(){"
    "if (window.__startAllMotionCanvases) { window.__startAllMotionCanvases(); }"
    "}"
)


def build_motion_keyboard_trial(
    tr: JsPsychTrial,
    trial_index: int,
    *,
    trial_duration_ms: int | None = None,
    canvas_width: int = 500,
    canvas_height: int = 260,
    n_dots: int = 80,
    speed_px_s: float = 120.0,
    seed: int = 42,
) -> dict[str, object]:
    """Convert one motion trial contract into a jsPsych html-keyboard-response trial."""
    correct_index = int(tr["correct_index"])
    direction = "left" if correct_index == 0 else "right"
    stim_html = motion_trial_stimulus_html(
        stim_level=float(tr["stim_level"]),
        motion_direction=direction,
        trial_id=f"trial-{trial_index}",
        width=canvas_width,
        height=canvas_height,
        n_dots=n_dots,
        speed_px_s=speed_px_s,
        seed=seed,
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
        "on_finish": MOTION_SCORING_ON_FINISH,
        "on_load": MOTION_CANVAS_ON_LOAD,
    }
    if trial_duration_ms is not None:
        timeline_trial["trial_duration"] = int(trial_duration_ms)
    return timeline_trial


def to_jspsych_timeline(
    trials: list[JsPsychTrial],
    trial_builder: Callable[..., dict[str, object]],
    *,
    trial_duration_ms: int | None = None,
) -> list[dict[str, object]]:
    """Map internal trial contracts to executable jsPsych timeline entries."""
    timeline: list[dict[str, object]] = []
    for i, tr in enumerate(trials):
        timeline.append(
            trial_builder(tr, i, trial_duration_ms=trial_duration_ms)
        )
    return timeline


def motion_to_jspsych_timeline(
    trials: list[JsPsychTrial],
    *,
    trial_duration_ms: int | None = None,
    canvas_width: int = 500,
    canvas_height: int = 260,
    n_dots: int = 80,
    speed_px_s: float = 120.0,
    seed: int = 42,
) -> list[dict[str, object]]:
    """Motion-coherence adapter for jsPsych timeline export."""

    def _builder(
        tr: JsPsychTrial,
        trial_index: int,
        *,
        trial_duration_ms: int | None = None,
    ) -> dict[str, object]:
        return build_motion_keyboard_trial(
            tr,
            trial_index,
            trial_duration_ms=trial_duration_ms,
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            n_dots=n_dots,
            speed_px_s=speed_px_s,
            seed=seed,
        )

    return to_jspsych_timeline(
        trials,
        _builder,
        trial_duration_ms=trial_duration_ms,
    )
