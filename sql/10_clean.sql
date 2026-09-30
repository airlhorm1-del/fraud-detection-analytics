-- Stage 3 - clean and prepare.
-- Nothing is deleted: the data has no missing values and no duplicate rows (see the profile).
-- Cleaning here means making the data consistent and readable:
--   * consistent snake_case names (PaySim mixes "Org" and "Orig" in its column names);
--   * readable time fields (day and hour of the 31-day simulation; step 1 = day 1, 00:00-00:59);
--   * receiver kind (C = customer, M = merchant);
--   * flags for balances that do not add up (kept, not fixed: they are part of the data's reality);
--   * the simulator's own flag renamed so nobody mistakes it for our rules.

CREATE OR REPLACE TABLE transactions AS
SELECT
    txn_id,
    step,
    (step - 1) // 24 + 1                          AS day,
    (step - 1) % 24                               AS hour,
    type,
    type IN ('TRANSFER', 'CASH_OUT')              AS is_money_out,
    amount,
    nameOrig                                      AS sender_id,
    oldbalanceOrg                                 AS sender_balance_before,
    newbalanceOrig                                AS sender_balance_after,
    nameDest                                      AS receiver_id,
    CASE WHEN nameDest LIKE 'M%' THEN 'Merchant' ELSE 'Customer' END AS receiver_kind,
    oldbalanceDest                                AS receiver_balance_before,
    newbalanceDest                                AS receiver_balance_after,
    abs(oldbalanceOrg - amount - newbalanceOrig) <= 0.01                 AS sender_balance_adds_up,
    CASE WHEN nameDest LIKE 'M%' THEN NULL
         ELSE abs(oldbalanceDest + amount - newbalanceDest) <= 0.01 END  AS receiver_balance_adds_up,
    isFraud                                       AS is_fraud,
    isFlaggedFraud                                AS simulator_flag
FROM raw_transactions;
