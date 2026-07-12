from unittest.mock import patch

from werkzeug.security import generate_password_hash

from app import create_app


def make_app():
    return create_app({"MYSQL_HOST": "test-db", "SECRET_KEY": "test-secret", "TESTING": True})


def make_user(password="secret123"):
    return {"id": 1, "email": "a@b.com", "password_hash": generate_password_hash(password)}


def test_index_redirects_to_login_when_not_authenticated():
    app = make_app()
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_login_page_renders():
    app = make_app()
    client = app.test_client()

    response = client.get("/login")

    assert response.status_code == 200
    assert b"Log in" in response.data


@patch("app.routes.auth.get_user_by_email")
def test_login_success_sets_session_and_redirects(mock_get_user_by_email):
    mock_get_user_by_email.return_value = make_user()
    app = make_app()
    client = app.test_client()

    response = client.post("/login", data={"email": "a@b.com", "password": "secret123"})

    assert response.status_code == 302
    with client.session_transaction() as sess:
        assert sess["user_id"] == 1


@patch("app.routes.auth.get_user_by_email")
def test_login_failure_with_wrong_password_returns_401(mock_get_user_by_email):
    mock_get_user_by_email.return_value = make_user()
    app = make_app()
    client = app.test_client()

    response = client.post("/login", data={"email": "a@b.com", "password": "wrong"})

    assert response.status_code == 401
    with client.session_transaction() as sess:
        assert "user_id" not in sess


@patch("app.routes.auth.get_user_by_email")
def test_login_failure_with_unknown_email_returns_401(mock_get_user_by_email):
    mock_get_user_by_email.return_value = None
    app = make_app()
    client = app.test_client()

    response = client.post("/login", data={"email": "nobody@b.com", "password": "secret123"})

    assert response.status_code == 401


@patch("app.routes.auth.get_user_by_id")
@patch("app.routes.auth.get_user_by_email")
def test_authenticated_user_can_access_index(mock_get_user_by_email, mock_get_user_by_id):
    user = make_user()
    mock_get_user_by_email.return_value = user
    mock_get_user_by_id.return_value = user
    app = make_app()
    client = app.test_client()
    client.post("/login", data={"email": "a@b.com", "password": "secret123"})

    response = client.get("/")

    assert response.status_code == 302
    assert "/accounts" in response.headers["Location"]


@patch("app.routes.auth.get_user_by_id")
def test_logout_clears_session(mock_get_user_by_id):
    mock_get_user_by_id.return_value = make_user()
    app = make_app()
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"] = 1

    response = client.post("/logout")

    assert response.status_code == 302
    with client.session_transaction() as sess:
        assert "user_id" not in sess
