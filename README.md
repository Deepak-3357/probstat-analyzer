# ProbStat Analyzer

## A Web-Based Probability Distribution Analysis and Statistical Modeling System

ProbStat Analyzer is a web-based statistical analysis system developed as a capstone project for **UBA5316 – Probabilistic Methods and Linear Algebra (PMLA)**.

The system analyzes numerical datasets, performs descriptive statistical analysis, classifies datasets as discrete or continuous, fits suitable probability distributions, evaluates goodness-of-fit, calculates probabilities, generates visualizations, and provides statistical interpretations.

---

## 📌 Project Overview

Probability distributions are widely used to model uncertainty and random phenomena in engineering, science, healthcare, finance, manufacturing, and data analysis.

Selecting an appropriate probability distribution manually can be difficult, especially when dealing with large numerical datasets.

**ProbStat Analyzer** provides an automated statistical workflow that allows users to upload a dataset and obtain a complete probability distribution analysis.

The system:

- Accepts CSV datasets
- Performs data preprocessing
- Extracts numerical observations
- Calculates descriptive statistics
- Classifies data as discrete or continuous
- Fits suitable probability distributions
- Estimates distribution parameters
- Calculates goodness-of-fit measures
- Compares candidate distributions
- Identifies the best-fitting distribution
- Calculates probabilities
- Generates statistical visualizations
- Provides distribution explanations
- Supports statistical report generation

---

# 🎯 Objectives

The main objectives of ProbStat Analyzer are:

1. Analyze numerical datasets using probability and statistical methods.
2. Classify datasets into discrete and continuous random variables.
3. Calculate descriptive statistics.
4. Estimate parameters for probability distributions.
5. Fit suitable probability distributions to observed data.
6. Compare distributions using goodness-of-fit measures.
7. Identify the distribution that best represents the dataset.
8. Calculate probabilities for selected events.
9. Generate graphical representations of the observed and fitted distributions.
10. Provide understandable statistical interpretations of the results.

---

# 📊 Supported Probability Distributions

The system supports six probability distributions.

## Continuous Distributions

| Distribution | Function | Parameters |
|---|---|---|
| Normal | PDF | Mean (μ), Standard Deviation (σ) |
| Uniform | PDF | Minimum (a), Maximum (b) |
| Exponential | PDF | Rate (λ) |

## Discrete Distributions

| Distribution | Function | Parameters |
|---|---|---|
| Binomial | PMF | n, p |
| Poisson | PMF | λ |
| Geometric | PMF | p |

---

# 🧮 Mathematical Foundation

## 1. Normal Distribution

The Normal probability density function is:

\[
f(x)=\frac{1}{\sigma\sqrt{2\pi}}
e^{-\frac{(x-\mu)^2}{2\sigma^2}}
\]

Mean:

\[
E(X)=\mu
\]

Variance:

\[
Var(X)=\sigma^2
\]

---

## 2. Uniform Distribution

\[
f(x)=\frac{1}{b-a}, \quad a\leq x\leq b
\]

Mean:

\[
E(X)=\frac{a+b}{2}
\]

Variance:

\[
Var(X)=\frac{(b-a)^2}{12}
\]

---

## 3. Exponential Distribution

\[
f(x)=\lambda e^{-\lambda x}, \quad x\geq0
\]

Mean:

\[
E(X)=\frac{1}{\lambda}
\]

Variance:

\[
Var(X)=\frac{1}{\lambda^2}
\]

The rate parameter is estimated from the sample mean:

\[
\hat{\lambda}=\frac{1}{\bar{x}}
\]

---

## 4. Poisson Distribution

\[
P(X=x)=\frac{e^{-\lambda}\lambda^x}{x!}
\]

Mean:

\[
E(X)=\lambda
\]

Variance:

\[
Var(X)=\lambda
\]

---

## 5. Binomial Distribution

\[
P(X=x)=
\binom{n}{x}p^x(1-p)^{n-x}
\]

Mean:

\[
E(X)=np
\]

Variance:

\[
Var(X)=np(1-p)
\]

---

## 6. Geometric Distribution

The project uses the convention where \(X\) represents the number of trials until the first success.

\[
P(X=x)=p(1-p)^{x-1}
\]

Mean:

\[
E(X)=\frac{1}{p}
\]

Variance:

\[
Var(X)=\frac{1-p}{p^2}
\]

---

# 🔬 Goodness-of-Fit Analysis

ProbStat Analyzer does not select a distribution simply by looking at the graph.

The system statistically evaluates each suitable candidate distribution using:

- Kolmogorov-Smirnov (KS) Statistic
- Akaike Information Criterion (AIC)
- Bayesian Information Criterion (BIC)

---

## Kolmogorov-Smirnov Statistic

The KS statistic measures the maximum difference between the empirical distribution and the fitted theoretical distribution.

\[
D=\max|F_n(x)-F(x)|
\]

A lower KS value indicates that the fitted distribution is closer to the observed data.

For discrete distributions, a discrete KS calculation is used to account for the stepwise nature of discrete probability distributions.

---

## Akaike Information Criterion

\[
AIC=2k-2\ln(L)
\]

where:

- \(k\) = number of model parameters
- \(L\) = likelihood of the observed data

Lower AIC indicates a better model according to the AIC criterion.

---

## Bayesian Information Criterion

\[
BIC=k\ln(n)-2\ln(L)
\]

where:

- \(k\) = number of parameters
- \(n\) = number of observations
- \(L\) = likelihood

Lower BIC indicates a better model according to the BIC criterion.

---

# 🔄 Distribution Selection Process

The analyzer independently determines which probability distribution best represents the uploaded dataset.

```text
CSV Dataset
     ↓
Data Preprocessing
     ↓
Numerical Data Extraction
     ↓
Discrete / Continuous Classification
     ↓
Suitable Candidate Distributions
     ↓
Parameter Estimation
     ↓
Distribution Fitting
     ↓
KS + AIC + BIC
     ↓
Distribution Comparison
     ↓
Best-Fitting Distribution
     ↓
Probability Calculation
     ↓
Visualization & Report
