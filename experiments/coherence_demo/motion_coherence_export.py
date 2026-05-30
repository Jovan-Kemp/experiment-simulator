# Motion-coherence task adapter: jsPsych export rows → simulate / HSSM-compatible DataFrame.

from __future__ import annotations

from typing import Any

import pandas as pd

from runtime.jspsych_export import jspsych_rows_to_dataframe

MOTION_COHERENCE_TASK = "motion_coherence"

FIT_DF_COLUMNS = ["subj", "stim_level", "choice_index", "response", "rt", "correct"]


def is_motion_coherence_row(row: dict[str, Any]) -> bool:
    task = str(row.get("task", ""))
    if task == MOTION_COHERENCE_TASK:
        return True
    if task and task not in ("html-keyboard-response", "html-button-response"):
        return False
    return row.get("stim_level") is not None or row.get("coherence") is not None


def _choice_index_from_response(response: object) -> int:
    key = str(response).strip().lower()
    if key in ("arrowleft", "left", "0"):
        return 0
    if key in ("arrowright", "right", "1"):
        return 1
    raise ValueError(f"unrecognized response key: {response!r}")


def _rt_seconds(rt: object) -> float:
    value = float(rt)
    if value > 20.0:
        value = value / 1000.0
    return value


def motion_row_to_trial_record(
    row: dict[str, Any],
    *,
    subj: int = 0,
) -> dict[str, object]:
    """Map one flattened jsPsych row to a simulate()-compatible motion trial record."""
    choice_index = row.get("choice_index")
    if choice_index is None:
        choice_index = _choice_index_from_response(row["response"])

    choice_idx = int(choice_index)
    rt_s = _rt_seconds(row["rt"])

    stim_level = row.get("stim_level")
    if stim_level is None:
        stim_level = row["coherence"]

    correct_val = row.get("correct")
    if correct_val is None:
        correct_val = int(choice_idx == int(row["correct_index"]))

    return {
        "subj": int(subj),
        "stim_level": float(stim_level),
        "choice_index": choice_idx,
        "response": -1 if choice_idx == 0 else 1,
        "rt": rt_s,
        "correct": int(bool(correct_val)),
    }


def motion_trials_dataframe(
    rows: list[dict[str, Any]] | str,
    *,
    subj: int = 0,
) -> pd.DataFrame:
    """Build the coherence-demo analysis table from jsPsych export rows."""
    return jspsych_rows_to_dataframe(
        rows,
        include_row=is_motion_coherence_row,
        row_to_record=lambda flat: motion_row_to_trial_record(flat, subj=subj),
        columns=FIT_DF_COLUMNS,
    )
