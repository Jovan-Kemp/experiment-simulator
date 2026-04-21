from __future__ import annotations

import numpy as np
import pandas as pd


def summarize_behavior(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["stim_level"], as_index=False)
        .agg(acc=("correct", "mean"), rt_mean=("rt", "mean"), rt_med=("rt", "median"), n=("rt", "size"))
        .sort_values("stim_level")
    )


def build_default_hssm_model(df: pd.DataFrame):
    import hssm

    include = [
        {
            "name": "v",
            "formula": "v ~ 1 + stim_level",
            "prior": {
                "Intercept": {"name": "Normal", "mu": 0.0, "sigma": 1.5},
                "stim_level": {"name": "Normal", "mu": 0.0, "sigma": 2.0},
            },
            "link": "identity",
        }
    ]
    return hssm.HSSM(data=df, model="ddm", include=include)


def fit_hssm_model(df: pd.DataFrame, *, draws: int, tune: int, chains: int):
    model = build_default_hssm_model(df)
    idata = model.sample(
        draws=int(draws),
        tune=int(tune),
        chains=int(chains),
        cores=min(4, int(chains)),
        progressbar=True,
    )
    return model, idata


def summarize_posterior(idata):
    import arviz as az

    return az.summary(idata, var_names=["~log_likelihood"], round_to=3)


def summarize_drift_posterior(
    idata,
    stim_levels: list[float] | np.ndarray,
    *,
    prob: float = 0.95,
) -> pd.DataFrame:
    """Summarize posterior drift curve v(stim_level) from fitted coefficients."""
    posterior = idata.posterior
    var_names = list(posterior.data_vars)

    def pick_name(candidates: list[str], *, contains: list[str]) -> str:
        for name in candidates:
            if name in var_names:
                return name
        for name in var_names:
            lname = name.lower()
            if all(tok in lname for tok in contains):
                return name
        raise KeyError(f"Could not find posterior variable matching {contains}. Found: {var_names}")

    intercept_name = pick_name(["v_Intercept", "Intercept"], contains=["v", "intercept"])
    slope_name = pick_name(["v_stim_level", "stim_level"], contains=["v", "stim_level"])

    intercept = posterior[intercept_name].values.reshape(-1)
    slope = posterior[slope_name].values.reshape(-1)

    levels = np.asarray(stim_levels, dtype=float)
    alpha = 1.0 - float(prob)
    lo_q = alpha / 2.0
    hi_q = 1.0 - lo_q

    rows: list[dict[str, float]] = []
    for level in levels:
        drift = intercept + slope * float(level)
        rows.append(
            {
                "stim_level": float(level),
                "v_mean": float(np.mean(drift)),
                "v_median": float(np.median(drift)),
                "v_lo": float(np.quantile(drift, lo_q)),
                "v_hi": float(np.quantile(drift, hi_q)),
            }
        )
    return pd.DataFrame(rows).sort_values("stim_level").reset_index(drop=True)


def summarize_drift_posterior_hssm_api(
    model,
    idata,
    stim_levels: list[float] | np.ndarray,
    *,
    prob: float = 0.95,
) -> pd.DataFrame:
    """Use HSSM/Bambi predict API to summarize posterior drift over stim levels."""
    levels = np.asarray(stim_levels, dtype=float)
    pred_data = pd.DataFrame({"stim_level": levels})
    pred_idata = model.predict(
        idata=idata,
        kind="response_params",
        data=pred_data,
        inplace=False,
        include_group_specific=False,
    )

    pred_vars = list(pred_idata.posterior.data_vars)
    v_name = "v" if "v" in pred_vars else next((name for name in pred_vars if "v" in name.lower()), None)
    if v_name is None:
        raise KeyError(f"Could not find drift parameter in predictive posterior. Found: {pred_vars}")

    v_samples = pred_idata.posterior[v_name].values
    # Expected shape is (chain, draw, observation); flatten first two dims.
    if v_samples.ndim != 3:
        raise ValueError(f"Unexpected drift sample shape for {v_name}: {v_samples.shape}")
    draws_by_obs = v_samples.reshape(-1, v_samples.shape[-1])

    alpha = 1.0 - float(prob)
    lo_q = alpha / 2.0
    hi_q = 1.0 - lo_q

    rows: list[dict[str, float]] = []
    for idx, level in enumerate(levels):
        drift = draws_by_obs[:, idx]
        rows.append(
            {
                "stim_level": float(level),
                "v_mean": float(np.mean(drift)),
                "v_median": float(np.median(drift)),
                "v_lo": float(np.quantile(drift, lo_q)),
                "v_hi": float(np.quantile(drift, hi_q)),
            }
        )
    return pd.DataFrame(rows).sort_values("stim_level").reset_index(drop=True)

