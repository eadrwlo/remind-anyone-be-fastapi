from httpx import AsyncClient
from app.auth import models as auth_models
from app.friends import models as friend_models
from sqlalchemy.ext.asyncio import AsyncSession

async def test_add_friend(client: AsyncClient, auth_headers: dict, session: AsyncSession):
    # Create another user to add as friend
    friend = auth_models.User(email="friend@example.com", username="friend", full_name="Friend")
    session.add(friend)
    await session.commit()
    
    response = await client.post(
        "/friends/", 
        json={"friend_email_or_username": "friend@example.com"},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["email"] == "friend@example.com"

async def test_list_friends(client: AsyncClient, auth_headers: dict, session: AsyncSession, test_user: auth_models.User):
    # Setup friendship
    friend = auth_models.User(email="friend2@example.com", username="friend2", full_name="Friend 2")
    session.add(friend)
    await session.commit()
    await session.refresh(friend)
    
    f1 = friend_models.Friendship(user_id=test_user.id, friend_id=friend.id)
    f2 = friend_models.Friendship(user_id=friend.id, friend_id=test_user.id)
    session.add(f1)
    session.add(f2)
    await session.commit()
    
    response = await client.get("/friends/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    emails = [f["email"] for f in data]
    assert "friend2@example.com" in emails
