from contextlib import contextmanager
import os
import asyncio

from nest_asyncio import apply
from supabase import AsyncClient
from .intermediate_states import (
  run_initial_loop,
  run_loop_after_planning,
  run_loop_after_requirements_gathering,
  run_loop_after_research_complete
)
from dotenv import load_dotenv

from api.lib.supabase import create_async_supabase_admin_client
from api.agents.contexts import with_supabase_client
load_dotenv()

apply()

async def async_main():
    with with_supabase_client(await create_async_supabase_admin_client()):
        return await run_initial_loop();

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
