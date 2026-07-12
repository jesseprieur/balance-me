from decimal import Decimal
from unittest.mock import patch

from werkzeug.security import generate_password_hash

from app import create_app


def make_app():
    return create_app({"MYSQL_HOST": "test-db", "SECRET_KEY": "test-secret", "TESTING": True})


def make_user():
    return {"id": 1, "email": "a@b.com", "password_hash": generate_password_hash("secret123")}


def login(client, user):
    with client.session_transaction() as sess:
        sess["user_id"] = user["id"]


@patch("app.routes.auth.get_user_by_id")
def test_list_accounts_requires_login(mock_get_user_by_id):
    mock_get_user_by_id.return_value = None
    app = make_app()
    client = app.test_client()

    response = client.get("/accounts")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


@patch("app.routes.accounts.get_accounts")
@patch("app.routes.auth.get_user_by_id")
def test_list_accounts_shows_derived_balance(mock_get_user_by_id, mock_get_accounts):
    user = make_user()
    mock_get_user_by_id.return_value = user
    mock_get_accounts.return_value = [
        {"id": 1, "name": "Checking", "type": "checking", "balance": Decimal("42.50")}
    ]
    app = make_app()
    client = app.test_client()
    login(client, user)

    response = client.get("/accounts")

    assert response.status_code == 200
    assert b"Checking" in response.data
    assert b"42.50" in response.data
    mock_get_accounts.assert_called_once_with()


@patch("app.routes.accounts.get_accounts")
@patch("app.routes.auth.get_user_by_id")
def test_list_accounts_splits_cash_and_credit_and_shows_running_balance(
    mock_get_user_by_id, mock_get_accounts
):
    user = make_user()
    mock_get_user_by_id.return_value = user
    mock_get_accounts.return_value = [
        {"id": 1, "name": "Checking", "type": "checking", "balance": Decimal("100.00")},
        {"id": 2, "name": "Visa", "type": "credit_card", "balance": Decimal("-30.00")},
    ]
    app = make_app()
    client = app.test_client()
    login(client, user)

    response = client.get("/accounts")
    body = response.data.decode()

    assert response.status_code == 200
    # Checking row: cash column shows its balance, credit column blank.
    checking_row = body[body.index("Checking"):body.index("Visa")]
    assert "100.00" in checking_row
    # Visa row: credit column shows its balance.
    visa_row = body[body.index("Visa"):]
    assert "-30.00" in visa_row
    # Running balance accumulates down the list: 100.00, then 100.00 + (-30.00) = 70.00.
    assert "70.00" in visa_row


@patch("app.routes.accounts.create_opening_balance_transaction")
@patch("app.routes.accounts.create_account")
@patch("app.routes.auth.get_user_by_id")
def test_new_account_with_starting_balance_creates_opening_transaction(
    mock_get_user_by_id, mock_create_account, mock_create_opening_balance_transaction
):
    user = make_user()
    mock_get_user_by_id.return_value = user
    mock_create_account.return_value = 7
    app = make_app()
    client = app.test_client()
    login(client, user)

    response = client.post(
        "/accounts/new",
        data={"name": "Chase Checking", "type": "checking", "starting_balance": "100.00"},
    )

    assert response.status_code == 302
    mock_create_account.assert_called_once_with("Chase Checking", "checking")
    mock_create_opening_balance_transaction.assert_called_once_with(7, Decimal("100.00"))


@patch("app.routes.accounts.create_opening_balance_transaction")
@patch("app.routes.accounts.create_account")
@patch("app.routes.auth.get_user_by_id")
def test_new_account_with_zero_starting_balance_skips_opening_transaction(
    mock_get_user_by_id, mock_create_account, mock_create_opening_balance_transaction
):
    user = make_user()
    mock_get_user_by_id.return_value = user
    mock_create_account.return_value = 7
    app = make_app()
    client = app.test_client()
    login(client, user)

    response = client.post(
        "/accounts/new",
        data={"name": "Chase Checking", "type": "checking", "starting_balance": "0"},
    )

    assert response.status_code == 302
    mock_create_opening_balance_transaction.assert_not_called()


@patch("app.routes.accounts.create_account")
@patch("app.routes.auth.get_user_by_id")
def test_new_account_rejects_invalid_type(mock_get_user_by_id, mock_create_account):
    user = make_user()
    mock_get_user_by_id.return_value = user
    app = make_app()
    client = app.test_client()
    login(client, user)

    response = client.post(
        "/accounts/new",
        data={"name": "Chase Checking", "type": "savings", "starting_balance": "0"},
    )

    assert response.status_code == 400
    mock_create_account.assert_not_called()


@patch("app.routes.accounts.update_account")
@patch("app.routes.accounts.get_account")
@patch("app.routes.auth.get_user_by_id")
def test_edit_account_updates_name_and_type(mock_get_user_by_id, mock_get_account, mock_update_account):
    user = make_user()
    mock_get_user_by_id.return_value = user
    mock_get_account.return_value = {"id": 1, "name": "Old", "type": "checking"}
    app = make_app()
    client = app.test_client()
    login(client, user)

    response = client.post("/accounts/1/edit", data={"name": "New Name", "type": "credit_card"})

    assert response.status_code == 302
    mock_update_account.assert_called_once_with(1, "New Name", "credit_card")


@patch("app.routes.accounts.get_account")
@patch("app.routes.auth.get_user_by_id")
def test_edit_account_404s_for_missing_account(mock_get_user_by_id, mock_get_account):
    user = make_user()
    mock_get_user_by_id.return_value = user
    mock_get_account.return_value = None
    app = make_app()
    client = app.test_client()
    login(client, user)

    response = client.get("/accounts/1/edit")

    assert response.status_code == 404


@patch("app.routes.accounts.delete_account")
@patch("app.routes.accounts.get_account")
@patch("app.routes.auth.get_user_by_id")
def test_delete_account_removes_account(mock_get_user_by_id, mock_get_account, mock_delete_account):
    user = make_user()
    mock_get_user_by_id.return_value = user
    mock_get_account.return_value = {"id": 1, "name": "Checking", "type": "checking"}
    app = make_app()
    client = app.test_client()
    login(client, user)

    response = client.post("/accounts/1/delete")

    assert response.status_code == 302
    mock_delete_account.assert_called_once_with(1)


@patch("app.routes.accounts.delete_account")
@patch("app.routes.accounts.get_account")
@patch("app.routes.auth.get_user_by_id")
def test_any_logged_in_user_can_delete_shared_account(
    mock_get_user_by_id, mock_get_account, mock_delete_account
):
    """Accounts are shared across all users, not owned by the creator (specs.md)."""
    other_user = {"id": 2, "email": "c@d.com", "password_hash": generate_password_hash("secret123")}
    mock_get_user_by_id.return_value = other_user
    mock_get_account.return_value = {"id": 1, "name": "Checking", "type": "checking"}
    app = make_app()
    client = app.test_client()
    login(client, other_user)

    response = client.post("/accounts/1/delete")

    assert response.status_code == 302
    mock_get_account.assert_called_once_with(1)
    mock_delete_account.assert_called_once_with(1)
