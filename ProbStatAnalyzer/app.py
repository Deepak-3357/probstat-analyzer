from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd
from flask import Flask, flash, jsonify, redirect, render_template, request, send_file, session, url_for
from werkzeug.utils import secure_filename

from config import Config
from models.distributions import fit_distributions
from models.pdf_generator import build_pdf_report
from models.preprocessing import clean_numeric_series, dataset_profile
from models.probability import calculate_probability
from models.statistics import descriptive_statistics, engineering_insights, statistic_cards
from models.visualization import build_all_charts
from utils.helpers import allowed_file, ensure_directories, json_safe

SUPPORTED_DISTRIBUTION_NAMES = {"binom", "poisson", "geom", "uniform", "expon", "norm"}


def _analysis_path(app: Flask, analysis_id: str) -> Path:
    return Path(app.config["REPORT_FOLDER"]) / f"analysis_{analysis_id}.json"


def _save_analysis(app: Flask, analysis: dict) -> str:
    analysis_id = uuid4().hex
    _analysis_path(app, analysis_id).write_text(json.dumps(analysis), encoding="utf-8")
    return analysis_id


def _load_analysis(app: Flask) -> dict | None:
    analysis_id = session.get("analysis_id")
    if not analysis_id:
        return None
    path = _analysis_path(app, analysis_id)
    if not path.exists():
        return None
    analysis = json.loads(path.read_text(encoding="utf-8"))
    distribution = analysis.get("distribution", {})
    best_name = distribution.get("best", {}).get("name")
    if best_name not in SUPPORTED_DISTRIBUTION_NAMES or "explanation" not in distribution or "dataset_type" not in distribution:
        session.pop("analysis_id", None)
        session.pop("probability", None)
        return None
    if "statistic_cards" not in analysis and "statistics" in analysis:
        analysis["statistic_cards"] = statistic_cards(analysis["statistics"])
    return analysis


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    ensure_directories([app.config["UPLOAD_FOLDER"], app.config["REPORT_FOLDER"]])

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/upload", methods=["GET", "POST"])
    def upload():
        if request.method == "GET":
            return render_template("upload.html")

        file = request.files.get("dataset")
        if not file or file.filename == "":
            flash("Choose a CSV file before uploading.", "warning")
            return redirect(url_for("upload"))

        if not allowed_file(file.filename):
            flash("Only CSV files are accepted.", "danger")
            return redirect(url_for("upload"))

        filename = secure_filename(file.filename)
        unique_name = f"{Path(filename).stem}_{uuid4().hex[:8]}.csv"
        upload_path = Path(app.config["UPLOAD_FOLDER"]) / unique_name
        file.save(upload_path)

        try:
            df = pd.read_csv(upload_path)
        except Exception as exc:
            upload_path.unlink(missing_ok=True)
            flash(f"The file could not be read as a CSV: {exc}", "danger")
            return redirect(url_for("upload"))

        profile = dataset_profile(df)
        numeric_columns = df.select_dtypes(include="number").columns.tolist()
        session["dataset"] = {
            "original_name": filename,
            "path": str(upload_path),
            "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "profile": profile,
            "numeric_columns": numeric_columns,
        }
        session.pop("analysis_id", None)
        session.pop("probability", None)

        if not numeric_columns:
            flash("Uploaded successfully, but no numeric column was found.", "warning")
        else:
            flash("CSV uploaded and profiled successfully.", "success")
        return redirect(url_for("dashboard"))

    @app.route("/dashboard")
    def dashboard():
        dataset = session.get("dataset")
        if not dataset:
            flash("Upload a dataset to open the dashboard.", "info")
            return redirect(url_for("upload"))

        df = pd.read_csv(dataset["path"])
        preview = df.head(20).to_html(classes="table table-sm table-hover align-middle", index=False)
        return render_template(
            "dashboard.html",
            dataset=dataset,
            preview=preview,
            analysis=_load_analysis(app),
            probability=session.get("probability"),
        )

    @app.route("/analyze", methods=["POST"])
    def analyze():
        dataset = session.get("dataset")
        if not dataset:
            flash("Upload a dataset first.", "warning")
            return redirect(url_for("upload"))

        column = request.form.get("column")
        if column not in dataset.get("numeric_columns", []):
            flash("Select a valid numeric column.", "danger")
            return redirect(url_for("dashboard"))

        df = pd.read_csv(dataset["path"])
        cleaned = clean_numeric_series(df, column)
        if cleaned.series.empty:
            flash("The selected column has no usable numeric values after cleaning.", "danger")
            return redirect(url_for("dashboard"))

        stats = descriptive_statistics(cleaned.series)
        stats_cards = statistic_cards(stats)
        distribution_result = fit_distributions(cleaned.series)
        charts = build_all_charts(cleaned.series, distribution_result)
        insights = engineering_insights(stats, cleaned, distribution_result)

        analysis_payload = json_safe(
            {
                "column": column,
                "cleaning": cleaned.summary,
                "statistics": stats,
                "statistic_cards": stats_cards,
                "distribution": distribution_result,
                "charts": charts,
                "insights": insights,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
        )
        session["analysis_id"] = _save_analysis(app, analysis_payload)
        session.pop("probability", None)
        flash("Analysis complete.", "success")
        return redirect(url_for("dashboard"))

    @app.route("/calculate_probability", methods=["POST"])
    def calculate_probability_ajax():
        analysis = _load_analysis(app)
        dataset = session.get("dataset")
        if not analysis or not dataset:
            return jsonify({"success": False, "error": "Run a distribution analysis before calculating probability."}), 400

        payload = request.get_json(silent=True) or {}
        operation = payload.get("operation", "lte")
        try:
            x_value = float(payload.get("x_value", "nan"))
            a_raw = payload.get("a_value")
            b_raw = payload.get("b_value")
            a_value = float(a_raw) if a_raw not in (None, "") else None
            b_value = float(b_raw) if b_raw not in (None, "") else None
        except (TypeError, ValueError):
            return jsonify({"success": False, "error": "Enter valid numeric probability inputs."}), 400

        if operation in {"lte", "gte"} and not pd.notna(x_value):
            return jsonify({"success": False, "error": "Enter a valid value for x."}), 400
        if operation == "between" and (a_value is None or b_value is None):
            return jsonify({"success": False, "error": "Enter both lower and upper bounds."}), 400

        try:
            result = calculate_probability(analysis["distribution"]["best"], operation, x_value, a_value, b_value)
        except Exception as exc:
            return jsonify({"success": False, "error": f"Probability calculation failed: {exc}"}), 400

        session["probability"] = json_safe(result)
        return jsonify({
            "success": True,
            "probability": result["result"],
            "formula": result["formula"],
            "result_math": result["result_math"],
            "steps": [f"{step['label']}: {step['math']}" for step in result["steps"]],
            "step_items": result["steps"],
            "interpretation": result["interpretation"],
        })

    @app.route("/export-statistics")
    def export_statistics():
        analysis = _load_analysis(app)
        if not analysis:
            flash("Analyze a column before exporting statistics.", "warning")
            return redirect(url_for("dashboard"))

        export_path = Path(app.config["REPORT_FOLDER"]) / f"statistics_{uuid4().hex[:8]}.xlsx"
        stat_rows = []
        for group in ("basic", "advanced"):
            for item in analysis["statistic_cards"][group]:
                stat_rows.append({
                    "Statistic": item["name"],
                    "Value": item["value"],
                    "Definition": item["definition"],
                })
        with pd.ExcelWriter(export_path, engine="openpyxl") as writer:
            pd.DataFrame(stat_rows).to_excel(writer, index=False, sheet_name="Statistics")
            worksheet = writer.sheets["Statistics"]
            worksheet.freeze_panes = "A2"
            widths = {"A": 24, "B": 16, "C": 72}
            for column, width in widths.items():
                worksheet.column_dimensions[column].width = width
            for cell in worksheet[1]:
                cell.style = "Accent1"
        return send_file(export_path, as_attachment=True, download_name="probstat_statistics.xlsx")

    @app.route("/report")
    def report():
        dataset = session.get("dataset")
        analysis = _load_analysis(app)
        if not dataset or not analysis:
            flash("Run an analysis before generating a PDF report.", "warning")
            return redirect(url_for("dashboard"))

        df = pd.read_csv(dataset["path"])
        cleaned = clean_numeric_series(df, analysis["column"])
        probability_result = session.get("probability")
        report_path = Path(app.config["REPORT_FOLDER"]) / f"ProbStat_Report_{uuid4().hex[:8]}.pdf"
        build_pdf_report(report_path, dataset, analysis, cleaned.series, probability_result)
        return send_file(report_path, as_attachment=True, download_name="ProbStat_Analyzer_Report.pdf")

    @app.errorhandler(413)
    def file_too_large(_error):
        flash("The uploaded file is larger than 20MB.", "danger")
        return redirect(url_for("upload"))

    @app.context_processor
    def inject_globals():
        history_path = Path(app.config["UPLOAD_FOLDER"])
        recent = sorted(history_path.glob("*.csv"), key=os.path.getmtime, reverse=True)[:5]
        return {"recent_uploads": [p.name for p in recent], "json": json}

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
