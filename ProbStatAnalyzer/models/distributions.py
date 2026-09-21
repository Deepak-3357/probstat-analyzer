from __future__ import annotations

import math
from typing import Callable

import numpy as np
import pandas as pd
from scipy import stats


DISCRETE_NAMES = {"binom", "poisson", "geom"}
SUPPORTED_DISTRIBUTIONS = {
    "binom": {
        "display_name": "Binomial Distribution",
        "type": "Discrete Distribution",
        "formula_title": "PMF",
        "formula": r"P(X=x)=\binom{n}{x}p^x(1-p)^{n-x}",
        "formula_text": "P(X=x) = C(n,x) p^x (1-p)^(n-x)",
        "mean_formula": r"np",
        "mean_formula_text": "n p",
        "variance_formula": r"np(1-p)",
        "variance_formula_text": "n p (1-p)",
        "mgf": r"M_X(t)=((1-p)+pe^t)^n",
        "mgf_text": "M_X(t) = ((1-p) + p e^t)^n",
        "model_sentence": "The Binomial Distribution models the number of successes in a fixed number of independent trials.",
    },
    "poisson": {
        "display_name": "Poisson Distribution",
        "type": "Discrete Distribution",
        "formula_title": "PMF",
        "formula": r"P(X=x)=\frac{e^{-\lambda}\lambda^x}{x!}",
        "formula_text": "P(X=x) = exp(-lambda) lambda^x / x!",
        "mean_formula": r"\lambda",
        "mean_formula_text": "lambda",
        "variance_formula": r"\lambda",
        "variance_formula_text": "lambda",
        "mgf": r"M_X(t)=\exp(\lambda(e^t-1))",
        "mgf_text": "M_X(t) = exp(lambda(e^t - 1))",
        "model_sentence": "The Poisson Distribution models the count of events occurring in a fixed interval.",
    },
    "geom": {
        "display_name": "Geometric Distribution",
        "type": "Discrete Distribution",
        "formula_title": "PMF",
        "formula": r"P(X=x)=p(1-p)^{x-1}",
        "formula_text": "P(X=x) = p(1-p)^(x-1)",
        "mean_formula": r"\frac{1}{p}",
        "mean_formula_text": "1 / p",
        "variance_formula": r"\frac{1-p}{p^2}",
        "variance_formula_text": "(1-p) / p^2",
        "mgf": r"M_X(t)=\frac{pe^t}{1-(1-p)e^t}",
        "mgf_text": "M_X(t) = p e^t / (1 - (1-p)e^t)",
        "model_sentence": "The Geometric Distribution models the number of trials until the first success.",
    },
    "uniform": {
        "display_name": "Uniform Distribution",
        "type": "Continuous Distribution",
        "formula_title": "PDF",
        "formula": r"f(x)=\frac{1}{b-a},\quad a\le x\le b",
        "formula_text": "f(x) = 1 / (b-a), for a <= x <= b",
        "mean_formula": r"\frac{a+b}{2}",
        "mean_formula_text": "(a+b) / 2",
        "variance_formula": r"\frac{(b-a)^2}{12}",
        "variance_formula_text": "(b-a)^2 / 12",
        "mgf": r"M_X(t)=\frac{e^{tb}-e^{ta}}{t(b-a)}",
        "mgf_text": "M_X(t) = (e^(tb) - e^(ta)) / (t(b-a))",
        "model_sentence": "The Uniform Distribution models measurements that are equally likely across a fixed interval.",
    },
    "expon": {
        "display_name": "Exponential Distribution",
        "type": "Continuous Distribution",
        "formula_title": "PDF",
        "formula": r"f(x)=\lambda e^{-\lambda x},\quad x\ge0",
        "formula_text": "f(x) = lambda e^(-lambda x), for x >= 0",
        "mean_formula": r"\frac{1}{\lambda}",
        "mean_formula_text": "1 / lambda",
        "variance_formula": r"\frac{1}{\lambda^2}",
        "variance_formula_text": "1 / lambda^2",
        "mgf": r"M_X(t)=\frac{\lambda}{\lambda-t}",
        "mgf_text": "M_X(t) = lambda / (lambda - t)",
        "model_sentence": "The Exponential Distribution models waiting time until the next event.",
    },
    "norm": {
        "display_name": "Normal Distribution",
        "type": "Continuous Distribution",
        "formula_title": "PDF",
        "formula": r"f(x)=\frac{1}{\sigma\sqrt{2\pi}}e^{-\frac{(x-\mu)^2}{2\sigma^2}}",
        "formula_text": "f(x) = 1 / (sigma sqrt(2 pi)) exp(-((x - mu)^2) / (2 sigma^2))",
        "mean_formula": r"\mu",
        "mean_formula_text": "mu",
        "variance_formula": r"\sigma^2",
        "variance_formula_text": "sigma^2",
        "mgf": r"M_X(t)=\exp(\mu t+\frac{\sigma^2t^2}{2})",
        "mgf_text": "M_X(t) = exp(mu t + sigma^2 t^2 / 2)",
        "model_sentence": "The Normal Distribution models continuous measurements clustered symmetrically around a mean.",
    },
}


