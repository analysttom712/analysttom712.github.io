-- Shared views the reports build on (synthetic data only).

-- Billing by month, rebuilt from the effective-dated enrollment ranges:
-- a person is billed in every month whose first day falls inside one of their ranges.
DROP VIEW IF EXISTS billing_month;
CREATE VIEW billing_month AS
SELECT
    m.month_start AS report_month,
    e.person_number,
    e.worker_type,
    e.payment_method,
    e.division,
    e.medical,
    e.dental,
    e.total_premium,
    e.medicare_eligible,
    e.dependent_turning_26,
    CASE e.worker_type WHEN 'Retiree' THEN 1 ELSE 2 END AS account_number
FROM benefit_enrollment_history e
JOIN month_calendar m
  ON m.month_start BETWEEN e.effective_start_date AND e.effective_end_date;

-- The assignment that was in effect on a given day, for any person: join on the date you need.
DROP VIEW IF EXISTS assignment_current;
CREATE VIEW assignment_current AS
SELECT * FROM assignment_history WHERE effective_end_date = '9999-12-31';

-- Journal entries grouped the way the roll-forward needs them
DROP VIEW IF EXISTS ledger_posting_grouped;
CREATE VIEW ledger_posting_grouped AS
SELECT
    lp.*,
    CASE
        WHEN description = 'Premium billing'   THEN 'Billing'
        WHEN description LIKE 'Deposit - %'    THEN 'Deposits'
        WHEN description = 'Check deposit'     THEN 'Checks'
        WHEN description LIKE 'Retro%'         THEN 'Retro adjustments'
        ELSE description                       -- Beginning balance, Off-cycle, Return, Refund
    END AS entry_group,
    CASE WHEN description LIKE 'Deposit - %' THEN substr(description, 11) END AS deposit_source,
    ROUND(debit - credit, 2) AS net
FROM ledger_posting lp;

