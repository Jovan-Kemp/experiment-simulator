from __future__ import annotations

from typing import Literal, TypedDict


class JsPsychTrialData(TypedDict):
    stim_level: float
    motion_direction: Literal["left", "right"] | str
    correct_response: str
    task: str


class JsPsychTrial(TypedDict):
    type: str
    stim_level: float
    evidence_weight: list[float]
    stim_strengths: list[float]
    correct_index: int
    choices: list[str]
    correct_key: str
    data: JsPsychTrialData


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

