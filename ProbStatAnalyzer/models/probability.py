from __future__ import annotations

import math

from scipy import stats


DISCRETE_NAMES = {"binom", "poisson", "geom"}


def _distribution(best: dict):
    dist = getattr(stats, best["name"])
    return dist, tuple(best["params"])


def _fmt(value: float) -> str:
    if math.isclose(value, round(value), abs_tol=1e-9):
        return str(int(round(value)))
    return f"{value:.4f}".rstrip("0").rstrip(".")


def _probability_symbol(best: dict) -> str:
    return "PMF" if best["name"] in DISCRETE_NAMES else "CDF"


def _point_substitution(best: dict, x_value: float) -> list[dict]:
    name = best["name"]
    params = tuple(best["params"])
    x = int(round(x_value))
    if name == "binom":
        n, p = params
        return [
            {"label": "Formula", "math": r"P(X=x)=\binom{n}{x}p^x(1-p)^{n-x}"},
            {"label": "Substitute", "math": rf"P(X={x})=\binom{{{int(round(n))}}}{{{x}}}({_fmt(p)})^{x}(1-{_fmt(p)})^{{{int(round(n))}-{x}}}"},
        ]
    if name == "poisson":
        lam = params[0]
        return [
            {"label": "Formula", "math": r"P(X=x)=\frac{e^{-\lambda}\lambda^x}{x!}"},
            {"label": "Substitute", "math": rf"P(X={x})=\frac{{e^{{-{_fmt(lam)}}}{_fmt(lam)}^{x}}}{{{x}!}}"},
        ]
    if name == "geom":
        p = params[0]
        return [
            {"label": "Formula", "math": r"P(X=x)=p(1-p)^{x-1}"},
            {"label": "Substitute", "math": rf"P(X={x})={_fmt(p)}({_fmt(1-p)})^{{{x}-1}}"},
        ]
    if name == "uniform":
        a, scale = params
        b = a + scale
        return [
            {"label": "Formula", "math": r"F(x)=\frac{x-a}{b-a}"},
            {"label": "Substitute", "math": rf"F({_fmt(x_value)})=\frac{{{_fmt(x_value)}-{_fmt(a)}}}{{{_fmt(b)}-{_fmt(a)}}}"},
        ]
    if name == "expon":
        lam = 1 / params[1]
        return [
            {"label": "Formula", "math": r"F(x)=1-e^{-\lambda x}"},
            {"label": "Substitute", "math": rf"F({_fmt(x_value)})=1-e^{{-{_fmt(lam)}({_fmt(x_value)})}}"},
        ]
    if name == "norm":
        mu, sigma = params
        z = (x_value - mu) / sigma
        return [
            {"label": "Convert to Z score", "math": rf"z=\frac{{{_fmt(x_value)}-{_fmt(mu)}}}{{{_fmt(sigma)}}}={_fmt(z)}"},
            {"label": "Compute", "math": rf"P(Z\le {_fmt(z)})"},
        ]
    return []


def _steps(best: dict, operation: str, x_value: float, a_value: float | None, b_value: float | None, probability: float) -> list[dict]:
    name = best["name"]
    if operation in {"lte", "gte"}:
        relation = r"\le" if operation == "lte" else r"\ge"
        steps = [{"label": "User Input", "math": rf"x={_fmt(x_value)}"}]
        steps.extend(_point_substitution(best, x_value))
        if name in DISCRETE_NAMES and operation == "lte":
            steps.append({"label": "Cumulative Probability", "math": rf"P(X\le {_fmt(x_value)})=\sum_{{k\le {math.floor(x_value)}}}P(X=k)"})
        if operation == "gte":
            if name in DISCRETE_NAMES:
                steps.append({"label": "Tail Conversion", "math": rf"P(X\ge {_fmt(x_value)})=1-P(X\le {_fmt(math.ceil(x_value)-1)})"})
            else:
                steps.append({"label": "Tail Conversion", "math": rf"P(X\ge {_fmt(x_value)})=1-P(X\le {_fmt(x_value)})"})
        steps.append({"label": "Answer", "math": rf"P(X{relation}{_fmt(x_value)})={probability:.4f}"})
        return steps

    lower, upper = sorted([float(a_value), float(b_value)])
    steps = [
        {"label": "User Input", "math": rf"a={_fmt(lower)},\quad b={_fmt(upper)}"},
        {"label": "Formula", "math": r"P(a<X<b)=F(b)-F(a)"},
    ]
    if name in DISCRETE_NAMES:
        discrete_lower = math.floor(lower)
        discrete_upper = math.ceil(upper) - 1
        steps.append({"label": "Discrete Bounds", "math": rf"P({ _fmt(lower) }<X<{ _fmt(upper) })=P(X\le {discrete_upper})-P(X\le {discrete_lower})"})
    else:
        steps.append({"label": "Substitute", "math": rf"P({_fmt(lower)}<X<{_fmt(upper)})=F({_fmt(upper)})-F({_fmt(lower)})"})
    steps.append({"label": "Answer", "math": rf"P({_fmt(lower)}<X<{_fmt(upper)})={probability:.4f}"})
    return steps


def calculate_probability(best: dict, operation: str, x_value: float, a_value: float | None, b_value: float | None) -> dict:
    dist, params = _distribution(best)
    is_discrete = best["name"] in DISCRETE_NAMES
    if operation == "lte":
        probability = float(dist.cdf(math.floor(x_value) if is_discrete else x_value, *params))
        formula = f"P(X <= {x_value:g})"
        interpretation = f"There is a {probability:.4%} chance that X is at most {x_value:g}."
    elif operation == "gte":
        if is_discrete:
            probability = float(dist.sf(math.ceil(x_value) - 1, *params))
        else:
            probability = float(dist.sf(x_value, *params))
        formula = f"P(X >= {x_value:g})"
        interpretation = f"There is a {probability:.4%} chance that X is at least {x_value:g}."
    elif operation == "between":
        if a_value is None or b_value is None:
            raise ValueError("Both lower and upper bounds are required.")
        lower, upper = sorted([a_value, b_value])
        if is_discrete:
            probability = float(dist.cdf(math.ceil(upper) - 1, *params) - dist.cdf(math.floor(lower), *params))
        else:
            probability = float(dist.cdf(upper, *params) - dist.cdf(lower, *params))
        formula = f"P({lower:g} < X < {upper:g})"
        interpretation = f"There is a {probability:.4%} chance that X lies between {lower:g} and {upper:g}."
    else:
        raise ValueError("Unsupported probability operation.")

    probability = max(0.0, min(1.0, probability))
    steps = _steps(best, operation, x_value, a_value, b_value, probability)
    return {
        "formula": formula,
        "result_math": steps[-1]["math"],
        "result": round(probability, 8),
        "interpretation": interpretation,
        "operation": operation,
        "x_value": x_value,
        "a_value": a_value,
        "b_value": b_value,
        "method": _probability_symbol(best),
        "steps": steps,
    }
