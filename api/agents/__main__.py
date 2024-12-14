import os
import asyncio

from nest_asyncio import apply
from .intermediate_states import (
  run_initial_loop,
  run_loop_after_planning,
  run_loop_after_requirements_gathering,
  run_loop_after_research_complete
)
from dotenv import load_dotenv

load_dotenv()

apply()


async def async_main():
    return await run_initial_loop();

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
