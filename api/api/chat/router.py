from fastapi import APIRouter
from .chat.router import router as chat_router

router = APIRouter()

router.include_router(chat_router, prefix="/chat")
