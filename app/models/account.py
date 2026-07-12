from app.db import get_db

ACCOUNT_TYPES = ("checking", "credit_card")


def create_account(name, type_):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO accounts (name, type) VALUES (%s, %s)",
            (name, type_),
        )
        return cur.lastrowid


def get_account(account_id):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "SELECT id, name, type, created_at FROM accounts WHERE id = %s",
            (account_id,),
        )
        return cur.fetchone()


def get_accounts():
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            """
            SELECT a.id, a.name, a.type, a.created_at,
                   COALESCE(SUM(t.amount), 0) AS balance
            FROM accounts a
            LEFT JOIN transactions t ON t.account_id = a.id
            GROUP BY a.id, a.name, a.type, a.created_at
            ORDER BY a.name
            """
        )
        return cur.fetchall()


def update_account(account_id, name, type_):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "UPDATE accounts SET name = %s, type = %s WHERE id = %s",
            (name, type_, account_id),
        )
        return cur.rowcount


def delete_account(account_id):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "DELETE FROM accounts WHERE id = %s",
            (account_id,),
        )
        return cur.rowcount


def get_balance(account_id):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "SELECT COALESCE(SUM(amount), 0) AS balance FROM transactions WHERE account_id = %s",
            (account_id,),
        )
        return cur.fetchone()["balance"]
