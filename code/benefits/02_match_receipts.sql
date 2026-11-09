-- Matches every receipt line to a person (synthetic data only).
-- Synthetic data: SSNs are 900-range; the vendors show only the last 4.
--
-- Internal ACH sends the person number. The vendors don't, and both mask the SSN to the last 4:
--   tier 1: last 4 + first name + last name
--   tier 2: last 4 + last name (catches a nickname or a typo in the first name)
-- A line is matched only when its best tier finds exactly one person. Anything else stays
-- unmatched with the reason, and shows up on the load checks report.

CREATE INDEX IF NOT EXISTS ix_person_ssn_last4 ON person (substr(ssn, 8, 4));

DROP TABLE IF EXISTS premium_receipt;
CREATE TABLE premium_receipt AS
WITH candidates AS (
    SELECT s.rowid AS line_id, p.person_number, 1 AS tier
    FROM receipt_staging s
    JOIN person p
      ON substr(p.ssn, 8, 4) = s.ssn_last4
     AND upper(p.first_name) = upper(s.first_name)
     AND upper(p.last_name) = upper(s.last_name)
    WHERE s.source IN ('Vendor 1', 'Vendor 2')
    UNION ALL
    SELECT s.rowid, p.person_number, 2
    FROM receipt_staging s
    JOIN person p
      ON substr(p.ssn, 8, 4) = s.ssn_last4
     AND upper(p.last_name) = upper(s.last_name)
    WHERE s.source IN ('Vendor 1', 'Vendor 2')
),
best_tier AS (
    SELECT line_id, MIN(tier) AS tier FROM candidates GROUP BY line_id
),
best AS (
    SELECT c.line_id, c.tier, MIN(c.person_number) AS person_number, COUNT(*) AS candidates
    FROM candidates c
    JOIN best_tier b ON b.line_id = c.line_id AND b.tier = c.tier
    GROUP BY c.line_id, c.tier
)
SELECT
    s.source,
    s.file_name,
    s.coverage_month,
    s.draft_date,
    date(s.draft_date, 'start of month') AS draft_month,
    CASE
        WHEN s.source = 'Internal ACH' THEN s.person_number
        WHEN b.candidates = 1 THEN b.person_number
    END AS person_number,
    CASE
        WHEN s.source = 'Internal ACH' THEN 'Person number'
        WHEN b.candidates = 1 AND b.tier = 1 THEN 'SSN last 4 + first and last name'
        WHEN b.candidates = 1 THEN 'SSN last 4 + last name'
        WHEN b.candidates > 1 THEN 'Unmatched: more than one candidate'
        ELSE 'Unmatched: no candidate'
    END AS match_method,
    s.first_name,
    s.last_name,
    s.amount
FROM receipt_staging s
LEFT JOIN best b ON b.line_id = s.rowid;
