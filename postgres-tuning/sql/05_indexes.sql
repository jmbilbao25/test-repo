-- Step 2: the indexes, one per query.
--
-- Q1 filters on a range of payment_date, so a plain B-tree on that column is
-- enough.
CREATE INDEX IF NOT EXISTS idx_payment_payment_date
    ON payment (payment_date);

-- Q2 filters on customer_id and then sorts by payment_date descending. A
-- composite index in that order lets the index satisfy both: the leading
-- column narrows to the customer, and because the second column is already
-- stored in the requested direction the sort disappears entirely.
CREATE INDEX IF NOT EXISTS idx_payment_customer_date
    ON payment (customer_id, payment_date DESC);

ANALYZE payment;

\echo
\echo === indexes on payment ===
SELECT indexname, pg_size_pretty(pg_relation_size(indexname::regclass)) AS size
FROM pg_indexes
WHERE tablename = 'payment'
ORDER BY indexname;
