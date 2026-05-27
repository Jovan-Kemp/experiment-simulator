from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Callable

import numpy as np


EvidenceModelFn = Callable[["NAfcObserver", np.ndarray, np.ndarray], np.ndarray]
StimulusToStrengthsFn = Callable[[dict[str, object]], list[float]]


@dataclass(frozen=True)
class NAfcObserver:
    """Virtual n-AFC observer operating on experiment ``stimulus_factors``.

    Derives latent ``stim_strengths`` from ``stimulus_factors`` via
    ``stimulus_to_strengths``. ``evidence_weight`` is an observer-side
    per-alternative multiplier (all ones = no directional bias).

    Args:
        sigma0: Sensory noise intercept parameter.
        sigma_scale: Sensory noise slope applied to stimulus level.
        lapse_rate: Probability of lapsing to a random choice.
        evidence_weight: Per-alternative multipliers applied to latent strengths.
        stimulus_to_strengths: Maps experiment params to latent strength vector.
        evidence_model: Optional custom latent evidence generator.
        rng: Random number generator.
    """

    sigma0: float = 0
    sigma_scale: float = 1.0
    lapse_rate: float = 0.02
    rt_scale: float = 0.35
    rt_noise: float = 0.03
    evidence_weight: tuple[float, ...] | None = None
    stimulus_to_strengths: StimulusToStrengthsFn | None = None
    evidence_model: EvidenceModelFn | None = None
    rng: np.random.Generator | None = field(default=None, compare=False)

    def _rng(self) -> np.random.Generator:
        return self.rng if self.rng is not None else np.random.default_rng()

    def latent_strengths(self, stimulus_factors: dict[str, object]) -> list[float]:
        """Derive per-alternative latent strengths from experiment parameters."""
        if self.stimulus_to_strengths is None:
            raise ValueError(
                "stimulus_to_strengths must be set to derive latent strengths"
            )
        return list(self.stimulus_to_strengths(stimulus_factors))

    def _resolve_evidence_weight(self, n_alternatives: int) -> np.ndarray:
        if self.evidence_weight is None:
            return np.ones(n_alternatives, dtype=float)
        weight = np.asarray(self.evidence_weight, dtype=float)
        if weight.shape != (n_alternatives,):
            raise ValueError(
                "evidence_weight length must match number of alternatives"
            )
        return weight

    def sensory_sigma(self, stim_level: float) -> float:
        c = max(0.0, float(stim_level))
        return float(self.sigma0 + self.sigma_scale * c)

    def _default_evidence_model(
        self, weight_arr: np.ndarray, strength_arr: np.ndarray
    ) -> np.ndarray:
        """Default latent evidence vector: evidence_weight * strength + Gaussian noise."""
        rng = self._rng()
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
        """Return choice, latent evidence, and lapse flag."""
        rng = self._rng()
        evidence = self._evidence_model(
            evidence_weight=evidence_weight, stim_strengths=stim_strengths
        )

        if rng.random() < self.lapse_rate:
            return int(rng.integers(0, len(evidence))), evidence, True

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
        base = float(ndt) + float(self.rt_scale)
        return max(0.05, base + rng.normal(0.0, float(self.rt_noise)))

    def _choice_and_rt(
        self,
        evidence_weight: list[float] | np.ndarray,
        stim_strengths: list[float] | np.ndarray,
        ndt: float,
    ) -> tuple[int, float]:
        choice_index, evidence, is_lapse = self._decision_process(
            evidence_weight=evidence_weight, stim_strengths=stim_strengths
        )
        if is_lapse:
            return choice_index, self._lapse_reaction_time(ndt=ndt)
        return choice_index, self._reaction_time(
            evidence=evidence, choice_index=choice_index, ndt=ndt
        )

    def choose(
        self,
        stimulus_factors: dict[str, object],
        ndt: float,
    ) -> tuple[int, float]:
        """Choose alternative index and return response time from experiment params."""
        stim_strengths = self.latent_strengths(stimulus_factors)
        weight = self._resolve_evidence_weight(len(stim_strengths))
        return self._choice_and_rt(weight, stim_strengths, ndt)

    def choose_from_latent(
        self,
        evidence_weight: list[float] | np.ndarray,
        stim_strengths: list[float] | np.ndarray,
        ndt: float,
    ) -> tuple[int, float]:
        """Choose directly from precomputed latent arrays (advanced / testing)."""
        return self._choice_and_rt(evidence_weight, stim_strengths, ndt)
