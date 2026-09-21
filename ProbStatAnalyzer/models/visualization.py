from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import plotly.express as px
from scipy import stats


TEMPLATE = "plotly_white"


def _html(fig: go.Figure) -> str:
    fig.update_layout(template=TEMPLATE, margin=dict(l=35, r=25, t=45, b=35), height=390)
    return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"displaylogo": False, "toImageButtonOptions": {"format": "png"}})


def _best_pdf(series: pd.Series, best: dict) -> tuple[np.ndarray, np.ndarray]:
    x = np.linspace(float(series.min()), float(series.max()), 300)
    dist = getattr(stats, best["name"])
    y = dist.pmf(np.rint(x), *best["params"]) if best["name"] in {"poisson", "binom", "geom"} else dist.pdf(x, *best["params"])
    return x, y


def build_all_charts(series: pd.Series, distribution: dict) -> dict:
    best = distribution["best"]
    x_pdf, y_pdf = _best_pdf(series, best)

    hist = px.histogram(series, nbins=30, labels={"value": "Value"}, title="Histogram", opacity=0.78)
    hist.update_traces(marker_color="#2563eb")

    density = px.histogram(series, nbins=30, histnorm="probability density", labels={"value": "Value"}, title="Histogram with Fitted Density")
    density.add_trace(go.Scatter(x=x_pdf, y=y_pdf, mode="lines", name=best["display_name"], line=dict(color="#ef4444", width=3)))

    box = px.box(series, points="outliers", labels={"value": "Value"}, title="Box Plot")
    violin = px.violin(series, box=True, points="all", labels={"value": "Value"}, title="Violin Plot")

    sorted_values = np.sort(series.to_numpy())
    ecdf_y = np.arange(1, len(sorted_values) + 1) / len(sorted_values)
    ecdf = go.Figure(go.Scatter(x=sorted_values, y=ecdf_y, mode="lines", line=dict(color="#0f766e", width=3)))
    ecdf.update_layout(title="ECDF", xaxis_title="Value", yaxis_title="Empirical Probability")

    cdf_dist = getattr(stats, best["name"])
    cdf_y = cdf_dist.cdf(x_pdf, *best["params"])
    cdf = go.Figure(go.Scatter(x=x_pdf, y=cdf_y, mode="lines", line=dict(color="#7c3aed", width=3)))
    cdf.update_layout(title="Fitted CDF", xaxis_title="Value", yaxis_title="Cumulative Probability")

    qq = go.Figure()
    theoretical, ordered = stats.probplot(series, dist="norm", fit=False)
    qq.add_trace(go.Scatter(x=theoretical, y=ordered, mode="markers", marker=dict(color="#0891b2")))
    qq.update_layout(title="QQ Plot", xaxis_title="Theoretical Quantiles", yaxis_title="Ordered Values")

    pdf = go.Figure(go.Scatter(x=x_pdf, y=y_pdf, mode="lines", fill="tozeroy", line=dict(color="#dc2626", width=3)))
    pdf.update_layout(title="Probability Density / Mass Function", xaxis_title="Value", yaxis_title="Density")

    comparison = go.Figure()
    for item in distribution["candidates"]:
        if item.get("params") and np.isfinite(item.get("ks_statistic", np.inf)):
            dist = getattr(stats, item["name"])
            y = dist.pmf(np.rint(x_pdf), *item["params"]) if item["name"] in {"poisson", "binom", "geom"} else dist.pdf(x_pdf, *item["params"])
            comparison.add_trace(go.Scatter(x=x_pdf, y=y, mode="lines", name=item["display_name"]))
    comparison.update_layout(title="Distribution Comparison", xaxis_title="Value", yaxis_title="Density")

    return {
        "histogram": _html(hist),
        "density": _html(density),
        "box": _html(box),
        "violin": _html(violin),
        "ecdf": _html(ecdf),
        "cdf": _html(cdf),
        "qq": _html(qq),
        "pdf": _html(pdf),
        "comparison": _html(comparison),
    }
