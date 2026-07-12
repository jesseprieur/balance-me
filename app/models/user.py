from werkzeug.security import generate_password_hash

from app.db import get_db


def get_user_by_email(email):
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT id, email, password_hash FROM users WHERE email = %s", (email,))
        return cur.fetchone()


def get_user_by_id(user_id):
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT id, email, password_hash FROM users WHERE id = %s", (user_id,))
        return cur.fetchone()


def create_user(email, password):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO users (email, password_hash) VALUES (%s, %s)",
            (email, generate_password_hash(password)),
        )
        return cur.lastrowid
