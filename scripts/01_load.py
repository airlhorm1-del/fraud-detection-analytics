"""Stage 1 - get the data.

Reads the PaySim CSV into a DuckDB database with explicit column types, adds a transaction id,
saves a Parquet copy (much faster to read than the CSV) and checks that no row was lost.

Run: uv run python scripts/01_load.py
"""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "data" / "raw" / "PS_20174392719_1491204439457_log.csv"
DB_PATH = ROOT / "data" / "processed" / "fraud.duckdb"
PARQUET = ROOT / "data" / "processed" / "transactions_raw.parquet"

COLUMNS = {
    "step": "INTEGER",          # hour of the 30-day simulation (1 = first hour)
    "type": "VARCHAR",          # CASH_IN, CASH_OUT, DEBIT, PAYMENT, TRANSFER
    "amount": "DOUBLE",
    "nameOrig": "VARCHAR",      # customer who starts the transaction
    "oldbalanceOrg": "DOUBLE",  # sender balance before
    "newbalanceOrig": "DOUBLE", # sender balance after
    "nameDest": "VARCHAR",      # receiver (C... = customer, M... = merchant)
    "oldbalanceDest": "DOUBLE", # receiver balance before
    "newbalanceDest": "DOUBLE", # receiver balance after
    "isFraud": "INTEGER",       # 1 = fraud (the label we test our rules against)
    "isFlaggedFraud": "INTEGER",  # 1 = flagged by the simulator's own simple rule
}


def count_csv_rows(path: Path) -> int:
    with path.open("rb") as f:
        return sum(1 for _ in f) - 1  # minus the header line


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))
    cols = ", ".join(f"'{k}': '{v}'" for k, v in COLUMNS.items())
    con.execute(f"""
        CREATE OR REPLACE TABLE raw_transactions AS
        SELECT row_number() OVER () AS txn_id, *
        FROM read_csv('{RAW_CSV.as_posix()}', header = true, columns = {{{cols}}})
    """)
    con.execute(f"COPY raw_transactions TO '{PARQUET.as_posix()}' (FORMAT parquet)")

    loaded = con.execute("SELECT count(*) FROM raw_transactions").fetchone()[0]
    in_file = count_csv_rows(RAW_CSV)
    print(f"Rows in the CSV file:   {in_file:,}")
    print(f"Rows loaded in DuckDB:  {loaded:,}")
    print("Check:", "OK - nothing lost" if loaded == in_file else "MISMATCH - investigate")
    con.close()


if __name__ == "__main__":
    main()