def _aic_bic(log_likelihood: float, params_count: int, n: int) -> tuple[float, float]:
    aic = 2 * params_count - 2 * log_likelihood
    bic = params_count * math.log(max(n, 1)) - 2 * log_likelihood
    return aic, bic


def _is_integer_data(data: np.ndarray) -> bool:
    return bool(np.allclose(data, np.rint(data), atol=1e-6))


def _dataset_profile(data: np.ndarray) -> dict:
    integer_data = _is_integer_data(data)
    non_negative = bool(np.min(data) >= 0)
    decimal_count = int(np.sum(~np.isclose(data, np.rint(data), atol=1e-6)))
    if integer_data and non_negative:
        return {
            "type": "Discrete Dataset",
            "family": "discrete",
            "reason": "All observations are integer-valued, non-negative, and count-like.",
            "integer_values": True,
            "non_negative": True,
            "decimal_count": decimal_count,
        }
    return {
        "type": "Continuous Dataset",
        "family": "continuous",
        "reason": "Decimal-valued measurements were detected, so the column is treated as measured continuous data.",
        "integer_values": integer_data,
        "non_negative": non_negative,
        "decimal_count": decimal_count,
    }


def _candidate_not_suitable(name: str, message: str) -> dict:
    meta = SUPPORTED_DISTRIBUTIONS[name]
    return {
        "name": name,
        "display_name": meta["display_name"],
        "type": meta["type"],
        "family": "discrete" if name in DISCRETE_NAMES else "continuous",
        "supported": True,
        "selected": False,
        "rank": None,
        "status": "Not Suitable",
        "reason": message,
        "error": message,
        "ks_statistic": float("inf"),
        "aic": float("inf"),
        "bic": float("inf"),
        "log_likelihood": float("-inf"),
        "params": [],
        "parameters": [],
        "p_value": 0.0,
    }


def _format_number(value: float) -> str:
    if math.isclose(value, round(value), abs_tol=1e-9):
        return str(int(round(value)))
    return f"{value:.4f}".rstrip("0").rstrip(".")


def _parameter_entries(name: str, params: tuple[float, ...]) -> list[dict]:
    if name == "binom":
        n, p = params
        return [{"symbol": "n", "value": int(round(n))}, {"symbol": "p", "value": round(float(p), 6)}]
    if name == "poisson":
        return [{"symbol": r"\lambda", "value": round(float(params[0]), 6)}]
    if name == "geom":
        return [{"symbol": "p", "value": round(float(params[0]), 6)}]
    if name == "uniform":
        a, scale = params
        b = a + scale
        return [{"symbol": "a", "value": round(float(a), 6)}, {"symbol": "b", "value": round(float(b), 6)}]
    if name == "expon":
        scale = float(params[1])
        return [{"symbol": r"\lambda", "value": round(1 / scale, 6)}]
    if name == "norm":
        mu, sigma = params
        return [{"symbol": r"\mu", "value": round(float(mu), 6)}, {"symbol": r"\sigma", "value": round(float(sigma), 6)}]
    return []


