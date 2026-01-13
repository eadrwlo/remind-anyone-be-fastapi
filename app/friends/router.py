import logging

from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.auth import models as auth_models
from app.auth import dependencies as auth_deps
from app.friends import models

router = APIRouter(prefix="/friends", tags=["friends"])

@router.post("/", response_model=auth_models.UserRead)
async def add_friend(
    friend_data: models.FriendshipCreate,
    current_user: Annotated[auth_models.User, Depends(auth_deps.get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    # Find target user
    query = select(auth_models.User).where(
        or_(
            auth_models.User.email == friend_data.friend_email_or_username,
            auth_models.User.username == friend_data.friend_email_or_username
        )
    )
    result = await session.execute(query)
    target_user = result.scalars().first()
    
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if target_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot add yourself as friend")
        
    # Check if already friends
    existing_query = select(models.Friendship).where(
        models.Friendship.user_id == current_user.id,
        models.Friendship.friend_id == target_user.id
    )
    existing_result = await session.execute(existing_query)
    if existing_result.scalars().first():
        raise HTTPException(status_code=400, detail="Already friends")

    # Create bidirectional friendship (auto-accept)
    friendship_1 = models.Friendship(user_id=current_user.id, friend_id=target_user.id)
    friendship_2 = models.Friendship(user_id=target_user.id, friend_id=current_user.id)
    
    session.add(friendship_1)
    session.add(friendship_2)
    await session.commit()
    
    return target_user

@router.get("/", response_model=List[auth_models.UserRead])
async def list_friends(
    current_user: Annotated[auth_models.User, Depends(auth_deps.get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    logging.info(f"Listing friends for user: {current_user}")
    # Join to get user details
    # We want valid friends for current_user
    query = select(auth_models.User).join(
        models.Friendship, 
        models.Friendship.friend_id == auth_models.User.id
    ).where(models.Friendship.user_id == current_user.id)
    
    result = await session.execute(query)
    friends = result.scalars().all()
    return friends
