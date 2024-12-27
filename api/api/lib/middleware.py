from typing import Annotated
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp

from api.agents.contexts import set_supabase_client
from api.lib.supabase import get_server_supabase_client

class SupabaseContextMiddleware(BaseHTTPMiddleware):
  def __init__(self, app: ASGIApp):
    super().__init__(app)
    self.security = HTTPBearer(auto_error=False)

  async def dispatch(self, request: Request, call_next):
    try:
      # Try to get credentials using HTTPBearer
      credentials = await self.security(request)
    except HTTPException:
      credentials = None

    # Get the Supabase client with proper credentials
    supabase = await get_server_supabase_client(credentials)

    # Set the context
    set_supabase_client(supabase)
    try:
      response = await call_next(request)
      return response
    finally:
      # Reset context and close client after request is done
      set_supabase_client(None)