def _mean_variance_estimates(name: str, params: tuple[float, ...]) -> tuple[str, str]:
    if name == "binom":
        n, p = params
        mean = n * p
        variance = n * p * (1 - p)
        return f"{_format_number(n)}({_format_number(p)}) = {_format_number(mean)}", f"{_format_number(n)}({_format_number(p)})(1-{_format_number(p)}) = {_format_number(variance)}"
    if name == "poisson":
        lam = params[0]
        return rf"\lambda = {_format_number(lam)}", rf"\lambda = {_format_number(lam)}"
    if name == "geom":
        p = params[0]
        return rf"\frac{{1}}{{{_format_number(p)}}} = {_format_number(1 / p)}", rf"\frac{{1-{_format_number(p)}}}{{{_format_number(p)}^2}} = {_format_number((1 - p) / (p * p))}"
    if name == "uniform":
        a, scale = params
        b = a + scale
        return rf"\frac{{{_format_number(a)}+{_format_number(b)}}}{{2}} = {_format_number((a + b) / 2)}", rf"\frac{{({_format_number(b)}-{_format_number(a)})^2}}{{12}} = {_format_number(((b - a) ** 2) / 12)}"
    if name == "expon":
        lam = 1 / params[1]
        return rf"\frac{{1}}{{{_format_number(lam)}}} = {_format_number(1 / lam)}", rf"\frac{{1}}{{{_format_number(lam)}^2}} = {_format_number(1 / (lam * lam))}"
    if name == "norm":
        mu, sigma = params
        return rf"\mu = {_format_number(mu)}", rf"\sigma^2 = {_format_number(sigma)}^2 = {_format_number(sigma * sigma)}"
    return "-", "-"


def _mgf_substitution(name: str, params: tuple[float, ...]) -> str:
    if name == "binom":
        n, p = params
        return rf"M_X(t)=((1-{_format_number(p)})+{_format_number(p)}e^t)^{{{_format_number(n)}}}"
    if name == "poisson":
        return rf"M_X(t)=\exp({_format_number(params[0])}(e^t-1))"
    if name == "geom":
        p = params[0]
        return rf"M_X(t)=\frac{{{_format_number(p)}e^t}}{{1-{_format_number(1-p)}e^t}}"
    if name == "uniform":
        a, scale = params
        b = a + scale
        return rf"M_X(t)=\frac{{e^{{{_format_number(b)}t}}-e^{{{_format_number(a)}t}}}}{{t({_format_number(b)}-{_format_number(a)})}}"
    if name == "expon":
        lam = 1 / params[1]
        return rf"M_X(t)=\frac{{{_format_number(lam)}}}{{{_format_number(lam)}-t}}"
    if name == "norm":
        mu, sigma = params
        return rf"M_X(t)=\exp({_format_number(mu)}t+\frac{{{_format_number(sigma * sigma)}t^2}}{{2}})"
    return "-"


def _safe_continuous_fit(name: str, data: np.ndarray, fitter: Callable[[np.ndarray], tuple[float, ...]]) -> dict:
    try:
        params = fitter(data)
        scipy_dist = getattr(stats, name)
        ks_stat, p_value = stats.kstest(data, name, args=params)
        pdf_values = np.maximum(scipy_dist.pdf(data, *params), 1e-300)
        log_likelihood = float(np.sum(np.log(pdf_values)))
        aic, bic = _aic_bic(log_likelihood, len(params), len(data))
        meta = SUPPORTED_DISTRIBUTIONS[name]
        return {
            "name": name,
            "display_name": meta["display_name"],
            "type": meta["type"],
            "family": "discrete" if name in DISCRETE_NAMES else "continuous",
            "supported": True,
            "selected": False,
            "rank": None,
            "status": "Successfully Fitted",
            "reason": "The distribution assumptions are compatible with the detected dataset type.",
            "error": None,
            "params": [float(x) for x in params],
            "parameters": _parameter_entries(name, params),
            "ks_statistic": float(ks_stat),
            "p_value": float(p_value),
            "log_likelihood": log_likelihood,
            "aic": float(aic),
            "bic": float(bic),
        }
    except Exception as exc:
        return _candidate_not_suitable(name, str(exc))


def _discrete_ks_statistic(data: np.ndarray, dist, params: tuple[float, ...]) -> float:
    """Return the two-sided KS distance for stepwise discrete CDFs.

    scipy.stats.kstest evaluates a continuous CDF at every individual sample
    observation.  For discrete distributions that compares a model's jump at
    a value with the empirical CDF immediately *before* its repeated samples,
    which inflates the statistic by the PMF at that value.  Compare the left
    and right limits of both step functions at each observed integer instead.
    """
    values, counts = np.unique(data, return_counts=True)
    empirical_right = np.cumsum(counts) / len(data)
    empirical_left = empirical_right - counts / len(data)
    model_right = dist.cdf(values, *params)
    model_left = dist.cdf(values - 1, *params)
    return float(max(
        np.max(np.abs(empirical_right - model_right)),
        np.max(np.abs(empirical_left - model_left)),
    ))


