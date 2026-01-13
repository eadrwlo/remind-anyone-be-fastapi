from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime

class FriendshipBase(SQLModel):
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    friend_id: int = Field(foreign_key="user.id", primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Friendship(FriendshipBase, table=True):
    pass

class FriendshipCreate(SQLModel):
    friend_email_or_username: str
