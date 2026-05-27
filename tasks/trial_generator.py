from __future__ import annotations

from abc import ABC, abstractmethod

from schemas.contracts import Trial


class TrialGenerator(ABC):
    """Abstract trial sequence: stores trial parameter dicts and retrieves them in order."""

    def __init__(self) -> None:
        self._trial_params: list[dict[str, object]] = []
        self._index = 0

    @property
    def trial_count(self) -> int:
        return len(self._trial_params)

    @property
    def index(self) -> int:
        return self._index

    def reset(self) -> None:
        """Return the internal cursor to the first trial."""
        self._index = 0

    def has_next(self) -> bool:
        return self._index < len(self._trial_params)

    def all_trials(self) -> list[dict[str, object]]:
        """Return all stored trial parameter dicts without advancing the cursor."""
        return list(self._trial_params)

    @abstractmethod
    def next_trial(self) -> dict[str, object]:
        """Return the next trial parameter dict and advance the internal index."""


class FactorTrialGenerator(TrialGenerator):
    """Trial generator backed by an explicit ordered list of trial parameter dicts."""

    def __init__(self, trial_params: list[dict[str, object]] | None = None) -> None:
        super().__init__()
        if trial_params:
            self._trial_params = list(trial_params)

    def add_trial(self, trial: Trial | dict[str, object]) -> None:
        """Append one trial parameter dict to the sequence."""
        self._trial_params.append(dict(trial))

    def next_trial(self) -> dict[str, object]:
        if not self.has_next():
            raise StopIteration("No more trials in generator")
        trial = self._trial_params[self._index]
        self._index += 1
        return trial

    @staticmethod
    def generate_trials(
        *,
        task: str,
        stimulus_params: dict[str, object],
        presentation_duration_ms: int | None,
        correct_index: int,
        choices: list[str],
        correct_key: str,
        data: dict[str, object] | None = None,
    ) -> Trial:
        """Build one trial parameter dict (stimulus side only)."""
        trial_data = dict(data or {})
        trial_data.setdefault("task", task)
        return {
            "task": task,
            "stimulus_params": dict(stimulus_params),
            "presentation_duration_ms": presentation_duration_ms,
            "correct_index": int(correct_index),
            "choices": list(choices),
            "correct_key": correct_key,
            "data": trial_data,
        }
