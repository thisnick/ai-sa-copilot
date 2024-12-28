from fastapi import FastAPI
from api.chat.chat.stream_messages import router as chat_router
from api.inngest.serve import serve_inngest
from lib.middleware import SupabaseContextMiddleware

app = FastAPI()
app.add_middleware(SupabaseContextMiddleware)

app.include_router(chat_router, prefix="/api/chat")
serve_inngest(app)

