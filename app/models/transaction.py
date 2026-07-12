from datetime import date

from app.db import get_db


def create_transaction(account_id, date_, description, amount, category=None, recurring_rule_id=None):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            """
            INSERT INTO transactions (account_id, date, description, amount, category, recurring_rule_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (account_id, date_, description, amount, category, recurring_rule_id),
        )
        return cur.lastrowid


def create_opening_balance_transaction(account_id, amount):
    return create_transaction(account_id, date.today(), "Opening Balance", amount)
