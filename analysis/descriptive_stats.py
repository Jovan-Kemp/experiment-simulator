from __future__ import annotations

import math
from statistics import NormalDist
from typing import Literal


def _dprime_from_rates(hit_rate: float, false_positive_rate: float, *, eps: float = 1e-6) -> float:
    """Compute d' from hit and false-positive rates."""
    h = min(1.0 - eps, max(eps, float(hit_rate)))
    f = min(1.0 - eps, max(eps, float(false_positive_rate)))
    z = NormalDist().inv_cdf
    return float(z(h) - z(f))


def _dprime_from_counts(
    hits: int,
    false_positives: int,
    n_signal: int,
    n_noise: int,
    *,
    eps: float = 1e-6,
) -> float:
    """Compute d' from counts with log-linear edge correction."""

    hit_rate = (float(hits) + 0.5) / (float(n_signal) + 1.0)
    false_positive_rate = (float(false_positives) + 0.5) / (float(n_noise) + 1.0)
    return _dprime_from_rates(hit_rate, false_positive_rate, eps=eps)


def dprime(
    data: list[float],
    *,
    mode: Literal["rates", "counts"] = "rates",
    eps: float = 1e-6,
) -> float:
    """Compute d' using rates or counts mode.

    Args:
        data:
            - ``mode="rates"`` expects ``[hit_rate, false_positive_rate]``.
            - ``mode="counts"`` expects ``[hits, false_positives, n_signal, n_noise]``.
        mode: Calculation mode for d' input format.
        eps: Clamp used in the rate-based z transform.
    """
    values = [float(x) for x in data]
    if mode == "rates":
        if len(values) != 2:
            raise ValueError("Rates mode expects data=[hit_rate, false_positive_rate].")
        return _dprime_from_rates(values[0], values[1], eps=eps)
    if mode == "counts":
        if len(values) != 4:
            raise ValueError(
                "Counts mode expects data=[hits, false_positives, n_signal, n_noise]."
            )
        return _dprime_from_counts(
            int(values[0]),
            int(values[1]),
            int(values[2]),
            int(values[3]),
            eps=eps,
        )
    raise ValueError("mode must be either 'rates' or 'counts'.")


def _sem_from_values(values: list[float]) -> float:
    if len(values) < 2:
        raise ValueError("At least two values are required to compute standard error.")
    mean = sum(values) / len(values)
    var = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(var) / math.sqrt(len(values))


def _sem_from_percentages(percentages: list[float], sample_sizes: int | list[int] | None = None) -> float:
    if not percentages:
        raise ValueError("percentages must be a non-empty list.")
    for p in percentages:
        if p < 0.0 or p > 100.0:
            raise ValueError("Percentage mode expects values in [0, 100].")

    if sample_sizes is None:
        return _sem_from_values(percentages)

    if isinstance(sample_sizes, int):
        n_list = [int(sample_sizes)] * len(percentages)
    else:
        n_list = [int(n) for n in sample_sizes]

    if len(n_list) != len(percentages):
        raise ValueError("sample_sizes list must match length of percentages.")
    if any(n <= 0 for n in n_list):
        raise ValueError("sample_sizes must contain positive integers.")

    proportions = [p / 100.0 for p in percentages]
    total_n = float(sum(n_list))
    pooled_p = sum(p * n for p, n in zip(proportions, n_list)) / total_n
    pooled_se = math.sqrt(pooled_p * (1.0 - pooled_p) / total_n)
    return pooled_se * 100.0


def standard_error(
    data: list[float],
    *,
    mode: Literal["values", "percentages"] = "values",
    sample_sizes: int | list[int] | None = None,
) -> float:
    """Compute standard error using value or percentage mode.

    Args:
        data: List of values or percentages.
        mode:
            - ``"values"``: standard SEM on raw values.
            - ``"percentages"``: percentage-specific handling.
        sample_sizes:
            - Optional only for ``mode="percentages"``.
            - If provided, uses pooled binomial SE:
              SE = sqrt(p * (1-p) / N) * 100
            - Can be one int (same N for each percentage) or a list matching data length.
            - If omitted, computes SEM across percentage observations.
    """
    values = [float(x) for x in data]
    if not values:
        raise ValueError("data must be a non-empty list.")

    if mode == "values":
        return _sem_from_values(values)

    if mode != "percentages":
        raise ValueError("mode must be either 'values' or 'percentages'.")

    return _sem_from_percentages(values, sample_sizes=sample_sizes)

