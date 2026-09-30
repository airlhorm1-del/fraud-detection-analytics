# Decision log

One entry per significant choice: what was decided, why, and what it costs.

## 001 - Dataset: PaySim
Public, synthetic mobile money transactions (6.3 million rows, 31 days) with fraud labels,
modelled on a mobile money service in an African country. Close to the owner's banking
background and free to publish. Cost: it is simulated, so some patterns are cleaner than real
life (see 006), and there are no customer details, devices or locations.

## 002 - Tools: DuckDB and Python (uv), Power BI for the dashboard
6.3 million rows is too many for Excel (limit about 1 million). DuckDB runs SQL on the full data
from Python with no database server. Power BI gets small summary and alert tables, not all rows.

## 003 - Rules only on money-out transactions (TRANSFER, CASH_OUT)
All fraud in the data is one of these two types; the other types contain none. In account
takeover fraud the money has to leave the account, so this is also the realistic place to look.

## 004 - Time: step 1 is taken as 00:00-00:59 on day 1
The data only numbers the hours. Customer activity collapses in hours 0-6 under this reading,
which matches night-time, so the assumption looks right, but it is an assumption.

## 005 - Six rules with points, alert at 30, three priorities
R1 account emptied (40), R2 receiver balance unchanged (25), R3 night time (15), R4 amount of
1,000,000 or more (15), R5 zero amount (40), R6 new receiver (10). Alert at a score of 30 or more;
priority High 60+, Medium 40-59, Low 30-39. Points and threshold were set from the profile and
the per-rule results, keeping alert volume manageable (about 310 a day). Points live in one place
(the rule_catalogue table in sql/20_rules.sql).

## 006 - R1 is "too good", so every result is also shown without it
R1 catches 97.6% of fraud with zero false alarms. That happens because in this simulation genuine
customers never empty their account in one go and their balances often do not add up, while
fraud balances do. Real data would not be this clean. R1 stays (emptying an account is a real
warning sign), but all results are also reported without R1 as a stress test: 54.5% of fraud
caught, 75.6% of alerts real.

## 007 - No train/test split
The rules were chosen by reasoning from the data profile, not fitted by an algorithm, so the
risk of overfitting is small. It still exists (thresholds were checked on the same month), and a
next step would be to set thresholds on the first weeks and test on the last ones.

## 008 - Rules that the data cannot support were dropped
"Many transactions in a short time" needs repeat customers, but only 9,298 of 6.35 million
senders appear more than once. Linking a transfer to the receiver's later cash-out by account
finds only 3 cases, because the simulation does not link them; matching on same amount and same
hour does (4,078 of 4,097), which is noted as the next rule to add.
