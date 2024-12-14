

from typing import List, Optional, cast
from swarm.types import StreamingResponse, AsyncStreamingResponse

from swarm import AsyncSwarm
from swarm.types import Message

from api.agents.agent_map import INITIAL_AGENT
from api.config import Settings
from .types import ContextVariables
from .agent_factory import create_agent
from .llm import AsyncLiteLLM

async def stream_response(
  messages: List[Message],
  agent_name: Optional[str],
  context_variables: ContextVariables = {},
  settings: Settings = Settings(),
) -> AsyncStreamingResponse:
  agent_name = agent_name or INITIAL_AGENT
  agent = create_agent(settings, agent_name)
  llm_client = AsyncLiteLLM()

  def retry_logging(retry_state):
    print(f"Retrying {retry_state}")

  swarm = AsyncSwarm(client=llm_client, exponential_backoff=True, retry_callback=retry_logging)

  response = await swarm.run(
    agent=agent,
    messages=messages,
    context_variables=cast(dict, context_variables),
    stream=True,
  )
  return cast(AsyncStreamingResponse, response)
