from fastapi import FastAPI
from .config import Settings
from .routes.inngest import serve_inngest
from .routes.chat.stream_messages import router as chat_router
from .lib.middleware import SupabaseContextMiddleware

app = FastAPI()
app.add_middleware(SupabaseContextMiddleware)

app.include_router(chat_router, prefix="/chat")
serve_inngest(app)


