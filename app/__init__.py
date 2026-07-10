import os

from flask import Flask


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

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    return app
