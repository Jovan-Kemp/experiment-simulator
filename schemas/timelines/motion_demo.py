from __future__ import annotations

from collections.abc import Callable

from runtime.jspsych_runner import RunnerConfig
from schemas.experimentGenerator import ExperimentGenerator
from schemas.jspsych_timeline import motion_to_jspsych_timeline
from schemas.trial_generator import FactorTrialGenerator

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

COUNTDOWN_SECONDS = 3

COUNTDOWN_TRIALS: list[dict[str, object]] = [
    {
        "type": "html-keyboard-response",
        "stimulus": (
            f'<div style="font-size:72px;font-weight:700;text-align:center;">{n}</div>'
        ),
        "choices": "NO_KEYS",
        "trial_duration": 1000,
        "data": {"task": "countdown"},
    }
    for n in range(COUNTDOWN_SECONDS, 0, -1)
]

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
    demo_levels: list[tuple[str, float]],
    *,
    display_params: dict[str, object],
    make_motion_coherence_trials: Callable[..., FactorTrialGenerator],
    presentation_duration_ms: int | None = None,
) -> list[dict[str, object]]:
    """Build intro -> countdown -> motion trials (+ feedback) for the marimo demo."""
    experiment = ExperimentGenerator(
        experiment_params={"display_params": dict(display_params)},
    )
    for idx, (label, level) in enumerate(demo_levels, start=1):
        block = make_motion_coherence_trials(
            n_trials=1,
            coherence=level,
            presentation_duration_ms=presentation_duration_ms,
        )
        trial = block.all_trials()[0]
        trial["data"]["label"] = label
        trial["data"]["trial_num"] = idx
        single_trial = FactorTrialGenerator([trial])
        experiment.add_trial_generator(single_trial)

    motion_trials = motion_to_jspsych_timeline(experiment.all_trials())  # type: ignore[arg-type]
    timeline: list[dict[str, object]] = [INTRO_TRIAL, *COUNTDOWN_TRIALS]
    for trial in motion_trials:
        timeline.extend([trial, FEEDBACK_TRIAL])
    return timeline
