-- Exercise 2, Step 2.2
-- The audit ledger. Its account_number is a FOREIGN KEY, so a ledger entry
-- cannot exist for an account that does not.

CREATE TABLE ewb_transactions (
    transaction_id   SERIAL PRIMARY KEY,
    account_number   VARCHAR(12) REFERENCES ewb_accounts(account_number),
    transaction_type VARCHAR(6) CHECK (transaction_type IN ('DEBIT', 'CREDIT')),
    amount           NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

\echo '--- the ledger table, and the foreign key it carries ---'
\d ewb_transactions
