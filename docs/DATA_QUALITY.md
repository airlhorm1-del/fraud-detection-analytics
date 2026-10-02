# Data quality report

What was checked in the PaySim data, what was found, what was done about it, and what the data cannot
support. The raw CSV is never edited; cleaning happens in SQL (`sql/10_clean.sql`) and adds flags
instead of changing values. Full tables: [results/01_profile.md](results/01_profile.md).

## 1. Checks on arrival

| Check | Result |
|---|---|
| Rows in the CSV file vs rows loaded into DuckDB | 6,362,620 both: nothing lost |
| Column types | Set explicitly for all 11 columns, nothing guessed |
| Missing values in the key columns | None |
| Duplicate rows (all values identical) | None |

## 2. Issues found and how they were resolved

| # | Issue | Size | Resolution |
|---|---|---|---|
| 1 | Inconsistent column names in the source (`oldbalanceOrg` next to `newbalanceOrig`) | The 4 balance columns | Renamed to one consistent scheme (`sender_balance_before`, `receiver_balance_after`, ...) |
| 2 | Time is only a step number (1 to 743), not a date | All rows | Turned into day (1 to 31) and hour (0 to 23), taking step 1 as midnight on day 1. The night-time pattern in the data supports this reading. No calendar dates are invented |
| 3 | The sender's balance does not add up (before minus amount is not after) in most genuine transfers and cash-outs | 90.5% of genuine money-out transactions | Flagged (`sender_balance_adds_up`), not corrected: an analyst never changes the evidence |
| 4 | Receivers' balances that stay at zero before and after although money arrives | 49.6% of fraudulent, 0.1% of genuine money-out transactions | Flagged (`receiver_balance_adds_up`); used as warning sign R2 |
| 5 | Money sent from accounts recorded with a zero balance | 47% of genuine money-out transactions | Left as is; it explains 25 of the 31 frauds the rules miss (see `docs/cases.md`, case 3) |
| 6 | Cash-outs of exactly 0.00 | 16, all fraud | Kept: they are a fraud signal (a "test" before the theft), used as rule R5 |
| 7 | The simulator's own fraud flag could be mistaken for a rule | 16 flagged | Renamed `simulator_flag` and reported as the baseline (0.2% of fraud caught) |

## 3. What the data cannot support (documented, not hidden)

| Limit | Consequence |
|---|---|
| Fraud only occurs in TRANSFER and CASH_OUT | Rules only look at money leaving an account |
| Only 9,298 of 6.35 million senders appear more than once | "Too many transactions in a short time" rules cannot be built |
| A transfer and the receiver's later cash-out are not linked by account (3 matches) | The mule chain is only visible by matching same amount and same hour (4,078 of 4,097 fraudulent transfers) |
| "Whole balance taken" separates fraud perfectly here, unlike real data | All results are also reported without that rule (stress test) |
| No customer details, devices or locations | Rules use transaction data only |

## 4. Automated checks

| Check | Result |
|---|---|
| Row counts after loading, cleaning and scoring | 6,362,620 at every step |
| Rerun from the raw file (`scripts/run_all.py`) | Same numbers every time, in about 30 seconds |
| Rules measured against the fraud labels | Precision, recall and money caught reported for each rule, each threshold, with and without R1 |
