from contextlib import asynccontextmanager, contextmanager
from supabase import AsyncClient

from contextvars import ContextVar

supabase_client_context = ContextVar[AsyncClient | None]('supabase', default=None)

def get_supabase_client_from_context() -> AsyncClient:
  supabase_client = supabase_client_context.get()
  if supabase_client is None:
    raise ValueError("Supabase client not found in context")
  return supabase_client

def set_supabase_client_context(client: AsyncClient | None) -> None:
  supabase_client_context.set(client)

@contextmanager
def with_supabase_client(client: AsyncClient):
  set_supabase_client_context(client)
  yield
  set_supabase_client_context(None)