-- One row per person per month: what was billed against everything received, from every source.
-- Same logic as the Power BI table 'Fact Person Month'.
DROP VIEW IF EXISTS person_month;
CREATE VIEW person_month AS
WITH billed AS (
    SELECT person_number, report_month,
           SUM(total_premium) AS billed,
           MAX(worker_type) AS worker_type,
           MAX(payment_method) AS payment_method
    FROM billing_month
    GROUP BY person_number, report_month
),
drafted AS (
    SELECT person_number, coverage_month AS report_month, SUM(amount) AS drafted
    FROM premium_receipt
    WHERE person_number IS NOT NULL
    GROUP BY person_number, coverage_month
),
logged AS (                                   -- 2025 payment log, refunds excluded
    SELECT person_number, date(action_date, 'start of month') AS report_month,
           SUM(CASE WHEN action = 'Check'     THEN amount ELSE 0 END) AS log_paid,
           SUM(CASE WHEN action = 'Off-cycle' THEN amount ELSE 0 END) AS off_cycle,
           SUM(CASE WHEN action = 'Return'    THEN amount ELSE 0 END) AS returns
    FROM payment_log
    WHERE action_date BETWEEN '2025-01-01' AND '2025-12-31'
      AND action <> 'Refund'
    GROUP BY person_number, date(action_date, 'start of month')
),
dep_life AS (
    SELECT person_number, report_month, SUM(debit) AS dependent_life
    FROM ledger_detail WHERE account_number = 3
    GROUP BY person_number, report_month
),
gl_billed AS (
    SELECT person_number, report_month, SUM(debit) AS gl_billed
    FROM ledger_detail WHERE account_number <> 3
    GROUP BY person_number, report_month
),
last_billed AS (
    SELECT person_number, MAX(report_month) AS last_billed_month
    FROM billed GROUP BY person_number
),
known AS (                                    -- a person's latest worker type and payment method
    SELECT b.person_number, b.worker_type, b.payment_method
    FROM billed b
    JOIN last_billed lb ON lb.person_number = b.person_number AND lb.last_billed_month = b.report_month
),
keys AS (
    SELECT person_number, report_month FROM billed
    UNION SELECT person_number, report_month FROM drafted
    UNION SELECT person_number, report_month FROM logged
    UNION SELECT person_number, report_month FROM dep_life
),
pm AS (
    SELECT
        k.person_number,
        k.report_month,
        COALESCE(b.worker_type, kn.worker_type) AS worker_type,
        COALESCE(b.payment_method, kn.payment_method) AS payment_method,
        COALESCE(b.billed, 0) AS billed,
        COALESCE(d.drafted, 0) AS drafted,
        COALESCE(l.log_paid, 0) AS log_paid,
        COALESCE(l.off_cycle, 0) AS off_cycle,
        COALESCE(l.returns, 0) AS returns,
        COALESCE(dl.dependent_life, 0) AS dependent_life,
        COALESCE(g.gl_billed, 0) AS gl_billed,
        lb.last_billed_month,
        p.date_of_death
    FROM keys k
    LEFT JOIN billed b       ON b.person_number = k.person_number AND b.report_month = k.report_month
    LEFT JOIN drafted d      ON d.person_number = k.person_number AND d.report_month = k.report_month
    LEFT JOIN logged l       ON l.person_number = k.person_number AND l.report_month = k.report_month
    LEFT JOIN dep_life dl    ON dl.person_number = k.person_number AND dl.report_month = k.report_month
    LEFT JOIN gl_billed g    ON g.person_number = k.person_number AND g.report_month = k.report_month
    LEFT JOIN last_billed lb ON lb.person_number = k.person_number
    LEFT JOIN known kn       ON kn.person_number = k.person_number
    LEFT JOIN person p       ON p.person_number = k.person_number
),
money AS (
    SELECT pm.*,
           ROUND(drafted + log_paid + off_cycle + returns, 2) AS paid,
           ROUND(drafted + log_paid + off_cycle + returns - billed, 2) AS difference,
           CASE worker_type WHEN 'Retiree' THEN 1 ELSE 2 END AS account_number
    FROM pm
),
classified AS (
    -- Planted causes, synthetic scenario. Order matters: the first rule that fits wins,
    -- same as the DAX SWITCH ( TRUE (), ... )
    SELECT money.*,
        CASE
            WHEN report_month > '2025-12-31' THEN 'Prepaid next year'
            WHEN billed > 0 AND date_of_death IS NOT NULL
                 AND report_month > date(date_of_death, 'start of month', '+1 month', '-1 day') THEN 'Billed after death'
            WHEN billed > 0 AND gl_billed = 0 THEN 'Costing not keyed (GL missing)'
            WHEN billed > 0 AND paid <= 0 AND COALESCE(last_billed_month, '') < '2025-12-01'
                 AND COALESCE(payment_method, '') <> 'Annual payment' THEN 'Retro-canceled, not adjusted'
            WHEN billed = 0 AND drafted > 0 THEN 'Drafted after removal'
            WHEN drafted > 0 AND payment_method = 'Monthly check' THEN 'Drafted in error'
            WHEN payment_method = 'Annual payment' THEN 'Annual payment (timing)'
            WHEN billed = 0 AND paid > 0 THEN 'Received, not billed'
            WHEN returns < 0 AND difference < 0 THEN 'Returned draft'
            WHEN difference = 0 THEN 'Ties'
            WHEN ROUND(difference - dependent_life, 2) = 0 THEN 'Dependent life in receipt'
            WHEN off_cycle > 0 AND difference > 0 THEN 'Off-cycle catch-up'
            WHEN paid = 0 AND billed > 0 THEN 'Missed payment'
            WHEN difference < 0 THEN 'Short or unpaid'
            WHEN difference > 0 THEN 'Overpaid'
            ELSE 'Review'
        END AS cause
    FROM money
)
SELECT
    classified.*,
    CASE cause
        WHEN 'Billed after death'             THEN 'Retro adjustment; refund due'
        WHEN 'Drafted in error'               THEN 'Return the draft'
        WHEN 'Drafted after removal'          THEN 'Refund the payer'
        WHEN 'Costing not keyed (GL missing)' THEN 'Post the missing billing; correct the setup'
        WHEN 'Retro-canceled, not adjusted'   THEN 'Post the retro reversal'
        WHEN 'Prepaid next year'              THEN 'None: 2026 premium'
        WHEN 'Annual payment (timing)'        THEN 'Check the yearly total'
        WHEN 'Received, not billed'           THEN 'Find out why; refund or bill'
        WHEN 'Returned draft'                 THEN 'Collect, or cancel'
        WHEN 'Dependent life in receipt'      THEN 'None: belongs in account 3'
        WHEN 'Off-cycle catch-up'             THEN 'None: catch-up payment'
        WHEN 'Missed payment'                 THEN 'Collect, or cancel'
        WHEN 'Short or unpaid'                THEN 'Collect the balance'
        WHEN 'Overpaid'                       THEN 'Apply or refund'
        WHEN 'Ties'                           THEN 'None'
        ELSE 'Review'
    END AS next_step,
    CASE WHEN cause IN ('Ties', 'Dependent life in receipt', 'Off-cycle catch-up',
                        'Annual payment (timing)', 'Prepaid next year') THEN 'No' ELSE 'Yes' END AS needs_action
FROM classified;
