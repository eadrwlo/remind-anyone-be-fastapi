from httpx import AsyncClient

async def test_login_success(client: AsyncClient):
    response = await client.post("/auth/login", json={"id_token": "test-token"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

async def test_login_fail(client: AsyncClient):
    response = await client.post("/auth/login", json={"id_token": "invalid"})
    assert response.status_code == 400
