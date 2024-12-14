from fastapi import FastAPI
from .config import Settings
from .routes.inngest import serve_inngest
from .routes.chat.stream_messages import router as chat_router
import inngest.fast_api

settings = Settings()
app = FastAPI()

app.include_router(chat_router, prefix="/chat")
serve_inngest(app)
