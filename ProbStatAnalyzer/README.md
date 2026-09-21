# ProbStat Analyzer

ProbStat Analyzer is a local Flask web application for probability distribution analysis and statistical modeling. It lets users upload a CSV dataset, select a numeric column, clean the data, compute descriptive statistics, fit probability distributions, inspect interactive Plotly charts, calculate probabilities, export statistics to Excel, and generate a professional PDF report.

## Features

- CSV upload with 20MB limit and CSV-only validation
- Dataset preview of the first 20 rows
- Dataset profile: rows, columns, column names, missing values, and data types
- Automatic numeric column detection
- Data cleaning: null removal, duplicate removal, non-finite value removal, and IQR outlier handling
- Descriptive statistics cards
- Distribution fitting with KS statistic, log likelihood, AIC, and BIC
- Supported distributions: Normal, Poisson, Binomial, Exponential, Uniform, Gamma, and Log Normal
- Interactive Plotly charts with PNG download controls
- Probability calculator for `P(X <= x)`, `P(X >= x)`, and `P(a < X < b)`
- Engineering insight generation
- ReportLab PDF report
- Excel export for statistics
- Dashboard with sidebar navigation, dark mode, search, recent upload history, loading-friendly UI, and toast notifications
- Responsive Bootstrap 5 interface

## Folder Structure

```text
ProbStatAnalyzer/
|-- app.py
|-- config.py
|-- requirements.txt
|-- README.md
|-- static/
|   |-- css/
|   |-- js/
|   `-- images/
|-- templates/
|   |-- index.html
|   |-- dashboard.html
|   |-- upload.html
|   |-- report.html
|   |-- navbar.html
|   `-- partials_flash.html
|-- uploads/
|-- reports/
|-- models/
|   |-- statistics.py
|   |-- distributions.py
|   |-- probability.py
|   |-- visualization.py
|   |-- pdf_generator.py
|   `-- preprocessing.py
|-- utils/
|   `-- helpers.py
`-- dataset_samples/
    `-- sample_measurements.csv
```

## Installation

Open the project in Visual Studio Code, then run these commands from the `ProbStatAnalyzer` folder.

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

The app runs at:

```text
http://127.0.0.1:5000
```

## Usage

1. Open the home page and choose **Upload Dataset**.
2. Upload a CSV file.
3. Review the dataset profile and preview.
4. Select a numeric column and run the analysis.
5. Explore statistics, fitted distributions, charts, and insights.
6. Use the probability calculator.
7. Download the Excel statistics export or PDF report.

## Screenshots

Add screenshots here after running the app locally:

- Home page
- Upload page
- Dashboard
- Distribution comparison
- PDF report

## Notes

- Distribution fitting can fail for mathematically incompatible data. The dashboard marks those candidates as skipped and continues with successful fits.
- For count distributions such as Poisson and Binomial, the app only attempts fitting when the selected data is non-negative integer-like.
- Plotly charts are stored server-side during a run so Flask sessions stay small and reliable.
