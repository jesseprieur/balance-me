# balance-me — Specs

Self-hosted personal accounting app for tracking account balances via a transaction ledger.

## Stack

- Backend: Python 3.12, Flask 3.x
- DB: MySQL 8
- Frontend: vanilla HTML/JS + Bootstrap 5 (no build step, no SPA framework)
- Orchestration: Docker Compose (app + db services)

Keep it simple — no extra services, no heavy frameworks, no premature abstraction.

## Users & Auth

- Single user for v1, but modeled as a `users` table (not an env-var password) so multi-user works later without rework.
- Flask session-based login. Password stored hashed (e.g. `werkzeug.security` generate/check password hash).
- All routes except login require an authenticated session.

## Core Entities

### User
- `id`
- `email` (unique)
- `password_hash`
- `created_at`

### Account
- `id`
- `user_id` (FK -> users.id)
- `name`
- `type`: enum `checking` | `credit_card`
- `created_at`
- Balance is **derived**, not stored: sum of its transactions' signed amounts.
- **Starting balance**: not a column on `Account`. The "create account" form has an optional "starting balance" field (default 0) which, on submit, inserts one ordinary `Transaction` ("Opening Balance", dated at account creation) for that amount. This keeps balance = `SUM(transactions.amount)` true everywhere with no special-casing, and editing the starting balance later is just editing/deleting that transaction like any other.

### Transaction
- `id`
- `account_id` (FK -> accounts.id)
- `date`
- `description`
- `amount` (signed decimal; positive = deposit/credit, negative = withdrawal/charge)
- `category` (nullable text field — reserved for future categorization/reporting, no UI/CRUD for it in v1)
- `recurring_rule_id` (nullable FK -> recurring_rules.id) — set if this row was generated from a recurring rule
- `created_at`

### RecurringRule
- `id`
- `account_id` (FK -> accounts.id)
- `description`
- `amount` (signed decimal)
- `interval`: enum `weekly` | `biweekly` | `monthly`
- `start_date`
- `created_at`
- On creation, immediately materializes the next 6 occurrences as real `Transaction` rows (linked via `recurring_rule_id`). No dynamic/on-the-fly generation — it's a batch of real rows.

## Explicit Non-Goals (v1)

- No categories CRUD or category-based reporting UI (field exists on `Transaction`, unused otherwise).
- No dashboard/charts/net-worth reporting.
- No CSV import — manual entry only.
- No transfer-between-accounts concept — a transfer is just two independent manually-entered transactions.
- No multi-user support yet (schema allows it later; UI/authorization does not).
- No auto-generation of more recurring instances beyond the initial 6 (i.e. no scheduled job that tops them back up over time — that's a future enhancement).

## Features (v1)

1. **Auth**: login / logout, session-gated app.
2. **Accounts**: create, list (with derived balance), edit, delete.
   - Deleting an account deletes its transactions (cascade).
3. **Transactions**: create, list (per account, most recent first), edit, delete.
4. **Recurring rules**: create a rule (account, description, amount, interval, start date) → generates 6 transaction rows immediately. List/delete a rule (deleting a rule does not delete already-materialized transactions, only detaches them — sets `recurring_rule_id` to null — or leaves them; decide in implementation, default: leave transactions, just delete the rule).

## Out of scope until explicitly revisited

Anything not listed above (reports, imports, transfers, multi-user auth, category management, recurring auto-refill).
