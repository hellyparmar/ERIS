from fastapi.testclient import TestClient

from app.main import app


def test_global_exception_handler_returns_clean_json_response():
    def raise_internal_error():
        raise RuntimeError("forced internal error for testing")

    app.add_api_route(
        "/__test-exception__",
        raise_internal_error,
        methods=["GET"],
        include_in_schema=False,
    )

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/__test-exception__")

    # Clean up the temporary test route to avoid leaking into other tests
    app.router.routes = [route for route in app.router.routes if getattr(route, "path", None) != "/__test-exception__"]

    assert response.status_code == 500
    body = response.json()
    assert body["error"] == "Internal server error"
    assert body["status"] == 500
    assert "request_id" in body
    assert isinstance(body["request_id"], str)
