from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from app.models.user import get_user_by_email, get_user_by_id

bp = Blueprint("auth", __name__)


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = get_user_by_id(user_id) if user_id is not None else None


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    user = get_user_by_email(email) if email else None
    if user is None or not check_password_hash(user["password_hash"], password):
        flash("Invalid email or password.")
        return render_template("login.html"), 401

    session.clear()
    session["user_id"] = user["id"]
    next_url = request.form.get("next") or url_for("index")
    return redirect(next_url)


@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
