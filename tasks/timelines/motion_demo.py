from __future__ import annotations

from typing import TYPE_CHECKING

from runtime.jspsych_runner import RunnerConfig
from tasks.jspsych_timeline import motion_to_jspsych_timeline

if TYPE_CHECKING:
    from tasks.jspsych_motion import JsPsychTrialEngine

INTRO_TRIAL: dict[str, object] = {
    "type": "html-button-response",
    "stimulus": (
        '<div style="font-size:20px;line-height:1.6;text-align:center;">'
        "Press left arrow for motion to the left, and right arrow for motion to the right"
        "</div>"
    ),
    "choices": ["click here to begin."],
    "button_layout": "grid",
    "grid_rows": 1,
    "grid_columns": 1,
}

FEEDBACK_TRIAL: dict[str, object] = {
    "type": "html-keyboard-response",
    "stimulus": (
        "function(){"
        "const j = window.__jsPsychInstance;"
        "const d = j.data.get().last(1).values()[0] || {};"
        "const ok = !!d.correct;"
        "const txt = ok ? 'Correct' : 'Incorrect';"
        "const color = ok ? '#15803d' : '#dc2626';"
        "return `<div style=\"font-size:30px;font-weight:700;color:${color};text-align:center;\">${txt}</div>`;"
        "}"
    ),
    "choices": "NO_KEYS",
    "trial_duration": 1000,
}

def motion_demo_runner_config(*, title: str = "jsPsych Demo") -> RunnerConfig:
    """Runner settings for the motion coherence iframe demo."""
    return RunnerConfig(
        title=title,
        plugins=("html-keyboard-response", "html-button-response"),
        extra_scripts=("stimulus_display/motion_rdk.js", "demo_results_charts.js"),
        input_arrow_keys=True,
        show_results_charts=True,
        results_task_filter="motion_coherence",
    )


def build_motion_demo_levels(
    level_a: float,
    level_b: float,
    level_c: float,
    *,
    reps_per_level: int = 5,
) -> list[tuple[str, float]]:
    """Expand A/B/C coherence levels with ``reps_per_level`` trials each."""
    levels = [("A", float(level_a)), ("B", float(level_b)), ("C", float(level_c))]
    return [
        (label, level)
        for label, level in levels
        for _ in range(int(reps_per_level))
    ]


def build_motion_demo_timeline(
    engine: "JsPsychTrialEngine",
    demo_levels: list[tuple[str, float]],
) -> list[dict[str, object]]:
    """Build intro -> motion trials (+ feedback) -> summary for the marimo demo."""
    demo_trials = []
    for idx, (label, level) in enumerate(demo_levels, start=1):
        trial = engine.make_trials(stim_level=level, n_trials=1)[0]
        trial["data"]["label"] = label
        trial["data"]["trial_num"] = idx
        demo_trials.append(trial)

    motion_trials = motion_to_jspsych_timeline(demo_trials, trial_duration_ms=None)
    timeline: list[dict[str, object]] = [INTRO_TRIAL]
    for trial in motion_trials:
        timeline.extend([trial, FEEDBACK_TRIAL])
    return timeline