def _fit_discrete(name: str, data: np.ndarray, params: tuple[float, ...]) -> dict:
    rounded = np.rint(data).astype(int)
    dist = getattr(stats, name)
    pmf_values = np.maximum(dist.pmf(rounded, *params), 1e-300)
    log_likelihood = float(np.sum(np.log(pmf_values)))
    ks_stat = _discrete_ks_statistic(rounded, dist, params)
    _, p_value = stats.kstest(rounded, name, args=params)
    aic, bic = _aic_bic(log_likelihood, len(params), len(rounded))
    meta = SUPPORTED_DISTRIBUTIONS[name]
    return {
        "name": name,
        "display_name": meta["display_name"],
        "type": meta["type"],
        "family": "discrete",
        "supported": True,
        "selected": False,
        "rank": None,
        "status": "Successfully Fitted",
        "reason": "The data satisfies the integer count-data assumptions for this discrete model.",
        "error": None,
        "params": [float(x) for x in params],
        "parameters": _parameter_entries(name, params),
        "ks_statistic": float(ks_stat),
        "p_value": float(p_value),
        "log_likelihood": log_likelihood,
        "aic": float(aic),
        "bic": float(bic),
    }


def _normal_fit(data: np.ndarray) -> tuple[float, float]:
    sigma = max(float(np.std(data, ddof=1)), 1e-9)
    return float(np.mean(data)), sigma


def _exponential_fit(data: np.ndarray) -> tuple[float, float]:
    if np.min(data) < 0 or np.mean(data) <= 0:
        raise ValueError("Requires non-negative data with a positive mean.")
    return 0.0, float(np.mean(data))


def _uniform_fit(data: np.ndarray) -> tuple[float, float]:
    a = float(np.min(data))
    b = float(np.max(data))
    return a, max(b - a, 1e-9)


def _poisson_params(data: np.ndarray) -> tuple[float]:
    return (max(float(np.mean(data)), 1e-9),)


def _binomial_params(data: np.ndarray) -> tuple[int, float]:
    rounded = np.rint(data)
    n = max(int(np.nanmax(rounded)), 1)
    p = min(max(float(np.mean(rounded) / n), 1e-9), 1 - 1e-9)
    return n, p


def _geometric_params(data: np.ndarray) -> tuple[float]:
    return (min(max(1 / float(np.mean(data)), 1e-9), 1 - 1e-9),)


def _distribution_explanation(best: dict, data: np.ndarray, dataset_type: dict) -> dict:
    name = best["name"]
    params = tuple(best["params"])
    meta = SUPPORTED_DISTRIBUTIONS[name]
    mean_estimate, variance_estimate = _mean_variance_estimates(name, params)
    symmetric_note = "The data is approximately symmetric around the mean." if name == "norm" else meta["model_sentence"]
    interpretation = [
        dataset_type["reason"],
        f"Hence it is identified as a {dataset_type['type'].lower()}.",
        f"The {meta['display_name']} provides the best fit among the mathematically suitable {meta['type'].lower()} candidates.",
        symmetric_note,
        f"The parameters were estimated from the selected dataset and then used in the {meta['formula_title']} and CDF calculations.",
    ]
    if name == "geom":
        p = params[0]
        interpretation.append(f"The estimated success probability is {_format_number(p)}.")
        interpretation.append(f"The expected number of trials until the first success is {_format_number(1 / p)}.")
    elif name == "norm":
        interpretation.append("About 68% of observations are expected within one standard deviation when the normal model is appropriate.")

    return {
        "distribution_type": meta["type"],
        "detected_dataset_type": dataset_type["type"],
        "detected_dataset_reason": dataset_type["reason"],
        "best_distribution": meta["display_name"],
        "selection_reason": "This distribution produced the lowest KS statistic among the mathematically suitable supported distributions.",
        "parameters": best["parameters"],
        "formula_title": meta["formula_title"],
        "formula": meta["formula"],
        "formula_text": meta["formula_text"],
        "mean_formula": meta["mean_formula"],
        "mean_formula_text": meta["mean_formula_text"],
        "mean_estimate": mean_estimate,
        "variance_formula": meta["variance_formula"],
        "variance_formula_text": meta["variance_formula_text"],
        "variance_estimate": variance_estimate,
        "mgf": meta["mgf"],
        "mgf_text": meta["mgf_text"],
        "mgf_estimate": _mgf_substitution(name, params),
        "interpretation": interpretation,
    }


