-- Exercise 2 -- proving the FOREIGN KEY and the ledger CHECKs do something.
--
-- Three rejections. All are supposed to fail, so this file is run without
-- ON_ERROR_STOP as well.

\echo '--- Attempt C: a ledger entry for an account that does not exist ---'
INSERT INTO ewb_transactions (account_number, transaction_type, amount)
VALUES ('EWB-9999', 'DEBIT', 100.00);
-- EXPECTED: violates foreign key constraint

\echo ''
\echo '--- Attempt D: a transaction type outside DEBIT / CREDIT ---'
INSERT INTO ewb_transactions (account_number, transaction_type, amount)
VALUES ('EWB-1001', 'REFUND', 100.00);
-- EXPECTED: violates check constraint on transaction_type

\echo ''
\echo '--- Attempt E: a zero-amount movement ---'
INSERT INTO ewb_transactions (account_number, transaction_type, amount)
VALUES ('EWB-1001', 'DEBIT', 0.00);
-- EXPECTED: violates check constraint on amount

\echo ''
\echo '--- the ledger is still empty ---'
SELECT count(*) AS rows_in_ewb_transactions FROM ewb_transactions;
