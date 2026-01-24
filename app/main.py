from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.database import init_db
from app.auth import router as auth_router
from app.friends import router as friends_router
from app.reminders import router as reminders_router


# Ensure models are imported for SQLModel metadata
from app.auth import models as auth_models
from app.friends import models as friends_models
from app.reminders import models as reminders_models

app = FastAPI(title=settings.PROJECT_NAME)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
async def on_startup():
    await init_db()

app.include_router(auth_router.router)
app.include_router(friends_router.router)
app.include_router(reminders_router.router)

origins = [
    "http://localhost:8081",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to Remind Anyone API"}
