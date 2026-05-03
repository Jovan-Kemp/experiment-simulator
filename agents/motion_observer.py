from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable

import numpy as np


SignalModelFn = Callable[["NAfcObserver", np.ndarray, np.ndarray], np.ndarray]


@dataclass(frozen=True)
class NAfcObserver:
    """Virtual n-AFC observer operating on arrays of inputs.

    This observer takes in a stimulus array that represents the stimuli options
    on a single trial. The observer than produces a choice index and a response time.

    Args:
        sigma0: Sensory noise intercept parameter.
        sigma_scale: Sensory noise slope applied to stimulus level.
        lapse_rate: Probability of lapsing to a random choice.
        signal_model: Optional custom latent signal generator.
        rng: Random number generator.
    """

    sigma0: float = 0
    sigma_scale: float = 1.0
    lapse_rate: float = 0.02
    rt_scale: float = 0.35
    rt_noise: float = 0.03
    signal_model: SignalModelFn | None = None
    rng: np.random.Generator | None = None

    def _rng(self) -> np.random.Generator:
        return self.rng if self.rng is not None else np.random.default_rng()

    def sensory_sigma(self, stim_level: float) -> float:
        # Enforce non-negativity only; allow values > 1.
        c = max(0.0, float(stim_level))
        return float(self.sigma0 + self.sigma_scale * c)

    def _default_signal_model(self, stim_arr: np.ndarray, level_arr: np.ndarray) -> np.ndarray:
        """Default latent evidence vector: stim * level + Gaussian noise."""
        rng = self._rng()
        # Base evidence grows with stim*level; noise scales with difficulty
        # (lower coherence -> higher noise).
        coherence = float(np.max(level_arr))
        sigma = self.sensory_sigma(1.0 - coherence)
        return stim_arr * level_arr + rng.normal(0.0, sigma, size=len(stim_arr))

    def _signal_model(
        self,
        stim: list[float] | np.ndarray,
        stim_levels: list[float] | np.ndarray,
    ) -> np.ndarray:
        """Shared latent signal model used by both decision and RT paths."""
        stim_arr = np.asarray(stim, dtype=float)
        level_arr = np.asarray(stim_levels, dtype=float)
        if stim_arr.shape != level_arr.shape:
            raise ValueError("stim and stim_levels must have the same shape")
        if stim_arr.ndim != 1 or len(stim_arr) == 0:
            raise ValueError("stim and stim_levels must be non-empty 1D arrays")

        if self.signal_model is None:
            return self._default_signal_model(stim_arr, level_arr)
        return self.signal_model(self, stim_arr, level_arr)

    def _decision_process(
        self,
        stim: list[float] | np.ndarray,
        stim_levels: list[float] | np.ndarray,
    ) -> tuple[int, np.ndarray, bool]:
        """Return choice, latent utility, and lapse flag.

        Pure lapse behavior:
        - choice is random
        - RT is not derived from evidence (handled downstream)
        """
        rng = self._rng()
        utility = self._signal_model(stim=stim, stim_levels=stim_levels)

        if rng.random() < self.lapse_rate:
            return int(rng.integers(0, len(utility))), utility, True

        # 1-stimulus detection special-case: return 0=absent, 1=present.
        if len(utility) == 1:
            return int(utility[0] > 0.0), utility, False
        return int(np.argmax(utility)), utility, False

    def _reaction_time(self, utility: np.ndarray, choice_index: int, ndt: float) -> float:
        """Compute evidence-driven RT from utility margin."""
        rng = self._rng()
        if len(utility) == 1:
            margin = abs(float(utility[0]))
        else:
            chosen = float(utility[int(choice_index)])
            others = np.delete(utility, int(choice_index))
            margin = chosen - (float(np.max(others)) if len(others) else 0.0)
        evidence = abs(margin)
        base = float(ndt) + float(self.rt_scale) / evidence
        return base + rng.normal(0.0, float(self.rt_noise))

    def _lapse_reaction_time(self, ndt: float) -> float:
        """Pure-lapse RT: independent from utility/evidence."""
        rng = self._rng()
        # Lapse RT centers around ndt + rt_scale with additive jitter.
        base = float(ndt) + float(self.rt_scale)
        return max(0.05, base + rng.normal(0.0, float(self.rt_noise)))

    def choose(
        self,
        stim: list[float] | np.ndarray,
        stim_levels: list[float] | np.ndarray,
        ndt: float,
    ) -> tuple[int, float]:
        """Choose alternative index and return response time.

        Args:
            stim: Stimulus array.
            stim_levels: Stimulus levels array, aligned with `stim`.
            ndt: Non-decision time for RT construction.

        Returns:
            Tuple of ``(choice_index, rt)``.
        """
        # Decision and RT share the same utility model unless trial lapses.
        choice_index, utility, is_lapse = self._decision_process(stim=stim, stim_levels=stim_levels)
        if is_lapse:
            rt = self._lapse_reaction_time(ndt=ndt)
        else:
            rt = self._reaction_time(utility=utility, choice_index=choice_index, ndt=ndt)
        return choice_index, rt

