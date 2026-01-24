from typing import Optional
from datetime import datetime
from enum import Enum
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, DateTime

class Severity(str, Enum):
    Low = "Low"
    Medium = "Medium"
    High = "High"

class ReminderStatus(str, Enum):
    Created = "Created"
    Completed = "Completed"

class ReminderBase(SQLModel):
    title: str = Field(index=True)
    description: Optional[str] = None
    due_date: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    severity: Severity = Severity.Medium
    status: ReminderStatus = ReminderStatus.Created

class Reminder(ReminderBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    creator_id: int = Field(foreign_key="user.id")
    recipient_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True))
    )

class ReminderCreate(SQLModel):
    title: str
    description: Optional[str] = None
    due_date: datetime
    severity: Severity = Severity.Medium
    recipient_id: int

class ReminderUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    severity: Optional[Severity] = None
    status: Optional[ReminderStatus] = None

class ReminderRead(ReminderBase):
    id: int
    creator_id: int
    recipient_id: int
    created_at: datetime
