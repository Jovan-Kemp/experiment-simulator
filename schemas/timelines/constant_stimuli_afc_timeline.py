# Generic jsPsych timeline builder for factorized n-AFC constant-stimulus tasks.
# Maps ``Trial`` contracts to ``html-keyboard-response`` entries via pluggable ``AFCStimulusPlugin``s.
# Task-specific rendering lives in experiment plugins; scoring and trial shape are handled here.

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from schemas.contracts import Trial

StimulusRenderer = Callable[[Trial, int], str]

DEFAULT_AFC_SCORING_ON_FINISH = (
    "function(data){"
    "const j = window.__jsPsychInstance;"
    "if (j && j.pluginAPI && j.pluginAPI.compareKeys) {"
    "data.correct = j.pluginAPI.compareKeys(data.response, data.correct_key);"
    "} else {"
    "data.correct = String(data.response) === String(data.correct_key);"
    "}"
    "}"
)

_PLUGINS: dict[str, AFCStimulusPlugin] = {}


@dataclass(frozen=True)
class AFCStimulusPlugin:
    """Pluggable constant stimulus presentation for factorized n-AFC keyboard trials."""

    name: str
    render_stimulus: StimulusRenderer
    on_load: str | None = None
    on_finish: str | None = field(default=None)


def register_stimulus_plugin(plugin: AFCStimulusPlugin) -> None:
    """Register a named stimulus plugin for use by name in timeline builders."""
    _PLUGINS[plugin.name] = plugin


def get_stimulus_plugin(name: str) -> AFCStimulusPlugin:
    if name not in _PLUGINS:
        known = ", ".join(sorted(_PLUGINS)) or "(none)"
        raise KeyError(f"Unknown AFC stimulus plugin {name!r}. Registered: {known}")
    return _PLUGINS[name]


def resolve_stimulus_plugin(plugin: AFCStimulusPlugin | str) -> AFCStimulusPlugin:
    if isinstance(plugin, str):
        return get_stimulus_plugin(plugin)
    return plugin


def build_afc_keyboard_trial(
    tr: Trial,
    trial_index: int,
    *,
    plugin: AFCStimulusPlugin,
    trial_duration_ms: int | None = None,
) -> dict[str, object]:
    """Convert one factorized n-AFC trial into a jsPsych html-keyboard-response trial."""
    duration_ms = tr["presentation_duration_ms"]
    if duration_ms is None:
        duration_ms = trial_duration_ms

    timeline_trial: dict[str, object] = {
        "type": "html-keyboard-response",
        "stimulus": plugin.render_stimulus(tr, trial_index),
        "choices": list(tr["choices"]),
        "response_ends_trial": True,
        "data": {
            **dict(tr["data"]),
            "correct_key": tr["correct_key"],
            "correct_index": int(tr["correct_index"]),
            "trial_index_py": trial_index,
            "stimulus_plugin": plugin.name,
        },
        "on_finish": plugin.on_finish or DEFAULT_AFC_SCORING_ON_FINISH,
    }
    if plugin.on_load is not None:
        timeline_trial["on_load"] = plugin.on_load
    if duration_ms is not None:
        timeline_trial["trial_duration"] = int(duration_ms)
    return timeline_trial


def map_trials_to_jspsych_timeline(
    trials: list[Trial],
    trial_builder: Callable[..., dict[str, object]],
    *,
    trial_duration_ms: int | None = None,
) -> list[dict[str, object]]:
    """Map trial contracts to executable jsPsych timeline entries via ``trial_builder``."""
    timeline: list[dict[str, object]] = []
    for index, trial in enumerate(trials):
        timeline.append(
            trial_builder(trial, index, trial_duration_ms=trial_duration_ms)
        )
    return timeline


def constant_stimuli_afc_timeline(
    trials: list[Trial],
    *,
    stimulus_plugin: AFCStimulusPlugin | str,
    trial_duration_ms: int | None = None,
) -> list[dict[str, object]]:
    """Build a jsPsych timeline for factorized n-AFC trials with constant per-trial stimuli."""
    plugin = resolve_stimulus_plugin(stimulus_plugin)

    def _builder(
        trial: Trial,
        trial_index: int,
        *,
        trial_duration_ms: int | None = None,
    ) -> dict[str, object]:
        return build_afc_keyboard_trial(
            trial,
            trial_index,
            plugin=plugin,
            trial_duration_ms=trial_duration_ms,
        )

    return map_trials_to_jspsych_timeline(
        trials,
        _builder,
        trial_duration_ms=trial_duration_ms,
    )
