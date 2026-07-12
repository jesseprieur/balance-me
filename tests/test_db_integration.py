import os
import socket

import pytest

from app import create_app
from app.db import get_db

MYSQL_HOST = os.environ.get("MYSQL_HOST", "db")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))


def _db_reachable(host, port, timeout=1):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(
    not _db_reachable(MYSQL_HOST, MYSQL_PORT),
    reason="MySQL not reachable; run inside `docker compose exec app pytest` to exercise this test",
)


def test_get_db_connects_and_authenticates():
    """Regression test for the caching_sha2_password/cryptography bug: unlike
    the mocked auth tests, this opens a real connection so a broken auth
    handshake actually fails the suite instead of only surfacing at runtime.
    """
    app = create_app()
    with app.app_context():
        db = get_db()
        with db.cursor() as cur:
            cur.execute("SELECT 1")
            assert cur.fetchone() is not None
