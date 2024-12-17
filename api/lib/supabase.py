from typing import Annotated, Optional
from abc import ABC
from supabase import AsyncClient, create_async_client, AsyncClientOptions
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..config import Settings

settings = Settings()
security = HTTPBearer()

async def create_async_supabase_admin_client() -> AsyncClient:
  return await create_async_client(settings.next_public_supabase_url, settings.supabase_service_role_key)

async def get_server_supabase_client(
  credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)] = None
) -> AsyncClient:

  supabase = await create_async_client(
    settings.next_public_supabase_url,
    settings.next_public_supabase_anon_key,
    options=AsyncClientOptions(
      auto_refresh_token=False,  # No need for refresh since we're using direct token
      persist_session=False  # No session persistence needed
    )
  )

  if credentials:
    await supabase.auth.set_session(credentials.credentials, "")

  return supabase

__all__ = [
  "get_server_supabase_client",
  "create_async_supabase_admin_client",
]
