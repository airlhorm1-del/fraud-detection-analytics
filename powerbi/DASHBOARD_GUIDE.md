# Power BI: data model and DAX measures

The pipeline writes small, ready-made tables into `powerbi/data/` for reporting, so a report reads
those rather than the 6.3 million raw rows. This file lists the tables, the measures and the report pages.

## 1. Load the data (Home > Get data > Text/CSV)

| File | Load as table | What it holds |
|---|---|---|
| summary_by_day_hour_type.csv | Summary | Counts and amounts per day, hour and transaction type (2,729 rows: only the combinations that had transactions) |
| alerts.csv | Alerts | Every alert (9,625 rows): score, priority, reasons, outcome |
| missed_fraud.csv | Missed | The 31 frauds without an alert |
| rule_catalogue.csv | Rules | The six rules and their points |
| rule_performance.csv | RulePerformance | Each rule on its own: precision and recall |
| threshold_analysis.csv | Thresholds | Alert volume, precision and recall per threshold, with and without R1 |

**Day and Hour tables (no date table, on purpose).** PaySim has no calendar dates, only simulation
day 1-31 and the hour, so "Mark as date table" and time intelligence do not apply. Modeling > New table:

```DAX
Days  = SELECTCOLUMNS ( GENERATESERIES ( 1, 31, 1 ), "Day", [Value] )
Hours = SELECTCOLUMNS ( GENERATESERIES ( 0, 23, 1 ), "Hour", [Value] )
```

Relationships (one-to-many, single direction): Days[Day] to Summary[day], Alerts[day] and Missed[day];
Hours[Hour] to Summary[hour] and Alerts[hour]. One day or hour slicer then filters every visual. The
other tables stay unlinked: Alerts and Missed never share a transaction, and Rules, RulePerformance
and Thresholds are small finished results.

## 2. Measures (Modeling > New measure)

```DAX
Transactions        = SUM ( Summary[transactions] )
Fraud Cases         = SUM ( Summary[fraud_transactions] )
Fraud Rate %        = DIVIDE ( [Fraud Cases], [Transactions] )
Alerts              = SUM ( Summary[alerts] )
Fraud Caught        = SUM ( Summary[alerts_confirmed_fraud] )
False Alarms        = SUM ( Summary[false_alarms] )
Fraud Missed        = SUM ( Summary[fraud_missed] )
Precision %         = DIVIDE ( [Fraud Caught], [Alerts] )          -- alerts that were real fraud
Recall %            = DIVIDE ( [Fraud Caught], [Fraud Cases] )     -- fraud that got an alert
Fraud Amount        = SUM ( Summary[fraud_amount] )
Fraud Amount Caught = SUM ( Summary[fraud_amount_caught] )
Money Caught %      = DIVIDE ( [Fraud Amount Caught], [Fraud Amount] )
Alerts per Day      = DIVIDE ( [Alerts], DISTINCTCOUNT ( Summary[day] ) )
High Priority Alerts = CALCULATE ( COUNTROWS ( Alerts ), Alerts[priority] = "High" )
```

Format the % measures as percentages and the amounts with thousands separators.

## 3. Pages

1. **Overview** - cards: Fraud Cases, Alerts, Precision %, Recall %, Money Caught %.
   Column chart: Fraud Cases and Alerts by Days[Day]. Column chart: Fraud Rate % by Hours[Hour].
   Slicer: type.
2. **Rules** - bar chart from RulePerformance (precision_pct and recall_pct by rule).
   Line chart from Thresholds (precision_pct and recall_pct by threshold, one small multiple per
   scenario). A short text box explaining why R1 is shown with and without.
3. **Alert queue** - table from Alerts sorted by risk_score: txn_id, day, hour, type, amount,
   priority, reasons, outcome. Slicers: priority, day, outcome. This is the analyst's work list.
4. **Missed fraud** - table from Missed with a text box on why they were missed (see docs/cases.md, Case 3).

## 4. Check it

The Overview cards must match docs/results/02_evaluation.md: 8,213 fraud cases, 9,625 alerts,
precision 85.0%, recall 99.6%.
