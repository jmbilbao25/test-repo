-- Exercise 1, Step 1.1
-- The EWB account master table. Every business rule that must hold no matter
-- which application is doing the writing lives here, in the table definition,
-- rather than in application code.

CREATE TABLE ewb_accounts (
    account_number  VARCHAR(12) PRIMARY KEY,
    customer_name   VARCHAR(100) NOT NULL,
    currency        VARCHAR(3) DEFAULT 'PHP',
    balance         NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    status          VARCHAR(10) DEFAULT 'ACTIVE',

    -- DB Constraint: prevent a negative balance at the database layer
    CONSTRAINT check_positive_balance CHECK (balance >= 0.00),

    -- DB Constraint: only allow approved currencies
    CONSTRAINT check_valid_currency CHECK (currency IN ('PHP', 'USD'))
);

\echo '--- the table as PostgreSQL stored it ---'
\d ewb_accounts

\echo ''
\echo '--- the two CHECK constraints, read back from the catalog ---'
SELECT con.conname AS constraint_name,
       pg_get_constraintdef(con.oid) AS definition
  FROM pg_constraint con
  JOIN pg_class rel ON rel.oid = con.conrelid
 WHERE rel.relname = 'ewb_accounts'
   AND con.contype = 'c'
 ORDER BY con.conname;
