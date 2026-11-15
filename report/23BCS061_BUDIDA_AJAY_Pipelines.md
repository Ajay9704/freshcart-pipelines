# From Git to Gold

**Student:** Budida Ajay  
**Roll number:** 23BCS061  
**Status:** Working draft — FreshCart baseline completed; Snowflake follow-up experiments, hosted CI/Mage/RabbitMQ evidence, and screenshots remain pending.

## Part A — Git and CI/CD

### A1. Repository

The local repository is organized into `elt/`, `iris_project/`, `stream/`,
`tests/`, and `.github/workflows/`. The public GitHub URL and GitHub Actions
screenshots must be added after the repository is published.

Current local history:

```text
0bb02bf Document pipeline run instructions
199b3e4 Test RabbitMQ message acknowledgements
7e071b5 Harden FreshCart notebook and add checks
05ac388 Add RabbitMQ dispatcher and drivers
84cf386 Build Mage Iris pipeline blocks
4cf16ed Set up assignment repo and CI
```

### A2. Where Git commands act

| Command | Where the change happens | What exactly happens |
|---|---|---|
| `git init` | Working folder / local repository | Creates the `.git` metadata directory so Git can track this folder. |
| `git add train.py` | Staging area | Stages the current contents of `train.py` for the next commit. |
| `git commit -m "msg"` | Local repository | Saves the staged snapshot as a commit in the local history. |
| `git remote add origin URL` | Local repository configuration | Records the remote URL under the name `origin`; it does not upload files. |
| `git push -u origin main` | Remote Git repository | Uploads local commits to the remote `main` branch and sets its upstream. |
| `git pull origin main` | Local repository and working folder | Fetches remote commits and integrates them into the current local branch. |

After `git commit`, a teammate cannot see the code on GitHub because the commit
exists only in the local repository until it is pushed.

### A3. CI

`tests/test_prepare_data.py` checks that the Iris transformer returns exactly
120 training rows and 30 test rows. The GitHub Actions workflow runs pytest on
pushes and pull requests using Python 3.12. The required green and intentionally
red GitHub Actions screenshots are pending the remote repository setup.

## Part B — FreshCart ELT on Snowflake

The notebook in `elt/freshcart_elt.ipynb` now reads credentials from Colab
Secrets and contains the `unsupported_currency` validation and the sixth
future-order quality check.

### B1. Baseline

The pipeline completed successfully. The Snowflake connector printed proxy
configuration warnings, but all SQL stages and quality checks completed.

| Check | Expected | Observed |
|---|---:|---:|
| Raw order rows in bronze after one run | 8 | 8 |
| Rows in `silver.orders_clean` | 6 | 6 |
| Quarantined orders | 2 | 2: ORD-1004, ORD-1006 |
| Rows in `silver.orders_dedup` | 4 | 4 |
| Gold orders | 4 | 4 |
| Gold revenue | ₹7,785.00 | ₹7,785.00 |
| Gold loyalty points | 126 | 126 |
| Share rejected | 25% | 25% |

The sixth check, future-dated orders in silver, also returned 0 (`OK`). Save
screenshots from the Colab run and append them to the final report.

### B2. Record trace

In bronze, the website copy of ORD-1003 is a flat object with fields such as
`order_id`, `cust_email`, `amount`, and `updated_at`; its `amount` is null. The
mobile copy is nested and uses `orderId`, `customer.email`, `total.value`, and
`updatedAt`; its amount is ₹2,100 and its update time is later.
`SQL_10_ORDERS_CLEAN` maps the website fields directly and maps the mobile
fields from their nested JSON paths into the same normalized columns. A null
amount is allowed, so both versions can be cleaned. In `SQL_20_ORDERS_DEDUP`,
`QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY updated_at DESC,
ingest_seq DESC) = 1` keeps the newer mobile copy. Gold calculates its amount
as ₹2,100 × INR rate 1.0 = ₹2,100; Meera's Platinum multiplier is 3, so
`FLOOR(2100 / 100) × 3 = 63` loyalty points.

For ORD-1005, Priya earns Gold points because its order date, 2026-09-03, is
the start date of her Gold SCD2 row. ORD-1001 is dated 2026-09-01, within her
Silver row. The point-in-time join uses matching email and
`order_date BETWEEN valid_from AND valid_to` in `SQL_40_GOLD`; the
`ref.tier_multiplier` table is joined with `m.tier = c.tier`.

### B3. Currency validation

Before adding the rule, ORD-1006's reasons were `bad_email` and `bad_pincode`.
The assignment's requested validation now adds `unsupported_currency`, and
the baseline run showed all three reasons for ORD-1006. Gold totals do not
change because this order already fails validation and is quarantined rather
than included in `silver.orders_clean` and gold. On a rerun, the quarantine
`INSERT` uses `NOT EXISTS` on source, null-safe order ID, and the raw row's
`UPDATED_AT` timestamp to avoid inserting the same source/order/version again.

### B4. SCD2 and idempotency

The following prediction was recorded before adding the new event and running
the pipeline:

| Quantity | Prediction | Actual |
|---|---:|---:|
| Rows for CUST-02 in `dim.customers_scd2` | 2 | 2 |
| Tier used for ORD-1002 | Gold | Gold |
| Loyalty points for ORD-1002 | 70 | 70 |
| Total gold loyalty points | 161 | 161 |
| Gold rows whose `published_at` changed | 1 | 1 |

