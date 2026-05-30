# Motion RDK ``AFCStimulusPlugin`` for the constant-stimuli n-AFC timeline.
# Registers ``motion_rdk`` and wires trial factors / display params to ``motion_coherence_stimulus``.
# Imported for side effect by ``coherence_timeline`` so the plugin is available by name.

from __future__ import annotations

from schemas.timelines.constant_stimuli_afc_timeline import (
    AFCStimulusPlugin,
    register_stimulus_plugin,
)
from schemas.contracts import Trial
from renderers.motion_coherence.motion_coherence_stimulus import motion_trial_stimulus_html

MOTION_RDK_ON_LOAD = (
    "function(){"
    "if (window.__startAllMotionCanvases) { window.__startAllMotionCanvases(); }"
    "}"
)


def _coherence_level(trial: Trial) -> float:
    factors = trial["stimulus_factors"]
    return float(factors.get("coherence", factors.get("stim_level", 0.0)))


def _display_param(trial: Trial, key: str, default: object) -> object:
    return trial["display_params"].get(key, default)


def render_motion_rdk_stimulus(trial: Trial, trial_index: int) -> str:
    direction = str(
        trial["stimulus_factors"].get(
            "motion_direction",
            trial["data"].get("motion_direction", "right"),
        )
    )
    return motion_trial_stimulus_html(
        stim_level=_coherence_level(trial),
        motion_direction=direction,
        trial_id=f"trial-{trial_index}",
        width=int(_display_param(trial, "canvas_width", 500)),
        height=int(_display_param(trial, "canvas_height", 260)),
        n_dots=int(_display_param(trial, "n_dots", 80)),
        speed_px_s=float(_display_param(trial, "speed_px_s", 120.0)),
        seed=int(_display_param(trial, "seed", 42)),
        dot_lifetime_s=float(_display_param(trial, "dot_lifetime_s", 0.1)),
    )


MOTION_RDK_STIMULUS_PLUGIN = AFCStimulusPlugin(
    name="motion_rdk",
    render_stimulus=render_motion_rdk_stimulus,
    on_load=MOTION_RDK_ON_LOAD,
)

register_stimulus_plugin(MOTION_RDK_STIMULUS_PLUGIN)
