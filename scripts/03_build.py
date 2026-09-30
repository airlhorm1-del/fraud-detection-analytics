"""Stages 3 and 4 - clean the data and apply the fraud rules.

Runs the SQL files in sql/ in name order (10_clean.sql, then 20_rules.sql) against the DuckDB
database, then prints a few sanity checks.

Run: uv run python scripts/03_build.py
"""
from common import SQL_DIR, connect


def main() -> None:
    con = connect()
    for path in sorted(SQL_DIR.glob("*.sql")):
        con.execute(path.read_text(encoding="utf-8"))
        print(f"ran {path.name}")

    raw, clean, scored = (con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
                          for t in ("raw_transactions", "transactions", "scored"))
    print(f"rows: raw {raw:,} | clean {clean:,} | scored {scored:,}",
          "OK" if raw == clean == scored else "MISMATCH")
    alerts, fraud = con.execute("SELECT sum(is_alert::INT), sum(is_fraud) FROM scored").fetchone()
    print(f"alerts: {alerts:,} | fraud in data: {fraud:,}")
    con.close()


if __name__ == "__main__":
    main()
