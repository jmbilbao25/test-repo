-- Step 3: exercise both, including the paths that are supposed to fail.
\set ON_ERROR_STOP off

\echo === 1. add a customer (expect: a new id) ===
SELECT add_customer(1::smallint, 'John', 'Bilbao',
                    'john.bilbao@example.com', 5::smallint) AS new_customer_id;

\echo
\echo === 2. the same email again (expect: rejected, unique_violation) ===
SELECT add_customer(1::smallint, 'Johnny', 'Bilbao',
                    'JOHN.BILBAO@EXAMPLE.COM', 5::smallint);

\echo
\echo === 3. a malformed email (expect: rejected, check_violation) ===
SELECT add_customer(1::smallint, 'Bad', 'Address',
                    'not-an-email', 5::smallint);

\echo
-- CALL will not accept a subquery as an argument, so the id is fetched into a
-- psql variable first.
SELECT customer_id AS cid FROM customer
 WHERE email = 'john.bilbao@example.com' \gset

\echo === 4. deactivate that customer (expect: committed) ===
CALL deactivate_customer(:cid);

\echo
\echo === 5. deactivate the same customer again (expect: rejected) ===
CALL deactivate_customer(:cid);

\echo
\echo === the resulting row ===
SELECT customer_id, first_name, last_name, email, activebool, create_date
FROM customer
WHERE email = 'john.bilbao@example.com';