def fit_distributions(series: pd.Series) -> dict:
    data = series.dropna().astype(float).to_numpy()
    dataset_type = _dataset_profile(data)
    dataset_family = dataset_type["family"]

    continuous_candidates = [
        _safe_continuous_fit("uniform", data, _uniform_fit),
        _safe_continuous_fit("expon", data, _exponential_fit),
        _safe_continuous_fit("norm", data, _normal_fit),
    ]

    integer_data = dataset_type["integer_values"]
    non_negative = dataset_type["non_negative"]
    positive = bool(np.min(data) >= 1)
    if integer_data and non_negative:
        discrete_candidates = [
            _fit_discrete("binom", data, _binomial_params(data)),
            _fit_discrete("poisson", data, _poisson_params(data)),
            _fit_discrete("geom", data, _geometric_params(data)) if positive else _candidate_not_suitable(
                "geom",
                "Geometric Distribution models the number of trials until the first success. The uploaded data contains zero values, so it does not satisfy the positive trial-count assumption.",
            ),
        ]
    else:
        decimal_reason = "The uploaded data contains decimal values. " if dataset_type["decimal_count"] else ""
        discrete_candidates = [
            _candidate_not_suitable("binom", f"{decimal_reason}Binomial Distribution requires integer observations with a fixed number of trials."),
            _candidate_not_suitable("poisson", f"{decimal_reason}Poisson Distribution requires non-negative integer count data."),
            _candidate_not_suitable("geom", f"{decimal_reason}Geometric Distribution models the number of trials until the first success. The uploaded data does not satisfy this assumption."),
        ]

    candidates = discrete_candidates + continuous_candidates

    for item in candidates:
        if item["family"] != dataset_family and math.isfinite(item["ks_statistic"]):
            item["rank"] = None
            item["selection_eligible"] = False
            item["reason"] = (
                "This distribution was fitted for educational comparison, but it is not eligible for best-fit selection because "
                f"the detected dataset type is {dataset_type['type'].lower()}."
            )
        else:
            item["selection_eligible"] = item["status"] == "Successfully Fitted"

    valid = [
        item for item in candidates
        if item.get("selection_eligible") and math.isfinite(item["ks_statistic"])
    ]
    valid_sorted = sorted(valid, key=lambda item: (item["ks_statistic"], item["aic"], item["bic"]))
    for rank, item in enumerate(valid_sorted, start=1):
        item["rank"] = rank

    best = valid_sorted[0] if valid_sorted else candidates[0]
    for item in candidates:
        item["selected"] = item["name"] == best["name"]
        if item["selected"]:
            item["status"] = "Selected"
            item["reason"] = "Best overall fit among the mathematically suitable distributions."

    confidence = max(0.0, min(100.0, (1.0 - best["ks_statistic"]) * 100.0))
    best["confidence_score"] = round(confidence, 2)
    reason = f"{best['display_name']} fits best because it has the minimum KS statistic among suitable {dataset_family} candidate fits."
    unsuitable_family = "discrete" if dataset_family == "continuous" else "continuous"
    if dataset_family == "continuous":
        summary = (
            "The uploaded dataset contains decimal-valued continuous measurements. "
            "Therefore the discrete probability distributions (Binomial, Poisson and Geometric) are mathematically unsuitable for best-fit selection. "
            f"Among the continuous distributions, the {best['display_name']} produced the lowest KS statistic and was selected as the best fitting model."
        )
    else:
        summary = (
            "The uploaded dataset contains non-negative integer count data. "
            "Therefore discrete probability distributions are the mathematically appropriate family for best-fit selection, while continuous models are shown only for educational comparison. "
            f"Among the discrete distributions, the {best['display_name']} produced the best goodness-of-fit."
        )

    return {
        "best": best,
        "candidates": candidates,
        "reason": reason,
        "dataset_type": dataset_type,
        "analysis_summary": summary,
        "comparison_family": dataset_family,
        "excluded_family": unsuitable_family,
        "explanation": _distribution_explanation(best, data, dataset_type),
    }
