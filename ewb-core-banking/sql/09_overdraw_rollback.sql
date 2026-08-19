-- Exercise 3, Step 3.2 -- an overdrawn transfer, and the rollback.
--
-- Maria Clara holds 5,500.00 PHP and attempts to send 20,000.00 PHP.
-- check_positive_balance rejects the UPDATE, which puts the whole transaction
-- into an aborted state: no further statement will run until it is ended.

BEGIN;

-- Attempt to deduct 20,000.00 PHP from Maria Clara (balance: 5,500.00 PHP)
UPDATE ewb_accounts
   SET balance = balance - 20000.00
 WHERE account_number = 'EWB-1002';
-- EXPECTED: violates check constraint "check_positive_balance"

-- Anything sent now is refused: the transaction is already aborted.
SELECT 'this will not run' AS attempted_after_the_error;

-- End the transaction and discard everything it did
ROLLBACK;
