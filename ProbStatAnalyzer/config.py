from pathlib import Path


class Config:
    SECRET_KEY = "change-this-secret-key-for-production"
    BASE_DIR = Path(__file__).resolve().parent
    UPLOAD_FOLDER = BASE_DIR / "uploads"
    REPORT_FOLDER = BASE_DIR / "reports"
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"csv"}
