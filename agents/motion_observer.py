from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class NAfcObserver:
    """Virtual n-AFC observer operating on arrays of inputs.

    This observer takes in a stimulus array that represents the stimuli options
    on a single trial. The observer than produces a choice index and a response time.

    Args:
        sigma0: Sensory noise scale parameter.
        lapse_rate: Probability of lapsing to a random choice.
        rng: Random number generator.
    """

    sigma0: float = 1.0
    lapse_rate: float = 0.02
    rng: np.random.Generator | None = None

    def _rng(self) -> np.random.Generator:
        return self.rng if self.rng is not None else np.random.default_rng()

    def sensory_sigma(self, stim_level: float) -> float:
        # Enforce non-negativity only; allow values > 1.
        c = max(0.0, float(stim_level))
        return float(self.sigma0 * c)

    def choose(self, stim: list[float] | np.ndarray, stim_levels: list[float] | np.ndarray) -> int:
        """Choose one alternative index from n candidates.

        Args:
            stim: Stimulus array.
            stim_levels: Stimulus levels array, aligned with `stim`.

        Returns:
            Choice index.
        """
        rng = self._rng()
        if rng.random() < self.lapse_rate:
            return int(rng.integers(0, len(stim_levels)))
        stim_arr = np.asarray(stim, dtype=float)
        level_arr = np.asarray(stim_levels, dtype=float)
        if stim_arr.shape != level_arr.shape:
            raise ValueError("stim and stim_levels must have the same shape")
        if stim_arr.ndim != 1 or len(stim_arr) == 0:
            raise ValueError("stim and stim_levels must be non-empty 1D arrays")

        # 
        sigma = self.sensory_sigma(float(np.max(level_arr)))
        utility = stim_arr * level_arr + rng.normal(0.0, sigma, size=len(stim_arr))
        # 1-level detection special-case: return 0=absent, 1=present.
        if len(utility) == 1:
            return int(utility[0] > 0.0)
        return int(np.argmax(utility))

    def rt(
        self,
        choice_index: int,
        stim: list[float] | np.ndarray,
        stim_levels: list[float] | np.ndarray,
        ndt: float,
        rt_scale: float,
        rt_noise: float,
    ) -> float:
        rng = self._rng()
        stim_arr = np.asarray(stim, dtype=float)
        level_arr = np.asarray(stim_levels, dtype=float)
        sigma = self.sensory_sigma(float(np.max(level_arr)))
        utility = stim_arr * level_arr + rng.normal(0.0, sigma, size=len(stim_arr))
        if len(utility) == 1:
            margin = abs(float(utility[0]))
        else:
            chosen = float(utility[int(choice_index)])
            others = np.delete(utility, int(choice_index))
            margin = chosen - (float(np.max(others)) if len(others) else 0.0)
        evidence = abs(margin) + 1e-3
        base = float(ndt) + float(rt_scale) / evidence
        return max(0.05, base + rng.normal(0.0, float(rt_noise)))

