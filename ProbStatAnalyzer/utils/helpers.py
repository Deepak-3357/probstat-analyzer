from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

import numpy as np


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() == "csv"


def ensure_directories(paths: Iterable[Path]) -> None:
    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)


def json_safe(value):
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        value = float(value)
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    return value
