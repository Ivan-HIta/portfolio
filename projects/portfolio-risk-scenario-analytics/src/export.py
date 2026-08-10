"""Safe in-memory CSV and Excel exports for local Streamlit downloads."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Mapping

import pandas as pd


def dataframe_to_csv(data: pd.DataFrame) -> bytes:
    """Return UTF-8 CSV bytes suitable for ``st.download_button``."""
    return data.to_csv(index=False).encode("utf-8")


def export_to_csv(data: pd.DataFrame, path: str | Path) -> Path:
    """Write a CSV explicitly requested by a local user and return its path."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(destination, index=False)
    return destination


def dataframes_to_excel(sheets: Mapping[str, pd.DataFrame]) -> bytes:
    """Build a multi-sheet XLSX workbook entirely in memory."""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for name, frame in sheets.items():
            frame.to_excel(writer, sheet_name=str(name)[:31], index=False)
    buffer.seek(0)
    return buffer.getvalue()


def scenario_result_to_excel(result: Mapping[str, object]) -> bytes:
    """Export detailed scenario impact tables to an XLSX download."""
    sheets = {
        "Holding Impacts": result.get("holding_impacts", pd.DataFrame()),
        "By Asset Class": result.get("impact_by_asset_class", pd.DataFrame()),
        "By Sector": result.get("impact_by_sector", pd.DataFrame()),
        "Top Holdings": result.get("top_holding_impacts", pd.DataFrame()),
    }
    return dataframes_to_excel({name: frame for name, frame in sheets.items() if isinstance(frame, pd.DataFrame)})


to_csv_bytes = dataframe_to_csv
