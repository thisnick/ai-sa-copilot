from typing import Any, List, Optional, cast

from swarm import AsyncAgent, AsyncResponse, AsyncSwarm
from swarm.types import AsyncStreamingResponse, AsyncResponse, AsyncMessageStreamingChunk, AsyncDelimStreamingChunk, AsyncResponseStreamingChunk
from swarm.repl.repl import pretty_print_messages
import litellm

from api.config import Settings
from api.db.types import ClusterSummary, TopLevelCluster

from .runbook_planning_agent import create_runbook_planning_agent
from .runbook_section_writing_agent import create_runbook_section_writing_agent
from .types import ContextVariables, KnowledgeTopic


from .research_coordinator_agent import create_research_coordinator_agent
from .topic_research_agent import create_topic_research_agent
from .intermediate_context_variables import AFTER_PLANNING, AFTER_REQUIREMENTS_GATHERING, AFTER_TOPIC_RESEARCH_COMPLETE
from .llm import AsyncLiteLLM

from api.lib.supabase import create_async_supabase_client

# Apply the patch
settings = Settings()

# litellm.set_verbose = True # type: ignore

USER_INPUT = "Give me a runbook for deploying Databricks on AWS. No other requirements."

DOMAIN_ID = "b54feb10-5011-429e-8585-35913d797d8e"


async def async_get_knowledge_topics(domain_id: str) -> List[KnowledgeTopic]:
  supabase = await create_async_supabase_client()
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


async def get_initial_context() -> ContextVariables:
  return ContextVariables(
    root_topics=await async_get_knowledge_topics(DOMAIN_ID)
  )



async def process_and_print_streaming_response(response : AsyncStreamingResponse) -> Optional[AsyncResponse]:
    content = ""
    last_sender = ""

    async for chunk in response:
        if "sender" in chunk:
            chunk = cast(AsyncMessageStreamingChunk, chunk)
            last_sender = chunk["sender"]

        if "content" in chunk and cast(AsyncMessageStreamingChunk, chunk)["content"] is not None:
            chunk = cast(AsyncMessageStreamingChunk, chunk)
            if not content and last_sender:
                print(f"\033[94m{last_sender}:\033[0m", end=" ", flush=True)
                last_sender = ""
            print(chunk["content"], end="", flush=True)
            content += chunk["content"]

        if "tool_calls" in chunk and cast(AsyncMessageStreamingChunk, chunk)["tool_calls"] is not None:
            for tool_call in cast(AsyncMessageStreamingChunk, chunk)["tool_calls"]:
                f = tool_call["function"]
                name = f["name"]
                if not name:
                    continue
                print(f"\033[94m{last_sender}: \033[95m{name}\033[0m()")

        if "delim" in chunk and cast(AsyncDelimStreamingChunk, chunk)["delim"] == "end" and content:
            print()  # End of response message
            content = ""

        if "response" in chunk:
            return cast(AsyncResponseStreamingChunk, chunk)["response"]


async def run_demo_loop_with_user_input(
    starting_agent: AsyncAgent, context_variables: ContextVariables | None = None, stream: bool = False, debug: bool = False, user_input: str | None = None
) -> None:
  def retry_logging(retry_state):
    print(f"Retrying {retry_state}")

  llm_client = AsyncLiteLLM()
  # llm_client = AsyncOpenAI()
  client = AsyncSwarm(client=llm_client, exponential_backoff=False, retry_callback=retry_logging)
  print("Starting Swarm CLI 🐝")

  messages = []
  agent : AsyncAgent = starting_agent

  if user_input:
    print(f"\033[90mUser\033[0m: {user_input}")

  while True:
    if not user_input:
      user_input = input("\033[90mUser\033[0m: ")

    messages.append({"role": "user", "content": user_input})

    response = await client.run(
        agent=agent,
        messages=messages,
        context_variables=cast(dict, context_variables or {}),
        stream=stream,
        debug=debug,
    )

    if stream:
        response = cast(AsyncStreamingResponse, response)
        response = await process_and_print_streaming_response(response)
    else:
        response = cast(AsyncResponse, response)
        pretty_print_messages(response.messages)

    messages.extend(response.messages) # type: ignore
    agent = response.agent # type: ignore
    user_input = None

async def run_initial_loop() -> None:
  researcher = create_research_coordinator_agent(settings)
  initial_context = await get_initial_context()
  await run_demo_loop_with_user_input(researcher, initial_context, stream=True)

async def run_loop_after_requirements_gathering() -> None:
  researcher = create_topic_research_agent(settings)
  initial_context = await get_initial_context()
  variables : ContextVariables = {
    **initial_context,
    **AFTER_REQUIREMENTS_GATHERING,
    "debug": True
  }
  await run_demo_loop_with_user_input(
    researcher,
    variables,
    stream=True,
    user_input=USER_INPUT
  )

async def run_loop_after_research_complete() -> None:
  agent = create_runbook_planning_agent(settings)
  initial_context = await get_initial_context()
  variables : ContextVariables = {
    **initial_context,
    **AFTER_TOPIC_RESEARCH_COMPLETE,
    "debug": True
  }
  await run_demo_loop_with_user_input(
    agent,
    variables,
    stream=True,
    user_input=USER_INPUT
  )


async def run_loop_after_planning() -> None:
  agent = create_runbook_section_writing_agent(settings)
  initial_context = await get_initial_context()
  variables : ContextVariables = {
    **initial_context,
    **AFTER_PLANNING,
    "debug": True
  }
  await run_demo_loop_with_user_input(
    agent,
    variables,
    stream=True,
    user_input=USER_INPUT
  )
