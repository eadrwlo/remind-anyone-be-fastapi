from httpx import AsyncClient, Response
from unittest.mock import MagicMock, patch
from sqlmodel import select
from app.auth.models import User
from app.friends.models import Friendship
from app.reminders.models import Reminder

async def test_update_device_token(client: AsyncClient, session, auth_headers, test_user):
    response = await client.put(
        "/auth/me/device-token",
        headers=auth_headers,
        json={"token": "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["expo_push_token"] == "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]"

    # Verify in DB
    await session.refresh(test_user)
    assert test_user.expo_push_token == "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]"

async def test_create_reminder_sends_notification(
    client: AsyncClient, 
    session, 
    auth_headers, 
    test_user
):
    # Setup: Create a second user (recipient)
    recipient = User(
        email="friend@example.com",
        username="friend",
        full_name="Friend User",
        expo_push_token="ExponentPushToken[recipient_token]"
    )
    session.add(recipient)
    await session.commit()
    await session.refresh(recipient)

    friendship = Friendship(user_id=test_user.id, friend_id=recipient.id)
    session.add(friendship)
    await session.commit()

    with patch("httpx.AsyncClient") as MockClient:
        mock_instance = MagicMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        
        async def async_post(*args, **kwargs):
            return Response(200, json={"data": {"status": "ok"}})
            
        mock_instance.post.side_effect = async_post
        
        MockClient.return_value = mock_instance

        response = await client.post(
            "/reminders/",
            headers=auth_headers,
            json={
                "title": "Test Push",
                "due_date": "2024-01-01T12:00:00Z",
                "recipient_id": recipient.id,
                "severity": "Medium"
            }
        )
        assert response.status_code == 200
        
        mock_instance.post.assert_called_once()
        call_args = mock_instance.post.call_args
        assert call_args[0][0] == "https://exp.host/--/api/v2/push/send"
        assert call_args[1]["json"]["to"] == "ExponentPushToken[recipient_token]"
        assert call_args[1]["json"]["title"] == f"New Reminder from {test_user.username}"
        assert call_args[1]["json"]["body"] == "Test Push"
