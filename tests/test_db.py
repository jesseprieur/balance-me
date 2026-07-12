def test_cryptography_available_for_mysql8_auth():
    """MySQL 8 defaults to caching_sha2_password; PyMySQL needs the
    `cryptography` package installed to complete that auth handshake.
    Without it, get_db() raises RuntimeError only at connection time,
    which mocked unit tests never exercise.
    """
    import cryptography  # noqa: F401
