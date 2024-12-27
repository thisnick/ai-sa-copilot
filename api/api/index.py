from fastapi import FastAPI
from api.routes.inngest import serve_inngest
from api.routes.chat.stream_messages import router as chat_router
from api.lib.middleware import SupabaseContextMiddleware

app = FastAPI()
app.add_middleware(SupabaseContextMiddleware)

app.include_router(chat_router, prefix="/chat")
serve_inngest(app)


