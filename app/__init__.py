import os

import click
from flask import Flask, render_template

from app import db as db_module
from app.auth import login_required


def create_app(config_overrides=None):
    app = Flask(__name__)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "dev"),
        MYSQL_HOST=os.environ.get("MYSQL_HOST", "db"),
        MYSQL_PORT=int(os.environ.get("MYSQL_PORT", "3306")),
        MYSQL_USER=os.environ.get("MYSQL_USER", "balance_me"),
        MYSQL_PASSWORD=os.environ.get("MYSQL_PASSWORD", ""),
        MYSQL_DATABASE=os.environ.get("MYSQL_DATABASE", "balance_me"),
    )

    if config_overrides:
        app.config.from_mapping(config_overrides)

    db_module.init_app(app)

    from app.routes.auth import bp as auth_bp

    app.register_blueprint(auth_bp)

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    @app.get("/")
    @login_required
    def index():
        return render_template("index.html")

    @app.cli.command("seed-user")
    @click.argument("email")
    @click.argument("password")
    def seed_user_command(email, password):
        """Create the initial user (there's no self-serve signup)."""
        from app.models.user import create_user, get_user_by_email

        if get_user_by_email(email):
            click.echo(f"User {email} already exists.")
            return
        create_user(email, password)
        click.echo(f"Created user {email}")

    return app
