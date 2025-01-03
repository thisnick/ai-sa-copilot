from fastapi import FastAPI
from .router import router as chat_router
from lib.middleware import SupabaseContextMiddleware

app = FastAPI()
app.add_middleware(SupabaseContextMiddleware)

app.include_router(chat_router, prefix="/api/chat/chat")
