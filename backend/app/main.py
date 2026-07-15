from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .database import engine, Base, get_db
from . import models  # noqa: F401 - needed so Base knows about the tables

from .routes import chat, interactions, hcps  # needed to register the routes with FastAPI

app = FastAPI(title="CRM Logger API")

app.include_router(chat.router, prefix="/api", tags=["chat"]) # wraps the chat routes in /api/chat
app.include_router(interactions.router, prefix="/api", tags=["interactions"]) # wraps the interactions routes in /api/interactions
app.include_router(hcps.router, prefix="/api", tags=["hcps"]) # wraps the HCP routes in /api/hcps

# Allow the React frontend (Vite default port) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # Creates tables in Neon if they don't exist yet
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"status": "CRM Logger API is running"}


@app.get("/health/db")
def db_health_check():
    """Quick check that we can actually talk to Neon."""
    from .database import SessionLocal
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {"database": "connected"}
    except Exception as e:
        return {"database": "error", "detail": str(e)}
    finally:
        db.close()