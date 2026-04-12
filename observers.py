from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class MotionCoherenceObserver:
    """Simulated observer for a left/right motion task.

    The observer makes a noisy internal motion estimate with Gaussian noise
    that depends on stimulus coherence, plus lapses (random responses).
    """

    # "Global" knobs (instance parameters, treated as global across trials)
    sigma0: float = 1.0  # coherence-dependent sensory noise scale
    lapse_rate: float = 0.02  # random-choice lapses
    rng: np.random.Generator | None = None

    def _rng(self) -> np.random.Generator:
        return self.rng if self.rng is not None else np.random.default_rng()

    def sensory_sigma(self, coherence: float) -> float:
        # Higher coherence => lower sensory noise. Add epsilon to avoid div-by-zero.
        c = float(np.clip(coherence, 0.0, 1.0))
        return float(self.sigma0 / (c + 0.05))

    def choose(self, stim_dir: int, coherence: float) -> int:
        """Return response in {-1, +1}."""
        rng = self._rng()

        if rng.random() < self.lapse_rate:
            return int(rng.choice([-1, 1]))

        sigma = self.sensory_sigma(coherence)
        # Internal estimate: sign(stim + noise); stim_dir is -1 or +1.
        est = float(stim_dir) + rng.normal(0.0, sigma)
        return 1 if est >= 0 else -1

    def rt(self, stim_dir: int, coherence: float, ndt: float, rt_scale: float, rt_noise: float) -> float:
        """Heuristic RT: faster when evidence magnitude is larger."""
        rng = self._rng()
        sigma = self.sensory_sigma(coherence)
        # Evidence proxy: |stim + noise|; larger => shorter RT.
        evidence = abs(float(stim_dir) + rng.normal(0.0, sigma))
        base = float(ndt) + float(rt_scale) / (evidence + 1e-3)
        return max(0.05, base + rng.normal(0.0, float(rt_noise)))

