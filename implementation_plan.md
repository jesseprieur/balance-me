# balance-me — Implementation Plan

Checkboxes track progress. See `specs.md` for feature detail, `readme.md` for architecture/usage once written.

## 0. Project scaffolding
- [ ] `docker-compose.yml` with `app` (Flask) and `db` (MySQL 8) services
- [ ] `Dockerfile` for the Flask app
- [ ] `requirements.txt` (Flask, PyMySQL or mysqlclient, werkzeug for password hashing)
- [ ] Basic Flask app factory (`app/__init__.py`) with config loaded from env vars (DB host/user/pass/name, secret key)
- [ ] `.env.example` documenting required env vars
- [ ] `.gitignore` (venv, `__pycache__`, `.env`, etc.)

## 1. Database schema
- [ ] `users` table (id, email/username, password_hash, created_at)
- [ ] `accounts` table (id, user_id, name, type, created_at)
- [ ] `transactions` table (id, account_id, date, description, amount, category nullable, recurring_rule_id nullable, created_at)
- [ ] `recurring_rules` table (id, account_id, description, amount, interval, start_date, created_at)
- [ ] SQL migration/init script run on container startup (or simple `schema.sql` mounted into MySQL init)

## 2. Auth
- [ ] Login route (GET form + POST verify) using session cookie
- [ ] Logout route
- [ ] `login_required` decorator applied to all app routes
- [ ] Seed script or first-run flow to create the initial user (since there's no self-serve signup yet)

## 3. Accounts
- [ ] List accounts view (name, type, derived balance)
- [ ] Create account form + route, including optional "starting balance" field that inserts an "Opening Balance" `Transaction` row on submit (no schema change — see specs.md)
- [ ] Edit account form + route
- [ ] Delete account route (cascade-deletes its transactions)
- [ ] Balance calculation helper: `SUM(amount)` for a given account_id

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
- Category CRUD/reporting, dashboards/charts, CSV import, transfer linking, multi-user UI/authorization, recurring auto-refill beyond initial 6.