Calculation: ORD-1002 is USD 42.50 on 2026-09-01, when the daily FX rate is
83.20 INR/USD, so its INR amount is ₹3,536. Gold's multiplier is 2;
`FLOOR(3536 / 100) × 2 = 70` points, 35 more than its baseline Silver value
of 35. The predicted new total is 126 + 35 = 161. The observed SCD2 rows are
Silver from 2024-01-15 through 2026-08-14 and Gold from 2026-08-15 onward.
The run reported 4 gold orders, ₹7,785.00 revenue, and 161 points. Comparing
before and after `published_at` values showed that only ORD-1002 changed.

Bronze still grows by eight order rows on each run because every extracted
website/mobile copy is appended. The final gold `MERGE` matches by `order_id`
and updates a matched row only when its `row_hash` changes. With identical
inputs, the hash is unchanged, so gold totals and `published_at` stay stable;
the new Arjun event changes ORD-1002's tier-dependent hash and should update
that one row.

After a subsequent rerun, the totals query displayed 80 bronze order rows,
2 quarantine rows, 4 gold orders, ₹7,785.00 revenue, and 161 points. All four
Gold `published_at` timestamps matched the values captured immediately before
that rerun, confirming that the repeated input did not update Gold.

### B5. Quality check and ELT explanation

The sixth check is `COUNT_IF(order_date > CURRENT_DATE())` over
`silver.orders_dedup`; it returned 0 in the baseline run. For the intentional
failure demonstration, a temporary 2099-dated order was added. The screenshot
showed `future-dated orders in silver = 1 PROBLEM`; it also showed one order
with an amount but no FX rate, and the temporary order appeared in gold,
confirming that quality checks report problems but do not stop the pipeline.
After removing the mock order and rerunning, the future-date check returned
`0 OK`, gold returned to 4 orders, and the total remained ₹7,785.00 and 161
points. The run log also confirmed the web input returned to its original six
records (plus two mobile records). Add the failure and cleanup screenshots to
the report appendix.

FreshCart is a good fit for ELT because the original web and mobile JSON can
be loaded into Snowflake first, then standardized, validated, deduplicated,
and enriched with SQL where the data is stored. Keeping the raw records in
bronze also makes it possible to revise the transformations and reprocess
without extracting the source data again. ETL would be preferable if data
must be masked or filtered before it is allowed into the warehouse, for
example when sensitive fields cannot be landed in raw form for compliance.
Rewrite this explanation in your own words and replace the ETL example with
the specific situation your instructor used in the lecture, if different.

## Part C — Mage Iris pipeline

The Mage-compatible blocks and pipeline metadata are in `iris_project/`. The
standalone pytest suite passed locally: **6 passed**. Direct block execution
with the supplied fixed split produced these test accuracies:

| `max_depth` | Test accuracy | 80% block check |
|---:|---:|---|
| 1 | 0.633 | Fails |
| 2 | 0.967 | Passes |
| 3 | 1.000 | Passes |
| 4 | 1.000 | Passes |
| 5 | 1.000 | Passes |

For `max_depth=3`, the locally evaluated confusion matrix was:

```text
           predicted
actual      0   1   2
       0   10   0   0
       1    0   9   0
       2    0   0  11
```

The metric values were accuracy 1.000, precision 1.000, recall 1.000, and
F1-score 1.000. These are local block results, not a Mage CLI or UI run.
Mage run logs, CSV-gating observations, and the UI graph screenshot remain
pending.

## Part D — RabbitMQ food-order stream

### D1. Routing table

| # | Routing key | Receiving queues |
|---:|---|---|
| 1 | `bangalore.koramangala.food` | Ravi, Meena, Control |
| 2 | `bangalore.indiranagar.ride` | Priya, Arjun, Control |
| 3 | `bangalore.whitefield.ride` | Arjun, Control |
| 4 | `chennai.tnagar.food` | Karthik |
| 5 | `chennai.whitefield.ride` | dropped |
| 6 | `bangalore.koramangala` | Control |

`*` consumes exactly one routing-key word, so the three-word driver patterns do
not match the two-word key in row 6. `#` consumes zero or more words, so
`bangalore.#` does match it.

### D2–D3. Implementation and acknowledgements

The dispatcher and driver scripts are in `stream/`. Unit tests verify that
every tenth payload omits `zone`, that such deliveries use NACK with
`requeue=False`, and that complete deliveries are ACKed. A live broker run,
console evidence, and the two-minute routing demonstration remain pending.

## Part E — Integration and reflection

```text
Git working tree -> staging -> local commits -> GitHub -> CI tests
                                                    |
             +------------------+------------------+-----------------+
             |                  |                                    |
       FreshCart ELT        Mage Iris                         RabbitMQ stream
       bronze -> gold       data -> model                      dispatcher -> drivers
```

The personal reflection and viva answers should be completed after the
remaining hosted runs. One local issue encountered during development was that
pytest collected an imported Mage test block as a test function; importing it
under a non-`test_` alias resolved the collection error. Rewrite this reflection
in your own words and include the actual debugging steps you took.
