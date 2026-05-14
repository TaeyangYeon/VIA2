import pytest
import httpx
from backend.main import app


@pytest.mark.asyncio
async def test_health_endpoint_returns_200():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_response_status_is_ok():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_health_response_contains_version():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
    assert "version" in response.json()


@pytest.mark.asyncio
async def test_cors_headers_present_on_health():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"},
        )
    assert "access-control-allow-origin" in response.headers
