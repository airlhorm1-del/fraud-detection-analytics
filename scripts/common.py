"""Shared paths and small helpers for the pipeline scripts."""
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "processed" / "fraud.duckdb"
SQL_DIR = ROOT / "sql"
RESULTS_DIR = ROOT / "docs" / "results"
IMAGES_DIR = ROOT / "docs" / "images"
POWERBI_DATA = ROOT / "powerbi" / "data"


def connect(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DB_PATH), read_only=read_only)


def md_table(df: pd.DataFrame) -> str:
    """A pandas table as a Markdown table, with thousands separators for numbers."""
    def fmt(v):
        if isinstance(v, bool) or v is None:
            return "" if v is None else str(v)
        if isinstance(v, float):
            return f"{v:,.0f}" if v.is_integer() and abs(v) >= 1000 else (f"{v:,.2f}" if abs(v) >= 1000 else f"{v:g}")
        if isinstance(v, int):
            return f"{v:,}"
        return str(v)

    head = "| " + " | ".join(df.columns) + " |"
    sep = "|" + "|".join("---" for _ in df.columns) + "|"
    rows = ["| " + " | ".join(fmt(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join([head, sep, *rows])
