from __future__ import annotations

from schemas.contracts import ExperimentParams, Trial
from schemas.trial_generator import TrialGenerator


class ExperimentGenerator:
    """Organize one experiment: shared parameters and one or more ``TrialGenerator`` blocks.

    Trial generators build and iterate trial parameter dicts. This class holds experiment-level
    defaults (display size, data writeout path) and walks attached generators in order.
    """

    def __init__(self, experiment_params: ExperimentParams | None = None) -> None:
        self._experiment_params: ExperimentParams = dict(experiment_params or {})
        self._trial_generators: list[TrialGenerator] = []
        self._generator_index = 0

    @property
    def experiment_params(self) -> ExperimentParams:
        return dict(self._experiment_params)

    @property
    def trial_generators(self) -> tuple[TrialGenerator, ...]:
        return tuple(self._trial_generators)

    @property
    def trial_generator_count(self) -> int:
        return len(self._trial_generators)

    @property
    def current_generator_index(self) -> int:
        return self._generator_index

    def set_experiment_params(self, experiment_params: ExperimentParams) -> None:
        self._experiment_params = dict(experiment_params)

    def add_trial_generator(self, generator: TrialGenerator) -> None:
        """Append a trial generator block (e.g. one coherence level, one condition)."""
        self._trial_generators.append(generator)

    def reset(self) -> None:
        """Reset experiment cursor and every attached trial generator."""
        self._generator_index = 0
        for generator in self._trial_generators:
            generator.reset()

    def has_next_trial(self) -> bool:
        return any(
            g.has_next() for g in self._trial_generators[self._generator_index :]
        )

    def next_trial(self) -> dict[str, object]:
        """Return the next trial from the current generator block, with experiment params applied."""
        while self._generator_index < len(self._trial_generators):
            generator = self._trial_generators[self._generator_index]
            if generator.has_next():
                return self._apply_experiment_params(generator.next_trial())
            self._generator_index += 1
        raise StopIteration("No more trials in experiment")

    def all_trials(self) -> list[dict[str, object]]:
        """Materialize every trial from all generators (does not advance cursors)."""
        return [
            self._apply_experiment_params(trial)
            for generator in self._trial_generators
            for trial in generator.all_trials()
        ]

    def _apply_experiment_params(self, trial: Trial | dict[str, object]) -> dict[str, object]:
        out = dict(trial)
        exp_display = dict(self._experiment_params.get("display_params") or {})
        trial_display = dict(out.get("display_params") or {})
        out["display_params"] = {**exp_display, **trial_display}

        output_path = self._experiment_params.get("data_output_path")
        if output_path:
            data = dict(out.get("data") or {})
            data.setdefault("data_output_path", output_path)
            out["data"] = data
        return out
