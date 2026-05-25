from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable

import numpy as np


EvidenceModelFn = Callable[["NAfcObserver", np.ndarray, np.ndarray], np.ndarray]


@dataclass(frozen=True)
class NAfcObserver:
    """Virtual n-AFC observer operating on arrays of inputs.

    This observer takes per-alternative ``evidence_weight`` and ``stim_strengths``
    on each trial and produces a choice index and a response time.

    Args:
        sigma0: Sensory noise intercept parameter.
        sigma_scale: Sensory noise slope applied to stimulus level.
        lapse_rate: Probability of lapsing to a random choice.
        evidence_model: Optional custom latent evidence generator.
        rng: Random number generator.
    """

    sigma0: float = 0
    sigma_scale: float = 1.0
    lapse_rate: float = 0.02
    rt_scale: float = 0.35
    rt_noise: float = 0.03
    evidence_model: EvidenceModelFn | None = None
    rng: np.random.Generator | None = None

    def _rng(self) -> np.random.Generator:
        return self.rng if self.rng is not None else np.random.default_rng()

    def sensory_sigma(self, stim_level: float) -> float:
        # Enforce non-negativity only; allow values > 1.
        c = max(0.0, float(stim_level))
        return float(self.sigma0 + self.sigma_scale * c)

    def _default_evidence_model(
        self, weight_arr: np.ndarray, strength_arr: np.ndarray
    ) -> np.ndarray:
        """Default latent evidence vector: evidence_weight * strength + Gaussian noise."""
        rng = self._rng()
        # Base evidence grows with weight*strength; noise scales with difficulty
        # (lower coherence -> higher noise).
        coherence = float(np.max(strength_arr))
        sigma = self.sensory_sigma(1.0 - coherence)
        return weight_arr * strength_arr + rng.normal(0.0, sigma, size=len(weight_arr))

    def _evidence_model(
        self,
        evidence_weight: list[float] | np.ndarray,
        stim_strengths: list[float] | np.ndarray,
    ) -> np.ndarray:
        """Shared latent evidence model used by both decision and RT paths."""
        weight_arr = np.asarray(evidence_weight, dtype=float)
        strength_arr = np.asarray(stim_strengths, dtype=float)
        if weight_arr.shape != strength_arr.shape:
            raise ValueError("evidence_weight and stim_strengths must have the same shape")
        if weight_arr.ndim != 1 or len(weight_arr) == 0:
            raise ValueError("evidence_weight and stim_strengths must be non-empty 1D arrays")

        if self.evidence_model is None:
            return self._default_evidence_model(weight_arr, strength_arr)
        return self.evidence_model(self, weight_arr, strength_arr)

    def _decision_process(
        self,
        evidence_weight: list[float] | np.ndarray,
        stim_strengths: list[float] | np.ndarray,
    ) -> tuple[int, np.ndarray, bool]:
        """Return choice, latent evidence, and lapse flag.

        Pure lapse behavior:
        - choice is random
        - RT is not derived from evidence (handled downstream)
        """
        rng = self._rng()
        evidence = self._evidence_model(
            evidence_weight=evidence_weight, stim_strengths=stim_strengths
        )

        if rng.random() < self.lapse_rate:
            return int(rng.integers(0, len(evidence))), evidence, True

        # 1-stimulus detection special-case: return 0=absent, 1=present.
        if len(evidence) == 1:
            return int(evidence[0] > 0.0), evidence, False
        return int(np.argmax(evidence)), evidence, False

    def _reaction_time(self, evidence: np.ndarray, choice_index: int, ndt: float) -> float:
        """Compute evidence-driven RT from evidence margin."""
        rng = self._rng()
        if len(evidence) == 1:
            margin = abs(float(evidence[0]))
        else:
            chosen = float(evidence[int(choice_index)])
            others = np.delete(evidence, int(choice_index))
            margin = chosen - (float(np.max(others)) if len(others) else 0.0)
        margin_abs = abs(margin)
        base = float(ndt) + float(self.rt_scale) / margin_abs
        return base + rng.normal(0.0, float(self.rt_noise))

    def _lapse_reaction_time(self, ndt: float) -> float:
        """Pure-lapse RT: independent from evidence."""
        rng = self._rng()
        # Lapse RT centers around ndt + rt_scale with additive jitter.
        base = float(ndt) + float(self.rt_scale)
        return max(0.05, base + rng.normal(0.0, float(self.rt_noise)))

    def choose(
        self,
        evidence_weight: list[float] | np.ndarray,
        stim_strengths: list[float] | np.ndarray,
        ndt: float,
    ) -> tuple[int, float]:
        """Choose alternative index and return response time.

        Args:
            evidence_weight: Per-alternative multiplier before noise; all ones
                means no bias toward either direction.
            stim_strengths: Per-alternative strength array, aligned with
                ``evidence_weight``.
            ndt: Non-decision time for RT construction.

        Returns:
            Tuple of ``(choice_index, rt)``.
        """
        # Decision and RT share the same evidence model unless trial lapses.
        choice_index, evidence, is_lapse = self._decision_process(
            evidence_weight=evidence_weight, stim_strengths=stim_strengths
        )
        if is_lapse:
            rt = self._lapse_reaction_time(ndt=ndt)
        else:
            rt = self._reaction_time(evidence=evidence, choice_index=choice_index, ndt=ndt)
        return choice_index, rt
