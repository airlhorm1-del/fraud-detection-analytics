-- Stage 4 - fraud rules and risk score.
-- Rules apply to money-out transactions (TRANSFER and CASH_OUT): in this data all fraud is an
-- account takeover where the money is moved out, and the other types contain no fraud at all.
-- Each rule adds points; the total is the risk score. Score >= 30 creates an alert.
-- Priority for the investigation queue: High >= 60, Medium 40-59, Low 30-39.
-- Rule points and thresholds are set in the rule_catalogue table below, so they live in one place.

CREATE OR REPLACE TABLE rule_catalogue AS
SELECT * FROM (VALUES
    ('R1', 'account_emptied',    'The whole sender balance leaves in one transaction',                  40),
    ('R2', 'receiver_unchanged', 'Receiving account shows no balance before or after (money vanishes)', 25),
    ('R3', 'night_time',         'Between 00:00 and 06:59, when normal customer activity is very low',  15),
    ('R4', 'large_amount',       'Amount of 1,000,000 or more',                                         15),
    ('R5', 'zero_amount',        'Zero-amount transaction (a test before the real theft)',               40),
    ('R6', 'new_receiver',       'First time this receiving account appears',                           10)
) AS t(rule_id, rule_name, description, points);

CREATE OR REPLACE TABLE scored AS
WITH receivers AS (
    SELECT txn_id,
           row_number() OVER (PARTITION BY receiver_id ORDER BY step, txn_id) = 1 AS first_seen
    FROM transactions
),
flags AS (
    SELECT t.*,
        is_money_out AND sender_balance_before > 0 AND abs(amount - sender_balance_before) < 0.01 AS r1_account_emptied,
        is_money_out AND amount > 0 AND receiver_balance_before = 0 AND receiver_balance_after = 0 AS r2_receiver_unchanged,
        is_money_out AND hour BETWEEN 0 AND 6                                                  AS r3_night_time,
        is_money_out AND amount >= 1000000                                                     AS r4_large_amount,
        is_money_out AND amount = 0                                                            AS r5_zero_amount,
        is_money_out AND r.first_seen                                                          AS r6_new_receiver
    FROM transactions t JOIN receivers r USING (txn_id)
),
points AS (SELECT rule_name, points FROM rule_catalogue)
SELECT f.*,
      r1_account_emptied::INT    * (SELECT points FROM points WHERE rule_name = 'account_emptied')
    + r2_receiver_unchanged::INT * (SELECT points FROM points WHERE rule_name = 'receiver_unchanged')
    + r3_night_time::INT         * (SELECT points FROM points WHERE rule_name = 'night_time')
    + r4_large_amount::INT       * (SELECT points FROM points WHERE rule_name = 'large_amount')
    + r5_zero_amount::INT        * (SELECT points FROM points WHERE rule_name = 'zero_amount')
    + r6_new_receiver::INT       * (SELECT points FROM points WHERE rule_name = 'new_receiver') AS risk_score
FROM flags f;

-- The same score without R1, to see how the rules would perform if the "account emptied"
-- pattern were not so clean (in this simulated data it is unrealistically perfect).
CREATE OR REPLACE TABLE scored_final AS
SELECT *,
    risk_score - r1_account_emptied::INT * (SELECT points FROM rule_catalogue WHERE rule_id = 'R1') AS risk_score_without_r1,
    risk_score >= 30 AS is_alert,
    CASE WHEN risk_score >= 60 THEN 'High'
         WHEN risk_score >= 40 THEN 'Medium'
         WHEN risk_score >= 30 THEN 'Low' END AS priority,
    concat_ws(', ',
        CASE WHEN r1_account_emptied    THEN 'R1 account emptied' END,
        CASE WHEN r2_receiver_unchanged THEN 'R2 receiver unchanged' END,
        CASE WHEN r3_night_time         THEN 'R3 night time' END,
        CASE WHEN r4_large_amount       THEN 'R4 large amount' END,
        CASE WHEN r5_zero_amount        THEN 'R5 zero amount' END,
        CASE WHEN r6_new_receiver       THEN 'R6 new receiver' END) AS reasons
FROM scored;

DROP TABLE scored;
ALTER TABLE scored_final RENAME TO scored;
