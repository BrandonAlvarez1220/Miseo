from httpx import AsyncClient


async def test_health_reports_database_ok(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"] == "ok"
    assert response.headers["x-request-id"]


async def test_request_id_is_propagated_when_safe(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health", headers={"X-Request-ID": "abc123"})
    assert response.headers["x-request-id"] == "abc123"


async def test_unsafe_request_id_is_replaced(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health", headers={"X-Request-ID": "bad id\nINJECT"})
    assert response.headers["x-request-id"] != "bad id\nINJECT"


async def test_unknown_route_uses_uniform_error_shape(client: AsyncClient) -> None:
    response = await client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "not_found", "message": "Not Found", "details": None}
    }


async def test_cors_allows_only_configured_origins(client: AsyncClient) -> None:
    allowed = await client.get("/api/v1/health", headers={"Origin": "http://testserver.local"})
    denied = await client.get("/api/v1/health", headers={"Origin": "http://evil.example"})

    assert allowed.headers["access-control-allow-origin"] == "http://testserver.local"
    assert "access-control-allow-origin" not in denied.headers
