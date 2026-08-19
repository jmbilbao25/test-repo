-- Exercise 3, Step 3.1 -- an atomic transfer.
--
-- PHP 3,000.00 from Juan Dela Cruz (EWB-1001) to Maria Clara (EWB-1002) via
-- EWB EasyWay. Four statements, one transaction: two balance movements and the
-- two ledger entries that account for them.

BEGIN;

-- 1. Deduct 3,000.00 PHP from Juan Dela Cruz
UPDATE ewb_accounts
   SET balance = balance - 3000.00
 WHERE account_number = 'EWB-1001';

-- 2. Credit 3,000.00 PHP to Maria Clara
UPDATE ewb_accounts
   SET balance = balance + 3000.00
 WHERE account_number = 'EWB-1002';

-- 3. Insert the DEBIT entry for Juan
INSERT INTO ewb_transactions (account_number, transaction_type, amount)
VALUES ('EWB-1001', 'DEBIT', 3000.00);

-- 4. Insert the CREDIT entry for Maria
INSERT INTO ewb_transactions (account_number, transaction_type, amount)
VALUES ('EWB-1002', 'CREDIT', 3000.00);

-- Commit all four operations permanently
COMMIT;
