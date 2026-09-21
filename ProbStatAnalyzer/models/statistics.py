from __future__ import annotations

import math

import pandas as pd

from models.preprocessing import CleanedSeries

BASIC_STAT_KEYS = [
    "count",
    "mean",
    "median",
    "mode",
    "variance",
    "standard_deviation",
    "minimum",
    "maximum",
    "range",
]

ADVANCED_STAT_KEYS = [
    "q1",
    "q2",
    "q3",
    "interquartile_range",
    "skewness",
    "kurtosis",
    "coefficient_of_variation",
]

STAT_METADATA = {
    "count": {
        "name": "Count",
        "full_form": "Number of Observations",
        "definition": "The total number of valid observations in the selected dataset column.",
        "formula": r"n",
        "formula_text": "n",
        "usefulness": "It shows the sample size used for all statistical calculations.",
        "icon": "bi-hash",
    },
    "mean": {
        "name": "Mean",
        "full_form": "Arithmetic Mean",
        "definition": "The arithmetic average of all observations in the dataset.",
        "formula": r"\mu=\frac{\sum x}{n}",
        "formula_text": "mu = sum(x) / n",
        "usefulness": "It summarizes the central tendency of the data with one representative value.",
        "icon": "bi-calculator",
    },
    "median": {
        "name": "Median",
        "full_form": "Second Quartile (Median)",
        "definition": "The middle value after all observations are arranged in ascending order.",
        "formula": r"Q_2=50^{th}\text{ Percentile}",
        "formula_text": "Q2 = 50th percentile",
        "usefulness": "It gives a robust center value when the data contains skewness or outliers.",
        "icon": "bi-distribute-vertical",
    },
    "mode": {
        "name": "Mode",
        "full_form": "Mode",
        "definition": "The observation that appears most frequently in the dataset.",
        "formula": r"\operatorname{mode}(X)",
        "formula_text": "mode(X)",
        "usefulness": "It identifies the most common observed value.",
        "icon": "bi-bullseye",
    },
    "variance": {
        "name": "Variance",
        "full_form": "Variance",
        "definition": "Measures how far the data is spread around the mean.",
        "formula": r"\sigma^2=\frac{\sum (x-\mu)^2}{N}",
        "formula_text": "sigma^2 = sum((x - mu)^2) / N",
        "usefulness": "It quantifies the overall spread of the dataset.",
        "icon": "bi-arrows-expand",
    },
    "standard_deviation": {
        "name": "Standard Deviation",
        "full_form": "Standard Deviation",
        "definition": "Measures the average amount of variation in the dataset.",
        "formula": r"\sigma=\sqrt{\text{Variance}}",
        "formula_text": "sigma = sqrt(Variance)",
        "usefulness": "It expresses spread in the same unit as the original data.",
        "icon": "bi-activity",
    },
    "minimum": {
        "name": "Minimum",
        "full_form": "Minimum Value",
        "definition": "The smallest observation in the dataset.",
        "formula": r"\min(X)",
        "formula_text": "min(X)",
        "usefulness": "It identifies the lower boundary of observed values.",
        "icon": "bi-arrow-down",
    },
    "maximum": {
        "name": "Maximum",
        "full_form": "Maximum Value",
        "definition": "The largest observation in the dataset.",
        "formula": r"\max(X)",
        "formula_text": "max(X)",
        "usefulness": "It identifies the upper boundary of observed values.",
        "icon": "bi-arrow-up",
    },
    "range": {
        "name": "Range",
        "full_form": "Range",
        "definition": "The distance between the maximum and minimum observations.",
        "formula": r"\text{Range}=\max(X)-\min(X)",
        "formula_text": "Range = max(X) - min(X)",
        "usefulness": "It gives a quick view of the total span of the data.",
        "icon": "bi-arrows",
    },
    "q1": {
        "name": "Q1",
        "full_form": "First Quartile",
        "definition": "The value below which 25% of observations fall.",
        "formula": r"Q_1=25^{th}\text{ Percentile}",
        "formula_text": "Q1 = 25th percentile",
        "usefulness": "It helps describe the lower portion of the data distribution.",
        "icon": "bi-1-circle",
    },
    "q2": {
        "name": "Q2",
        "full_form": "Second Quartile (Median)",
        "definition": "The value below which 50% of observations fall.",
        "formula": r"Q_2=50^{th}\text{ Percentile}",
        "formula_text": "Q2 = 50th percentile",
        "usefulness": "It marks the midpoint of the ordered dataset.",
        "icon": "bi-2-circle",
    },
    "q3": {
        "name": "Q3",
        "full_form": "Third Quartile",
        "definition": "The value below which 75% of observations fall.",
        "formula": r"Q_3=75^{th}\text{ Percentile}",
        "formula_text": "Q3 = 75th percentile",
        "usefulness": "It helps describe the upper portion of the data distribution.",
        "icon": "bi-3-circle",
    },
    "interquartile_range": {
        "name": "IQR",
        "full_form": "Interquartile Range",
        "definition": "The spread of the middle 50% of observations.",
        "formula": r"\text{IQR}=Q_3-Q_1",
        "formula_text": "IQR = Q3 - Q1",
        "usefulness": "It measures spread while reducing the influence of extreme values.",
        "icon": "bi-arrows-collapse",
    },
    "skewness": {
        "name": "Skewness",
        "full_form": "Skewness",
        "definition": "Measures the asymmetry of the dataset around its mean.",
        "formula": r"\gamma_1=\frac{E[(X-\mu)^3]}{\sigma^3}",
        "formula_text": "gamma1 = E[(X - mu)^3] / sigma^3",
        "usefulness": "It shows whether the distribution leans left, right, or is approximately symmetric.",
        "icon": "bi-slash-lg",
    },
    "kurtosis": {
        "name": "Kurtosis",
        "full_form": "Kurtosis",
        "definition": "Measures the tail weight and peakedness of the dataset.",
        "formula": r"\gamma_2=\frac{E[(X-\mu)^4]}{\sigma^4}",
        "formula_text": "gamma2 = E[(X - mu)^4] / sigma^4",
        "usefulness": "It helps compare the shape of the data with a normal distribution.",
        "icon": "bi-graph-up",
    },
    "coefficient_of_variation": {
        "name": "CV",
        "full_form": "Coefficient of Variation",
        "definition": "Measures the relative variability with respect to the mean.",
        "formula": r"CV=\frac{\sigma}{\mu}\times 100\%",
        "formula_text": "CV = (sigma / mu) x 100%",
        "usefulness": "It compares variability across datasets with different scales or units.",
        "icon": "bi-percent",
    },
}


