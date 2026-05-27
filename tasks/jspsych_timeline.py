from __future__ import annotations

from collections.abc import Callable

from renderers.jspsych_preview import motion_trial_stimulus_html
from schemas.contracts import Trial


def _motion_coherence(tr: Trial) -> float:
    params = tr["stimulus_params"]
    return float(params.get("coherence", params.get("stim_level", 0.0)))


def _motion_param(tr: Trial, key: str, default: object) -> object:
    return tr["stimulus_params"].get(key, default)


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
    tr: Trial,
    trial_index: int,
    *,
    trial_duration_ms: int | None = None,
) -> dict[str, object]:
    """Convert one motion trial contract into a jsPsych html-keyboard-response trial."""
    correct_index = int(tr["correct_index"])
    direction = str(_motion_param(tr, "motion_direction", "right"))
    duration_ms = tr["presentation_duration_ms"]
    if duration_ms is None:
        duration_ms = trial_duration_ms

    stim_html = motion_trial_stimulus_html(
        stim_level=_motion_coherence(tr),
        motion_direction=direction,
        trial_id=f"trial-{trial_index}",
        width=int(_motion_param(tr, "canvas_width", 500)),
        height=int(_motion_param(tr, "canvas_height", 260)),
        n_dots=int(_motion_param(tr, "n_dots", 80)),
        speed_px_s=float(_motion_param(tr, "speed_px_s", 120.0)),
        seed=int(_motion_param(tr, "seed", 42)),
        dot_lifetime_s=float(_motion_param(tr, "dot_lifetime_s", 0.1)),
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
    if duration_ms is not None:
        timeline_trial["trial_duration"] = int(duration_ms)
    return timeline_trial


def to_jspsych_timeline(
    trials: list[Trial],
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
    trials: list[Trial],
    *,
    trial_duration_ms: int | None = None,
) -> list[dict[str, object]]:
    """Motion-coherence adapter for jsPsych timeline export."""

    def _builder(
        tr: Trial,
        trial_index: int,
        *,
        trial_duration_ms: int | None = None,
    ) -> dict[str, object]:
        return build_motion_keyboard_trial(
            tr,
            trial_index,
            trial_duration_ms=trial_duration_ms,
        )

    return to_jspsych_timeline(
        trials,
        _builder,
        trial_duration_ms=trial_duration_ms,
    )
