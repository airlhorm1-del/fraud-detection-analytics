# Investigation cases

Four alerts written up the way a fraud analyst would, to show the reasoning behind the rules.
All values are real rows from the data (look them up by `txn_id` in `powerbi/data/alerts.csv`
or `missed_fraud.csv`). Money amounts are in the simulation's currency units.

---

## Case 1 - High priority, confirmed fraud: the account takeover

| | |
|---|---|
| Transaction | 6281794, day 28 at 02:00, TRANSFER of **9,996,886.64** |
| Sender | C429282035: balance 9,996,886.64 before, **0.00 after** |
| Receiver | C1318460385: balance 0.00 before **and 0.00 after**, never seen before |
| Risk score | **105**: R1 account emptied, R2 receiver unchanged, R3 night time, R4 large amount, R6 new receiver |

**What the analyst sees.** At two in the morning the customer's whole balance leaves in one
transfer, to an account that has never appeared before and whose balance does not move. Five
warning signs at once.

**Following the money.** In the same hour, another account (C887830623, txn 6281795) cashes out
**exactly 9,996,886.64**, also labelled fraud. This is the classic chain: take over an account,
transfer everything to a "mule" account, cash out immediately. The data does not link the two
accounts directly, but matching on *same amount, same hour* finds the partner for 4,078 of the
4,097 fraudulent transfers.

**Action in real life.** Block the sender's account and the cash-out account, contact the
customer through a known channel, and try to stop or recover the cash-out.

---

## Case 2 - Low priority, false alarm: big and late, but genuine

| | |
|---|---|
| Transaction | 3960278, day 13 at 02:00, TRANSFER of **28,617,438.58** |
| Sender | C765197285: balance shows 0.00 before and after |
| Receiver | C1912929673: balance 42,684,157.98 before, **71,301,596.56 after** (the money arrived) |
| Risk score | **30**: R3 night time, R4 large amount |

**What the analyst sees.** A very large transfer at night, so it reaches the alert threshold. But
the receiver is an established account with a large balance that clearly received the money,
it is not new, and nothing was emptied.

**Decision.** Closed as genuine.

**Lesson.** In this data the Low band (score 30-39) is almost all false alarms: 1,410 of 1,411.
A team would review it last, or tighten it (for example, only alert on night + large amount when
a third sign is present). But in the stress test without R1, alerts scoring 30-39 contain about half
of the fraud that is still caught (2,203 of 4,479), so the band should not simply be switched off.

---

## Case 3 - Missed fraud: when the data itself is broken

| | |
|---|---|
| Transaction | 138560, day 1 at 10:00, TRANSFER of **1,933,920.80** |
| Sender | C1706582969: balance **0.00 before and 0.00 after** |
| Receiver | C461905695: balance 1,283,762.85 before, 3,217,683.65 after |
| Risk score | **15**: R4 large amount only (no alert) |

**Why it was missed.** The sender "sends" almost two million from an account that shows a zero
balance, which is impossible, so the balance data is wrong here. Because of that, R1 (account
emptied) cannot fire. It happened in the daytime, to a known receiver, so nothing else fired either.

**Why not simply add a rule "sender balance is zero"?** Because 47% of genuine money-out
transactions in this data also show a zero starting balance. The rule would raise over a million
false alarms.

**Lesson.** Detection is only as good as the data. 31 of 8,213 frauds were missed, 19 of them with
no rule firing at all. Next steps: the "same amount cashed out in the same hour" pattern from
Case 1 as a seventh rule, or a simple model trained on the labelled data.

---

## Case 4 - Medium priority, confirmed fraud: the zero-amount "test"

| | |
|---|---|
| Transaction | 3760290, day 12 at 14:00, CASH_OUT of **0.00** |
| Sender | C539112012: balance 0.00 |
| Receiver | C1106468520: balance 538,547.63, unchanged |
| Risk score | **40**: R5 zero amount |

**What the analyst sees.** A cash-out of nothing. There are 16 of these in the data and every one
is labelled fraud.

**Why it matters.** Fraudsters often send a zero or tiny "test" transaction to check that a
stolen account or card works before the real theft. In real life you would look at what the same
account did next and put a hold on it.
