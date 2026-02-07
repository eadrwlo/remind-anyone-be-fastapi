import logging
from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from app.core.database import get_session
from app.core.config import settings
from app.core import security
from app.auth import models, schemas, dependencies as auth_deps

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    OAuth2 compatible token login, used for Swagger UI.
    For development, simply accepts any username/password and creates a test user.
    """
    email = f"{form_data.username}@example.com"
    username = form_data.username
    
    # Check if user exists
    result = await session.execute(select(models.User).where(models.User.username == username))
    user = result.scalars().first()
    logging.info(f"User found: {user}")

    if not user:
        # Auto-provision user for dev convenience
        user = models.User(
            email=email,
            username=username,
            full_name=f"Dev User {username}"
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=schemas.Token)
async def login_google(
    login_data: schemas.GoogleLogin,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    # Verify Google Token
    # In dev/test without real credentials, we might want a bypass or mock.
    # For now, implementing the real logic but wrapped in try/except or handling "test" token.
    
    email = ""
    username = ""
    full_name = ""
    
    if login_data.id_token == "test-token":
         # Mock for testing/development if needed
         email = "test@example.com"
         username = "testuser"
         full_name = "Test User"
    else:
        try:
             id_info = id_token.verify_oauth2_token(
                 login_data.id_token, 
                 google_requests.Request(), 
                 settings.GOOGLE_CLIENT_ID or None, # Allow None if not set, though verify might fail if mismatch
                 clock_skew_in_seconds=10
             )
             email = id_info['email']
             full_name = id_info.get('name')
             # Username strategy: use email prefix or prompt user?
             # Requirement says: "User Provisioning: If a user logs in for the first time... account created"
             # We'll default username to email or part of it for now.
             username = email.split('@')[0] 
        except ValueError as e:
             raise HTTPException(status_code=400, detail=f"Invalid Google Token: {str(e)}")

    # Check if user exists
    result = await session.execute(select(models.User).where(models.User.email == email))
    user = result.scalars().first()

    if not user:
        # Create new user
        user = models.User(
            email=email,
            username=username,
            full_name=full_name
        )
        session.add(user)
        # Handle unique constraint violation for username if needed (e.g. if email prefix taken)
        # minimal implementation for now
        await session.commit()
        await session.refresh(user)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer"
    }

@router.get("/me", response_model=models.UserRead)
async def read_users_me(
    current_user: Annotated[models.User, Depends(auth_deps.get_current_user)]
):
    """
    Get current user details.
    """
    return current_user

@router.put("/me/device-token", response_model=models.UserRead)
async def update_device_token(
    token_request: schemas.DeviceTokenRequest,
    current_user: Annotated[models.User, Depends(auth_deps.get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Update the current user's Expo Push Token.
    """
    current_user.expo_push_token = token_request.token
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    return current_user
