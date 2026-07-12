# balance-me — Specs

Self-hosted personal accounting app for tracking account balances via a transaction ledger.

## Stack

- Backend: Python 3.12, Flask 3.x
- DB: MySQL 8
- Frontend: vanilla HTML/JS + Bootstrap 5 (no build step, no SPA framework)
- Orchestration: Docker Compose (app + db services)

Keep it simple — no extra services, no heavy frameworks, no premature abstraction.

## Users & Auth

- Multiple users can log in (each with their own `users` row + credentials), but users exist only to gate access to the app — they are not an ownership boundary. All accounts, transactions, and recurring rules are shared/visible to every logged-in user.
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
- `name`
- `type`: enum `checking` | `credit_card`
- `created_at`
- Balance is **derived**, not stored: sum of its transactions' signed amounts.
- **Starting balance**: not a column on `Account`. The "create account" form has an optional "starting balance" field (default 0) which, on submit, inserts one ordinary `Transaction` ("Opening Balance", dated at account creation) for that amount. This keeps balance = `SUM(transactions.amount)` true everywhere with no special-casing, and editing the starting balance later is just editing/deleting that transaction like any other.
- Checking and credit card accounts behave differently past this point:
  - **Checking**: the starting balance is just cash on hand. It affects the running balance immediately and permanently, same as any other transaction.
  - **Credit card**: the starting balance is debt owed, not cash — it shouldn't count against the running balance the way a checking balance does until it's actually due. Instead it behaves like a loan with a recurring monthly due date: the balance accrues from charges, and on each due date the outstanding balance is what actually hits the running balance (as a deduction), then the card's balance resets to 0 for the next cycle.
- **`next_due_date`** (nullable date): only applicable when `type = credit_card`. Set from the optional "first due date" field on the "create account" form, then mutated forward by the app each time a payoff fires (see "Credit card payoff mechanics"). There's no separate immutable "first due date" column — once it's seeded the account only ever needs to know its *next* due date.

## Credit card payoff mechanics

A credit card's due-date payment isn't a fixed amount like a normal recurring rule — it's however much is owed on that date, which depends on what's been charged since the last payoff. Rather than model this as a `RecurringRule` (which materializes fixed-amount transactions in batches up front — impossible here, since the amount isn't known yet), it's tracked directly on the account:

- A credit card account with `next_due_date` set is checked opportunistically (e.g. on login/dashboard load, since there's no background job runner in v1) whenever that date has arrived.
- When it has, the app:
  1. Computes the account's current derived balance (sum of transactions since the last payoff, or since account creation for the first cycle).
  2. Inserts a `Transaction` dated `next_due_date`, description "Credit Card Payment Due", `amount` = the negation of that balance (bringing the account's running total back to 0). Not linked via `recurring_rule_id` — there's no rule row; the payoff transaction is identified purely by its description, same convention as "Opening Balance".
  3. Advances the account's `next_due_date` by one month.
- This is an intentional, narrow exception to the "no dynamic/on-the-fly generation" behavior that applies to `RecurringRule`s — it's required because the payoff amount can't be known in advance, and it's account-level state (at most one pending payoff per credit card account), not a general rule a user creates/lists/deletes.

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
- This entity is unrelated to credit card payoffs — see "Credit card payoff mechanics" above, which is tracked on `Account` instead since it's account-level state, not a user-managed rule.

## Explicit Non-Goals (v1)

- No categories CRUD or category-based reporting UI (field exists on `Transaction`, unused otherwise).
- No dashboard/charts/net-worth reporting.
- No CSV import — manual entry only.
- No transfer-between-accounts concept — a transfer is just two independent manually-entered transactions.
- No per-user ownership/authorization on accounts — every logged-in user sees and can edit everything.
- No auto-generation of more recurring instances beyond the initial 6 (i.e. no scheduled job that tops them back up over time — that's a future enhancement). This does not apply to credit card payoffs, which are inherently a rolling single-occurrence mechanism tracked on the account (see "Credit card payoff mechanics").
- No true background job runner — the credit card due-date check happens opportunistically on request (e.g. dashboard load), not on a cron/scheduler.

## Features (v1)

1. **Auth**: login / logout, session-gated app.
2. **Accounts**: create, list (with derived balance), edit, delete.
   - Create form: name, type, optional starting balance (both types), and — only shown/used for `credit_card` — optional "first due date" (stored as the account's `next_due_date`).
   - Deleting an account deletes its transactions (cascade).
   - List view: running balance for a credit card only reflects transactions since its last payoff, not the un-due accrued balance, until a due date is reached and a payoff transaction is generated (see "Credit card payoff mechanics").
3. **Transactions**: create, list (per account, most recent first), edit, delete.
4. **Recurring rules**: create a rule (account, description, amount, interval, start date) → generates 6 transaction rows immediately. List/delete a rule (deleting a rule does not delete already-materialized transactions, only detaches them — sets `recurring_rule_id` to null — or leaves them; decide in implementation, default: leave transactions, just delete the rule).
5. **Credit card payoff**: on each app request that touches the dashboard/account list, check any credit card accounts whose `next_due_date` has arrived; materialize the payoff transaction and advance `next_due_date` by a month (see "Credit card payoff mechanics").

## Out of scope until explicitly revisited

Anything not listed above (reports, imports, transfers, per-user data ownership/authorization, category management, recurring auto-refill).
