# Code guide

What every file does, in the order it runs, in plain language. `scripts/run_all.py` runs everything
(about 30 seconds once the CSV is downloaded).

## How a run works

```
scripts/01_load.py      raw CSV -> DuckDB table raw_transactions (+ Parquet copy); row count checked
scripts/02_profile.py   raw data -> docs/results/01_profile.md (look before changing anything)
scripts/03_build.py     runs sql/10_clean.sql (table transactions) then sql/20_rules.sql (table scored)
scripts/04_evaluate.py  scored -> docs/results/02_evaluation.md and the Power BI tables in powerbi/data/
scripts/06_charts.py    -> the charts in docs/images/
```

The database is one DuckDB file, `data/processed/fraud.duckdb` (kept on the laptop, too big for GitHub).

## Files

| File | What it does | Reads | Writes |
|---|---|---|---|
| `scripts/common.py` | Shared folder paths, the database connection, and a helper that turns a table into Markdown | - | - |
| `scripts/01_load.py` | Loads the 6.3 million rows with an explicit type for each column, adds a transaction id, saves a faster Parquet copy, and checks that the number of rows matches the file | `data/raw/PS_...log.csv` | table `raw_transactions`, `transactions_raw.parquet` |
| `scripts/02_profile.py` | Answers the first questions about the raw data: size, missing values, duplicates, fraud by type, hour and amount, balance quality, which fraud patterns the data can support | `raw_transactions` | `docs/results/01_profile.md` |
| `sql/10_clean.sql` | Consistent column names, day and hour, receiver type (customer or merchant), balance-quality flags, renamed simulator flag. Nothing deleted | `raw_transactions` | table `transactions` |
| `sql/20_rules.sql` | The rule catalogue (six rules and their points), one true/false column per rule, the risk score, the score without R1, the alert flag (score 30 or more), priority and a readable list of reasons | `transactions` | tables `rule_catalogue`, `scored` |
| `scripts/03_build.py` | Runs the two SQL files in order and checks the row counts | the SQL files | the two tables above |
| `scripts/04_evaluate.py` | Measures the rules against the fraud labels: overall result, by priority, each rule alone, each threshold with and without R1. Exports the tables Power BI uses | `scored` | `docs/results/02_evaluation.md`, `powerbi/data/*.csv` |
| `scripts/06_charts.py` | Draws the six charts | `scored`, `powerbi/data/` | `docs/images/*.png` |
| `scripts/run_all.py` | Runs the steps above in order | - | everything above |

## Outputs

| Folder or file | What it is |
|---|---|
| `docs/results/` | The profile and evaluation tables (generated, never typed by hand) |
| `docs/images/` | The charts (generated) |
| `docs/cases.md` | Four investigation write-ups based on real rows (look them up by `txn_id`) |
| `docs/decisions.md` | Every design choice and why |
| `powerbi/data/` | Six small tables for Power BI: summary by day/hour/type, alerts, missed fraud, rules, rule results, threshold results |
| `powerbi/DASHBOARD_GUIDE.md` | The Power BI data model, DAX measures and report pages |
