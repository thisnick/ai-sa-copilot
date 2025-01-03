from typing import Annotated
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp

from lib.supabase import set_supabase_client_context, get_server_supabase_client

class SupabaseContextMiddleware(BaseHTTPMiddleware):
  def __init__(self, app: ASGIApp):
    super().__init__(app)
    self.security = HTTPBearer(auto_error=False)

  async def dispatch(self, request: Request, call_next):
    try:
      # Try to get credentials using HTTPBearer
      credentials = await self.security(request)
      # Get the Supabase client with proper credentials
      supabase = await get_server_supabase_client(credentials)
    except HTTPException:
      # If credentials are not found, use a anonymous client
      credentials = None
      supabase = await get_server_supabase_client(None)

    # Set the context
    set_supabase_client_context(supabase)
    try:
      response = await call_next(request)
      return response
    finally:
      # Reset context and close client after request is done
      set_supabase_client_context(None)
