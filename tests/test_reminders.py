from httpx import AsyncClient
from datetime import datetime, timedelta
from app.auth import models as auth_models
from app.friends import models as friend_models
from app.reminders import models as reminder_models
from sqlalchemy.ext.asyncio import AsyncSession

async def test_create_reminder(client: AsyncClient, auth_headers: dict, session: AsyncSession, test_user: auth_models.User):
    friend = auth_models.User(email="friend3@example.com", username="friend3", full_name="Friend 3")
    session.add(friend)
    await session.commit()
    await session.refresh(friend)
    
    # Establish friendship
    f1 = friend_models.Friendship(user_id=test_user.id, friend_id=friend.id)
    f2 = friend_models.Friendship(user_id=friend.id, friend_id=test_user.id)
    session.add(f1)
    session.add(f2)
    await session.commit()
    
    deadline = datetime.utcnow() + timedelta(days=1)
    response = await client.post(
        "/reminders/",
        json={
            "title": "Buy milk",
            "due_date": deadline.isoformat(),
            "recipient_id": friend.id
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Buy milk"
    assert data["status"] == "Created"

async def test_list_reminders(client: AsyncClient, auth_headers: dict):
    response = await client.get("/reminders/", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

async def test_update_reminder(client: AsyncClient, auth_headers: dict, session: AsyncSession, test_user: auth_models.User):
    # Setup reminder
    reminder = reminder_models.Reminder(
        title="Old",
        due_date=datetime.utcnow(),
        creator_id=test_user.id,
        recipient_id=test_user.id # Send to self for easy test or mock recipient
    )
    session.add(reminder)
    await session.commit()
    await session.refresh(reminder)
    
    response = await client.put(
        f"/reminders/{reminder.id}",
        json={"title": "New Title"},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["title"] == "New Title"

async def test_delete_reminder(client: AsyncClient, auth_headers: dict, session: AsyncSession, test_user: auth_models.User):
    reminder = reminder_models.Reminder(
        title="To Delete",
        due_date=datetime.utcnow(),
        creator_id=test_user.id,
        recipient_id=test_user.id
    )
    session.add(reminder)
    await session.commit()
    await session.refresh(reminder)
    
    response = await client.delete(f"/reminders/{reminder.id}", headers=auth_headers)
    assert response.status_code == 200
    
    # Verify deletion
    r = await session.get(reminder_models.Reminder, reminder.id)
    assert r is None
