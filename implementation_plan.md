# balance-me — Implementation Plan

Checkboxes track progress. See `specs.md` for feature detail, `README.md` for architecture/usage once written.

## 0. Project scaffolding
- [x] `docker-compose.yml` with `app` (Flask) and `db` (MySQL 8) services
- [x] `Dockerfile` for the Flask app
- [x] `requirements.txt` (Flask, PyMySQL or mysqlclient, werkzeug for password hashing)
- [x] Basic Flask app factory (`app/__init__.py`) with config loaded from env vars (DB host/user/pass/name, secret key)
- [x] `.env.example` documenting required env vars
- [x] `.gitignore` (venv, `__pycache__`, `.env`, etc.)

## 1. Database schema
- [x] `users` table (id, email/username, password_hash, created_at)
- [x] `accounts` table (id, name, type, created_at)
- [ ] `accounts.next_due_date` nullable column (only meaningful for `credit_card` type; seeded from the create form's "first due date" and advanced monthly by the app — see specs.md)
- [x] `transactions` table (id, account_id, date, description, amount, category nullable, recurring_rule_id nullable, created_at)
- [x] `recurring_rules` table (id, account_id, description, amount, interval, start_date, created_at)
- [x] SQL migration/init script run on container startup (or simple `schema.sql` mounted into MySQL init)

## 2. Auth
- [x] Login route (GET form + POST verify) using session cookie
- [x] Logout route
- [x] `login_required` decorator applied to all app routes
- [x] Seed script or first-run flow to create the initial user (since there's no self-serve signup yet)

## 3. Accounts
- [ ] List accounts view (name, type, cash +/-, credit +/-, running balance)
  - [ ] Running balance should only take into account cash +/- *until* credit card is due
- [x] Create account form + route, 
  - [ ] If choosing checking, including optional "starting balance" field that inserts an "Opening Balance" `Transaction` row on submit (no schema change — see specs.md)
  - [ ] If choosing credit card, including optional "starting balance" field (same "Opening Balance" `Transaction` insert) and an optional "first due date" field that's stored directly as `accounts.next_due_date`, regardless of whether a starting balance was given
- [x] Edit account form + route
- [x] Delete account route (cascade-deletes its transactions)
- [x] Balance calculation helper: `SUM(amount)` for a given account_id
- [ ] Credit card payoff check: on dashboard/account-list load, find credit card accounts with `next_due_date <= today`, insert the payoff `Transaction` (amount = negated current balance since last payoff, identified by description, not `recurring_rule_id`) and advance `next_due_date` by one month (see specs.md "Credit card payoff mechanics")

## 4. Transactions
- [ ] List transactions for an account (most recent first)
- [ ] Create transaction form + route
- [ ] Edit transaction form + route
- [ ] Delete transaction route

## 5. Recurring rules
- [ ] Create recurring rule form + route (account, description, amount, interval, start date)
- [ ] Occurrence-date generator for weekly/biweekly/monthly, capped at 6
- [ ] On rule creation, insert 6 linked `transactions` rows
- [ ] List recurring rules (per account or globally)
- [ ] Delete recurring rule route (rule row only; leaves already-materialized transactions intact)

## 6. Frontend (Bootstrap 5 + vanilla JS, server-rendered templates)
- [ ] Base layout template (nav, login state)
- [ ] Login page
- [ ] Accounts list/dashboard page
- [ ] Account detail page (transactions list + add transaction + add recurring rule)
- [ ] Shared form partials for account/transaction/recurring-rule forms

## 7. Polish / cross-cutting
- [ ] Flash messages for create/update/delete confirmations and errors
- [ ] Basic input validation (amount is numeric, required fields) server-side
- [ ] Diagnostic logging in dev (per project convention)
- [ ] README usage instructions verified end-to-end (`docker compose up`, login, create account, add transaction, add recurring rule)

## Explicitly deferred (do not build yet)
- Category CRUD/reporting, dashboards/charts, CSV import, transfer linking, per-user data ownership/authorization, recurring auto-refill beyond initial 6.
