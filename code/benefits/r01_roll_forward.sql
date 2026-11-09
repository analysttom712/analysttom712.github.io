-- Report 1: Roll-forward by account and month (synthetic data only)
-- Opening + every kind of entry = ending. The last column must be 0.00 on every row.
-- Parameter :p_month = a month start ('2025-03-01'), or NULL for every month.
WITH by_month AS (
    SELECT
        account_number,
        report_month,
        SUM(net) AS total_net,
        SUM(CASE WHEN entry_group <> 'Beginning balance' THEN net ELSE 0 END) AS activity,
        SUM(CASE WHEN entry_group = 'Billing'           THEN net ELSE 0 END) AS billing,
        SUM(CASE WHEN entry_group = 'Deposits'          THEN net ELSE 0 END) AS deposits,
        SUM(CASE WHEN entry_group = 'Checks'            THEN net ELSE 0 END) AS checks,
        SUM(CASE WHEN entry_group = 'Off-cycle'         THEN net ELSE 0 END) AS off_cycle,
        SUM(CASE WHEN entry_group = 'Return'            THEN net ELSE 0 END) AS returns,
        SUM(CASE WHEN entry_group = 'Refund'            THEN net ELSE 0 END) AS refunds,
        SUM(CASE WHEN entry_group = 'Retro adjustments' THEN net ELSE 0 END) AS retro_adjustments
    FROM ledger_posting_grouped
    GROUP BY account_number, report_month
),
running AS (
    SELECT by_month.*,
           SUM(total_net) OVER (PARTITION BY account_number ORDER BY report_month) AS ending_balance
    FROM by_month
)
SELECT
    account_number,
    report_month,
    ROUND(ending_balance - activity, 2) AS opening_balance,
    ROUND(billing, 2) AS billing,
    ROUND(deposits, 2) AS deposits,
    ROUND(checks, 2) AS checks,
    ROUND(off_cycle, 2) AS off_cycle,
    ROUND(returns, 2) AS returns,
    ROUND(refunds, 2) AS refunds,
    ROUND(retro_adjustments, 2) AS retro_adjustments,
    ROUND(ending_balance, 2) AS ending_balance,
    ROUND((ending_balance - activity) + billing + deposits + checks + off_cycle + returns + refunds
          + retro_adjustments - ending_balance, 2) AS check_should_be_zero
FROM running
WHERE :p_month IS NULL OR report_month = :p_month
ORDER BY account_number, report_month;