def descriptive_statistics(series: pd.Series) -> dict:
    mean = float(series.mean())
    std = float(series.std(ddof=1)) if len(series) > 1 else 0.0
    mode = series.mode()
    cv = (std / mean) * 100 if mean else 0.0
    q1 = float(series.quantile(0.25))
    q2 = float(series.quantile(0.50))
    q3 = float(series.quantile(0.75))
    result = {
        "count": int(series.count()),
        "mean": mean,
        "median": float(series.median()),
        "mode": float(mode.iloc[0]) if not mode.empty else math.nan,
        "variance": float(series.var(ddof=1)) if len(series) > 1 else 0.0,
        "standard_deviation": std,
        "minimum": float(series.min()),
        "maximum": float(series.max()),
        "range": float(series.max() - series.min()),
        "q1": q1,
        "q2": q2,
        "q3": q3,
        "interquartile_range": float(q3 - q1),
        "skewness": float(series.skew()) if len(series) > 2 else 0.0,
        "kurtosis": float(series.kurtosis()) if len(series) > 3 else 0.0,
        "coefficient_of_variation": float(cv),
    }
    return {key: round(value, 6) if isinstance(value, float) else value for key, value in result.items()}


def _value(stats: dict, key: str) -> float:
    return float(stats.get(key, 0) or 0)


def _interpret_stat(stats: dict, key: str) -> str:
    value = _value(stats, key)
    if key == "count":
        return f"The dataset contains {int(value)} observations."
    if key == "mean":
        return f"The average value is {value:.2f}."
    if key == "median":
        return f"Half of the observations lie below {value:.2f}."
    if key == "mode":
        return f"The most frequently occurring value is {value:.2f}."
    if key == "variance":
        mean = abs(_value(stats, "mean"))
        spread = "low" if value <= mean else "high"
        return f"The variance is {spread}, indicating {'limited' if spread == 'low' else 'substantial'} spread around the mean."
    if key == "standard_deviation":
        return f"Values typically deviate by {value:.2f} units from the mean."
    if key == "minimum":
        return f"The smallest observed value is {value:.2f}."
    if key == "maximum":
        return f"The largest observed value is {value:.2f}."
    if key == "range":
        return f"The values span {value:.2f} units."
    if key == "q1":
        return "25% of observations are below this value."
    if key == "q2":
        return "This is the median of the dataset."
    if key == "q3":
        return "75% of observations lie below this value."
    if key == "interquartile_range":
        return "The middle 50% of observations fall within this interval."
    if key == "skewness":
        if value > 0.5:
            return "The dataset is positively skewed."
        if value < -0.5:
            return "The dataset is negatively skewed."
        return "The dataset is approximately symmetric."
    if key == "kurtosis":
        if value > 0.5:
            return "The distribution is more peaked or heavy-tailed than a normal distribution."
        if value < -0.5:
            return "The distribution is flatter or lighter-tailed than a normal distribution."
        return "The distribution is approximately normal in tail weight."
    if key == "coefficient_of_variation":
        if value < 15:
            level = "low"
        elif value < 35:
            level = "moderate"
        else:
            level = "high"
        return f"The dataset shows {level} relative variability."
    return "This statistic summarizes an important property of the dataset."


def _stat_card(stats: dict, key: str) -> dict:
    meta = STAT_METADATA[key]
    value = stats[key]
    return {
        "key": key,
        "name": meta["name"],
        "full_form": meta["full_form"],
        "definition": meta["definition"],
        "formula": meta["formula"],
        "formula_text": meta["formula_text"],
        "usefulness": meta["usefulness"],
        "value": value,
        "interpretation": _interpret_stat(stats, key),
        "icon": meta["icon"],
    }


def statistic_cards(stats: dict) -> dict:
    return {
        "basic": [_stat_card(stats, key) for key in BASIC_STAT_KEYS],
        "advanced": [_stat_card(stats, key) for key in ADVANCED_STAT_KEYS],
    }


def engineering_insights(stats: dict, cleaned: CleanedSeries, distribution: dict) -> list[str]:
    insights = [f"The data approximately follows a {distribution['best']['display_name']}."]
    if abs(stats["skewness"]) < 0.5:
        insights.append("The dataset is close to symmetric.")
    elif stats["skewness"] > 0:
        insights.append("The dataset contains right skewness.")
    else:
        insights.append("The dataset contains left skewness.")

    if stats["coefficient_of_variation"] > 50:
        insights.append("The variance is relatively high compared with the mean.")
    else:
        insights.append("Most observations lie comparatively close to the mean.")

    if cleaned.summary["outliers_detected"] > 0:
        insights.append(f"{cleaned.summary['outliers_detected']} outlier(s) were detected using the IQR rule.")
    else:
        insights.append("No IQR outliers were detected.")

    insights.append(distribution["reason"])
    return insights
