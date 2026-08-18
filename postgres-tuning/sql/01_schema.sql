-- Step 1: what the restored sample database contains.
\echo === tables ===
\dt
\echo
\echo === row counts of the tables this report touches ===
SELECT 'payment'  AS table_name, count(*) FROM payment
UNION ALL SELECT 'rental',   count(*) FROM rental
UNION ALL SELECT 'customer', count(*) FROM customer
UNION ALL SELECT 'film',     count(*) FROM film
ORDER BY 1;
