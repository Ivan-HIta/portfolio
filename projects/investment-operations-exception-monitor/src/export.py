"""Small export helpers for Streamlit download controls."""

from __future__ import annotations

import pandas as pd


def dataframe_to_csv(data: pd.DataFrame) -> bytes:
    """Return an UTF-8 CSV payload suitable for ``st.download_button``."""

    if not isinstance(data, pd.DataFrame):
        raise TypeError("data must be a pandas DataFrame")
    return data.to_csv(index=False).encode("utf-8")


to_csv_bytes = dataframe_to_csv
export_csv = dataframe_to_csv
