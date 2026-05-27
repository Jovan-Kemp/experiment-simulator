from __future__ import annotations

from typing import TypedDict


class Trial(TypedDict):
    """Task-agnostic trial contract for human and simulated runs.

    ``stimulus_params`` holds experiment / presentation parameters only.
    Latent ``stim_strengths`` for the observer are derived inside the observer
    from ``stimulus_params``, not stored on the trial.
    ``presentation_duration_ms`` is ``None`` for unlimited (response-terminated).
    """

    task: str
    stimulus_params: dict[str, object]
    presentation_duration_ms: int | None
    correct_index: int
    choices: list[str]
    correct_key: str
    data: dict[str, object]


# Backward-compatible alias used by jsPsych adapters.
JsPsychTrial = Trial


class SimulatedObservation(TypedDict):
    subj: int
    stim_level: float
    choice_index: int
    response: int  # binary mapping for current DDM pipeline
    rt: float
    correct: int


class JsPsychResultsMessage(TypedDict):
    type: str
    rows: list[dict[str, object]]
