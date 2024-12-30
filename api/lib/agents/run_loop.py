

from typing import List, Optional, cast
from swarm.types import StreamingResponse, AsyncStreamingResponse

from swarm import AsyncSwarm
from swarm.types import Message

from lib.agents.agent_map import INITIAL_AGENT
from lib.agents.contexts import get_supabase_client_from_context
from lib.config import Settings
from lib.db.types import TopLevelCluster
from .types import ContextVariables, KnowledgeTopic
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
  print("created agent", agent)
  llm_client = AsyncLiteLLM()

  def retry_logging(retry_state):
    print(f"Retrying {retry_state}")

  swarm = AsyncSwarm(
    client=llm_client,
    exponential_backoff=True,
    retry_callback=retry_logging
  )

  response = await swarm.run(
    agent=agent,
    messages=messages,
    context_variables=cast(dict, context_variables),
    stream=True,
  )
  return cast(AsyncStreamingResponse, response)


async def async_get_knowledge_topics(domain_id: str) -> List[KnowledgeTopic]:
  supabase = get_supabase_client_from_context()
  top_level_clusters_response = await supabase.rpc("get_top_level_clusters", {"target_domain_id": domain_id}).execute()
  top_level_clusters = cast(List[TopLevelCluster], top_level_clusters_response.data)

  results = [
    KnowledgeTopic(
      topic=cluster["summary"]["main_theme"],
      key_concepts=list(cluster["summary"]["key_concepts"])
    )
    for cluster in top_level_clusters
    if cluster["summary"] is not None
  ]
  return results
