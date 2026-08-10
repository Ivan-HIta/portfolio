"""Load and normalize synthetic exception data or a local user-provided file."""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import pandas as pd

from .data_generator import default_data_path, write_synthetic_data
from .utils import normalise_exception_frame


def load_exceptions(path: str | Path | None = None, validate: bool = False) -> pd.DataFrame:
    """Load the bundled synthetic CSV, regenerating it only if it is absent."""

    target = Path(path) if path is not None else default_data_path()
    if not target.exists():
        if path is not None:
            raise FileNotFoundError(f"Exception data file not found: {target}")
        write_synthetic_data(target)
    frame = normalise_exception_frame(pd.read_csv(target))
    if validate:
        from .validation import validate_exceptions

        result = validate_exceptions(frame)
        if not result["is_valid"]:
            raise ValueError(f"Exception data failed validation: {result['summary']}")
    return frame


def load_uploaded_exceptions(source: str | Path | BinaryIO, validate: bool = False) -> pd.DataFrame:
    """Load a local CSV/XLSX upload and normalize the base fields."""

    name = str(getattr(source, "name", source)).lower()
    frame = pd.read_excel(source) if name.endswith((".xlsx", ".xls")) else pd.read_csv(source)
    frame = normalise_exception_frame(frame)
    if validate:
        from .validation import validate_exceptions

        result = validate_exceptions(frame)
        if not result["is_valid"]:
            raise ValueError(f"Uploaded exception data failed validation: {result['summary']}")
    return frame


load_exception_data = load_exceptions
load_data = load_exceptions
