# balance-me

A simple, self-hosted personal accounting app. Track bank/credit accounts and their transactions; balances are derived from the transaction ledger, not stored separately. Supports simple recurring transactions (e.g. a monthly bill), pre-generated 6 occurrences at a time.

No third-party services, no SPA framework, no build step — just Flask, MySQL, and server-rendered Bootstrap pages, all run via Docker Compose.

## Problem

Existing personal finance tools either require linking bank credentials to a third party or are overkill for someone who just wants a private ledger they fully control. balance-me is intentionally minimal: accounts, transactions, and simple recurrence — nothing else, until it's actually needed.

## Architecture

```
┌─────────────┐      ┌──────────────┐
│   Browser   │◄────►│  Flask app   │◄────►  MySQL 8
│ (Bootstrap  │      │ (server-     │      (accounts,
│  5 + vanilla│      │  rendered    │       transactions,
│  JS)        │      │  templates)  │       recurring_rules,
└─────────────┘      └──────────────┘       users)
```

Both `app` and `db` run as Docker Compose services. The Flask app is the only thing talking to MySQL; the browser only talks to Flask over server-rendered HTML (no separate API/frontend split).

## Repo structure

```
balance-me/
├── app/
│   ├── __init__.py       # Flask app factory, config from env
│   ├── models/           # thin data-access helpers per entity
│   ├── routes/           # auth, accounts, transactions, recurring_rules
│   ├── templates/        # Jinja + Bootstrap 5 pages
│   └── static/           # any vanilla JS/CSS
├── db/
│   └── schema.sql        # initial schema, mounted into MySQL init
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── specs.md               # feature specs
├── implementation_plan.md # task checklist
└── README.md               # this file
```

(Structure will firm up as implementation proceeds — see `implementation_plan.md`.)

## Data model (v1)

- **User**: login credentials (hashed password).
- **Account**: belongs to a user; `checking` or `credit_card`; balance = sum of its transactions.
- **Transaction**: belongs to an account; signed amount (positive = deposit, negative = withdrawal/charge); optional `category` field reserved for future use.
- **RecurringRule**: belongs to an account; on creation, immediately generates 6 linked transaction rows at the given interval (`weekly` / `biweekly` / `monthly`).

Full detail in [specs.md](specs.md).

## Usage

```bash
cp .env.example .env   # fill in DB credentials, Flask secret key
docker compose up --build
```

There's no self-serve signup, so create the initial user via the `seed-user` CLI command, run inside the `app` container:

```bash
docker compose exec app flask seed-user you@example.com your-password
```

Then visit `http://localhost:5000` (port TBD in `docker-compose.yml`), log in with that user, and:

1. Create an account (checking or credit card).
2. Add transactions to it — balance updates automatically.
3. Optionally create a recurring rule on an account to pre-generate 6 upcoming transactions (e.g. a monthly rent charge).

## Example

- Create account "Chase Checking" (`checking`).
- Add transaction: `2026-07-01`, "Paycheck", `+2500.00`.
- Add transaction: `2026-07-05`, "Rent", `-1800.00`.
- Balance shown for "Chase Checking": `700.00`.
- Create recurring rule: "Rent", `-1800.00`, `monthly`, starting `2026-08-01` → generates 6 future rent transactions through `2027-01-01`.

## Development

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

## Status

Scaffolding, DB schema, and auth are in place (Flask app factory, Docker Compose, `db/schema.sql`, session-based login/logout, `login_required`). Create the initial user with `flask seed-user <email> <password>` inside the `app` container. Accounts, transactions, and recurring rules routes are still to be built. See [implementation_plan.md](implementation_plan.md) for the current checklist and [specs.md](specs.md) for what's in/out of scope for v1.
