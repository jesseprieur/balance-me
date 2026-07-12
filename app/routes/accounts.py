from decimal import Decimal, InvalidOperation

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app.auth import login_required
from app.models.account import (
    ACCOUNT_TYPES,
    create_account,
    delete_account,
    get_account,
    get_accounts,
    update_account,
)
from app.models.transaction import create_opening_balance_transaction

bp = Blueprint("accounts", __name__, url_prefix="/accounts")


def _parse_amount(raw, default=None):
    raw = (raw or "").strip()
    if not raw:
        return default
    try:
        return Decimal(raw)
    except InvalidOperation:
        return None


@bp.get("")
def list_accounts():
    accounts = get_accounts()

    rows = []
    running_balance = Decimal("0")
    for account in accounts:
        balance = account["balance"]
        running_balance += balance
        rows.append(
            {
                **account,
                "cash": balance if account["type"] == "checking" else None,
                "credit": balance if account["type"] == "credit_card" else None,
                "running_balance": running_balance,
            }
        )

    return render_template("accounts/list.html", accounts=rows)


@bp.route("/new", methods=["GET", "POST"])
def new_account():
    if request.method == "GET":
        return render_template("accounts/form.html", account=None, account_types=ACCOUNT_TYPES)

    name = request.form.get("name", "").strip()
    type_ = request.form.get("type", "")
    starting_balance = _parse_amount(request.form.get("starting_balance"), default=Decimal("0"))

    errors = []
    if not name:
        errors.append("Name is required.")
    if type_ not in ACCOUNT_TYPES:
        errors.append("Type must be checking or credit_card.")
    if starting_balance is None:
        errors.append("Starting balance must be a number.")

    if errors:
        for error in errors:
            flash(error)
        return render_template("accounts/form.html", account=None, account_types=ACCOUNT_TYPES), 400

    account_id = create_account(name, type_)
    if starting_balance != 0:
        create_opening_balance_transaction(account_id, starting_balance)

    flash("Account created.")
    return redirect(url_for("accounts.list_accounts"))


@bp.route("/<int:account_id>/edit", methods=["GET", "POST"])
def edit_account(account_id):
    account = get_account(account_id)
    if account is None:
        abort(404)

    if request.method == "GET":
        return render_template("accounts/form.html", account=account, account_types=ACCOUNT_TYPES)

    name = request.form.get("name", "").strip()
    type_ = request.form.get("type", "")

    errors = []
    if not name:
        errors.append("Name is required.")
    if type_ not in ACCOUNT_TYPES:
        errors.append("Type must be checking or credit_card.")

    if errors:
        for error in errors:
            flash(error)
        return render_template("accounts/form.html", account=account, account_types=ACCOUNT_TYPES), 400

    update_account(account_id, name, type_)
    flash("Account updated.")
    return redirect(url_for("accounts.list_accounts"))


@bp.post("/<int:account_id>/delete")
def delete_account_route(account_id):
    account = get_account(account_id)
    if account is None:
        abort(404)

    delete_account(account_id)
    flash("Account deleted.")
    return redirect(url_for("accounts.list_accounts"))


@bp.before_request
@login_required
def require_login():
    pass
