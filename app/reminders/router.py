from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.auth import models as auth_models
from app.auth import dependencies as auth_deps
from app.friends import models as friend_models
from app.reminders import models

router = APIRouter(prefix="/reminders", tags=["reminders"])

@router.post("/", response_model=models.ReminderRead)
async def create_reminder(
    reminder_data: models.ReminderCreate,
    current_user: Annotated[auth_models.User, Depends(auth_deps.get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    # Check if recipient is friend
    # Assuming friendship is symmetric/bidirectional rows exist
    friend_query = select(friend_models.Friendship).where(
        friend_models.Friendship.user_id == current_user.id,
        friend_models.Friendship.friend_id == reminder_data.recipient_id
    )
    result = await session.execute(friend_query)
    if not result.scalars().first():
         raise HTTPException(status_code=400, detail="You can only send reminders to friends")
         
    reminder = models.Reminder(
        **reminder_data.dict(),
        creator_id=current_user.id,
        status=models.ReminderStatus.Created
    )
    session.add(reminder)
    await session.commit()
    await session.refresh(reminder)
    return reminder

@router.get("/", response_model=List[models.ReminderRead])
async def list_reminders(
    current_user: Annotated[auth_models.User, Depends(auth_deps.get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    # List sent and received
    query = select(models.Reminder).where(
        or_(
            models.Reminder.creator_id == current_user.id,
            models.Reminder.recipient_id == current_user.id
        )
    )
    result = await session.execute(query)
    return result.scalars().all()

@router.put("/{reminder_id}", response_model=models.ReminderRead)
async def update_reminder(
    reminder_id: int,
    reminder_update: models.ReminderUpdate,
    current_user: Annotated[auth_models.User, Depends(auth_deps.get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    query = select(models.Reminder).where(models.Reminder.id == reminder_id)
    result = await session.execute(query)
    reminder = result.scalars().first()
    
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
        
    is_creator = reminder.creator_id == current_user.id
    is_recipient = reminder.recipient_id == current_user.id
    
    if not (is_creator or is_recipient):
        raise HTTPException(status_code=403, detail="Not authorized to update this reminder")
        
    update_data = reminder_update.dict(exclude_unset=True)
    
    # Logic: Creator can update all except status (maybe status too? Requirement says "except status").
    # Requirement:
    # Creator: Can update all fields *except* the status.
    # Recipient: Can *only* update the status.
    
    # Logic:
    # - Status update allowed ONLY if recipient
    # - Other updates allowed ONLY if creator
    
    if "status" in update_data and update_data["status"] != reminder.status:
        # Check if user is allowed to update status (must be recipient)
        if not is_recipient:
             raise HTTPException(status_code=403, detail="Only recipient can update status")

    non_status_fields = [k for k in update_data.keys() if k != "status"]
    if non_status_fields:
        # Check if user is allowed to update non-status fields (must be creator)
        if not is_creator:
             raise HTTPException(status_code=403, detail="Only creator can update reminder details")
    
    for key, value in update_data.items():
        setattr(reminder, key, value)
        
    session.add(reminder)
    await session.commit()
    await session.refresh(reminder)
    return reminder

@router.delete("/{reminder_id}")
async def delete_reminder(
    reminder_id: int,
    current_user: Annotated[auth_models.User, Depends(auth_deps.get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    query = select(models.Reminder).where(models.Reminder.id == reminder_id)
    result = await session.execute(query)
    reminder = result.scalars().first()
    
    if not reminder:
         raise HTTPException(status_code=404, detail="Reminder not found")
         
    if reminder.creator_id != current_user.id:
         raise HTTPException(status_code=403, detail="Only creator can delete reminder")
         
    await session.delete(reminder)
    await session.commit()
    return {"ok": True}
