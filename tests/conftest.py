import pytest
from httpx import AsyncClient, ASGITransport
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import get_session
from app.auth import models as auth_models
from app.core import security

from sqlalchemy.pool import StaticPool

# Use SQLite for testing
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(name="engine")
async def engine_fixture():
    engine = create_async_engine(
        DATABASE_URL, 
        echo=False, 
        future=True, 
        poolclass=StaticPool, 
        connect_args={"check_same_thread": False}
    )
    yield engine
    await engine.dispose()

@pytest.fixture(name="session")
async def session_fixture(engine):
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

@pytest.fixture(name="client")
async def client_fixture(session: AsyncSession):
    def get_session_override():
        return session
    
    app.dependency_overrides[get_session] = get_session_override
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()

@pytest.fixture(name="test_user")
async def test_user_fixture(session: AsyncSession):
    user = auth_models.User(
        email="test@example.com",
        username="testuser",
        full_name="Test User"
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

@pytest.fixture(name="auth_headers")
def auth_headers_fixture(test_user: auth_models.User):
    access_token = security.create_access_token(subject=test_user.id)
    return {"Authorization": f"Bearer {access_token}"}
