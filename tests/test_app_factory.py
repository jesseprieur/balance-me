from app import create_app


def test_create_app_returns_configured_flask_app():
    app = create_app({"MYSQL_HOST": "test-db", "SECRET_KEY": "test-secret"})

    assert app.config["MYSQL_HOST"] == "test-db"
    assert app.config["SECRET_KEY"] == "test-secret"


def test_healthz_endpoint_returns_ok():
    app = create_app()
    client = app.test_client()

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
