from fastapi import APIRouter
from app.api.routes import auth, messages, friends

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])
api_router.include_router(friends.router, prefix="/friends", tags=["friends"])
